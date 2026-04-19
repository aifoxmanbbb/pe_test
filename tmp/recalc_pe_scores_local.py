import json
from datetime import datetime

import pymysql

from application.config.production import MYSQL_DB, MYSQL_HOST, MYSQL_PASSWORD, MYSQL_PORT, MYSQL_USER
from apps.vadmin.sport.service.rule_engine import RuleEngine


def normalize_gender(gender: str | None) -> str:
    text = str(gender or '').strip().lower()
    if ('男' in text) or ('male' in text) or text in {'m', '1'}:
        return 'male'
    if ('女' in text) or ('female' in text) or text in {'f', '0', '2'}:
        return 'female'
    return 'all'


def select_rule(item_rules: list[dict], gender: str | None) -> dict | None:
    if not item_rules:
        return None
    target = normalize_gender(gender)
    for rule in item_rules:
        if normalize_gender(rule.get('gender')) == target:
            return rule
    for rule in item_rules:
        if normalize_gender(rule.get('gender')) == 'all':
            return rule
    return None


def to_float(value, default: float = 0.0) -> float:
    try:
        if value is None or value == '':
            return default
        return float(value)
    except Exception:
        return default


def parse_raw_score(raw, item_code: str | None = None):
    parsed = RuleEngine.parse_time_to_seconds(raw)
    if parsed is None:
        return None
    code = str(item_code or '').lower()
    if code in {'jump', 'ball'} and parsed > 30:
        return round(parsed / 100.0, 2)
    return parsed


def calc_by_rule(raw_score, rule: dict | None, conflict_policy: str) -> dict:
    if raw_score is None or not rule:
        return {}

    mode = str(rule.get('calc_mode') or 'segment').strip().lower()
    if mode == 'segment':
        segments = rule.get('segment_json')
        if isinstance(segments, str):
            try:
                segments = json.loads(segments)
            except Exception:
                segments = None
        if isinstance(segments, list) and segments:
            result = RuleEngine.eval_by_segment(raw_score, segments, conflict_policy=conflict_policy)
            max_score = to_float(rule.get('max_score'), 0.0)
            score_value = to_float(result.get('score_value'), 0.0)
            if max_score > 0 and max_score < score_value <= 100:
                result['score_value'] = round((score_value / 100.0) * max_score, 2)
            return result
        return {}

    result = RuleEngine.eval_by_threshold(raw_score, {
        'pass': to_float(rule.get('pass_threshold'), 0.0),
        'excellent': to_float(rule.get('excellent_threshold'), 0.0),
        'full': to_float(rule.get('full_threshold'), 0.0)
    })
    if to_float(rule.get('max_score'), 0.0) <= 0:
        result['score_value'] = 0.0
    return result


def main():
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=int(MYSQL_PORT),
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        charset='utf8mb4',
        autocommit=False
    )
    cur = conn.cursor(pymysql.cursors.DictCursor)

    cur.execute(
        """
        select
            s.id,
            s.gender,
            s.item_code,
            s.raw_score,
            s.item_name,
            b.standard_id,
            st.conflict_policy
        from vadmin_pef_score s
        join vadmin_pef_batch b on b.id = s.batch_id
        left join vadmin_pef_standard st on st.id = b.standard_id
        where s.is_delete = 0 and s.biz_type = 'pe'
        order by s.id asc
        """
    )
    score_rows = cur.fetchall()

    cur.execute(
        """
        select
            standard_id,
            item_code,
            item_name,
            gender,
            calc_mode,
            pass_threshold,
            excellent_threshold,
            full_threshold,
            segment_json,
            max_score
        from vadmin_pef_standard_item
        where is_delete = 0
        order by standard_id asc, sort asc, id asc
        """
    )
    rule_rows = cur.fetchall()

    rule_map: dict[tuple[int, str], list[dict]] = {}
    for row in rule_rows:
        rule_map.setdefault((int(row['standard_id']), row['item_code']), []).append(row)

    updated = 0
    deleted = 0

    for row in score_rows:
        rules = rule_map.get((int(row['standard_id']), row['item_code']), [])
        selected_rule = select_rule(rules, row['gender'])
        if not selected_rule:
            cur.execute(
                """
                update vadmin_pef_score
                set is_delete = 1, delete_datetime = %s
                where id = %s
                """,
                (datetime.now(), row['id'])
            )
            deleted += 1
            continue

        raw_score = parse_raw_score(row['raw_score'], row['item_code'])
        calc_result = calc_by_rule(raw_score, selected_rule, row.get('conflict_policy') or 'lower_priority')
        cur.execute(
            """
            update vadmin_pef_score
            set item_name = %s,
                raw_score = %s,
                score_value = %s,
                is_pass = %s,
                is_excellent = %s,
                is_full = %s
            where id = %s
            """,
            (
                selected_rule.get('item_name') or row['item_name'],
                raw_score,
                calc_result.get('score_value'),
                calc_result.get('is_pass'),
                calc_result.get('is_excellent'),
                calc_result.get('is_full'),
                row['id']
            )
        )
        updated += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f'recalc complete: updated={updated}, soft_deleted={deleted}')


if __name__ == '__main__':
    main()
