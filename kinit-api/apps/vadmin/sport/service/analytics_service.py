#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any, Iterable

from sqlalchemy import false, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.vadmin.auth.models.dept import VadminDept
from apps.vadmin.sport.models import VadminSportBatch, VadminSportScore, VadminSportStandardItem


from utils.excel.write_xlsx import WriteXlsx


def to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def round2(value: float) -> float:
    return round(float(value), 2)


def avg(values: Iterable[float]) -> float:
    nums = [float(v) for v in values if v is not None]
    if not nums:
        return 0.0
    return round2(sum(nums) / len(nums))


def pct(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round2((numerator * 100.0) / denominator)


async def resolve_dept_filter_names(
        db: AsyncSession,
        school_id: int | None = None,
        grade_id: int | None = None,
        class_id: int | None = None,
        school_name: str | None = None,
        grade_name: str | None = None,
        class_name: str | None = None
) -> tuple[str | None, str | None, str | None]:
    async def _name_by_id(dept_id: int | None) -> str | None:
        if not dept_id:
            return None
        row = await db.get(VadminDept, int(dept_id))
        if not row or bool(row.is_delete):
            return None
        return row.name

    if not school_name:
        school_name = await _name_by_id(school_id)
    if not grade_name:
        grade_name = await _name_by_id(grade_id)
    if not class_name:
        class_name = await _name_by_id(class_id)
    return school_name, grade_name, class_name


async def list_batches(
        db: AsyncSession,
        biz_type: str,
        stage_type: str | None = None,
        batch_id: int | None = None,
        school_name: str | None = None,
        grade_name: str | None = None,
        class_name: str | None = None,
        limit: int | None = None
) -> list[VadminSportBatch]:
    sql = select(VadminSportBatch).where(
        VadminSportBatch.is_delete == false(),
        VadminSportBatch.biz_type == biz_type
    )
    if batch_id:
        sql = sql.where(VadminSportBatch.id == batch_id)
    if stage_type:
        sql = sql.where(VadminSportBatch.stage_type == stage_type)
    if school_name:
        sql = sql.where(VadminSportBatch.school_name == school_name)
    if grade_name:
        sql = sql.where(VadminSportBatch.grade_name == grade_name)
    if class_name:
        sql = sql.where(VadminSportBatch.class_name == class_name)

    sql = sql.order_by(VadminSportBatch.id.desc())
    if limit and limit > 0:
        sql = sql.limit(limit)
    return (await db.scalars(sql)).all()


async def list_scores(
        db: AsyncSession,
        biz_type: str,
        batch_ids: list[int],
        school_name: str | None = None,
        grade_name: str | None = None,
        class_name: str | None = None,
        student_no: str | None = None,
        student_keyword: str | None = None
) -> list[VadminSportScore]:
    if not batch_ids:
        return []

    sql = select(VadminSportScore).where(
        VadminSportScore.is_delete == false(),
        VadminSportScore.biz_type == biz_type,
        VadminSportScore.batch_id.in_(batch_ids)
    )
    if biz_type == 'fitness':
        sql = sql.where(VadminSportScore.item_code != 'run_50x8')
    if school_name:
        sql = sql.where(VadminSportScore.school_name == school_name)
    if grade_name:
        sql = sql.where(VadminSportScore.grade_name == grade_name)
    if class_name:
        sql = sql.where(VadminSportScore.class_name == class_name)
    if student_no:
        sql = sql.where(VadminSportScore.student_no == student_no)

    rows = (await db.scalars(sql.order_by(VadminSportScore.batch_id.asc(), VadminSportScore.id.asc()))).all()
    if student_keyword:
        kw = str(student_keyword).strip()
        if kw:
            rows = [
                r for r in rows
                if kw in (r.student_no or '')
                or kw in (r.student_name or '')
                or kw in (r.mobile or '')
            ]
    return rows


async def get_standard_item_thresholds(db: AsyncSession, standard_id: int | None) -> dict[str, dict[str, float]]:
    if not standard_id:
        return {}
    sql = select(VadminSportStandardItem).where(
        VadminSportStandardItem.is_delete == false(),
        VadminSportStandardItem.standard_id == standard_id
    ).order_by(VadminSportStandardItem.sort.asc(), VadminSportStandardItem.id.asc())
    rows = (await db.scalars(sql)).all()
    result: dict[str, dict[str, float]] = {}
    for row in rows:
        result[row.item_code] = {
            'pass': to_float(row.pass_threshold),
            'excellent': to_float(row.excellent_threshold),
            'full': to_float(row.full_threshold),
            'max': to_float(row.max_score)
        }
    return result


def group_scores_by_student(rows: list[VadminSportScore]) -> dict[str, list[VadminSportScore]]:
    result: dict[str, list[VadminSportScore]] = defaultdict(list)
    for row in rows:
        result[row.student_no].append(row)
    return result


def group_scores_by_batch(rows: list[VadminSportScore]) -> dict[int, list[VadminSportScore]]:
    result: dict[int, list[VadminSportScore]] = defaultdict(list)
    for row in rows:
        result[row.batch_id].append(row)
    return result


def group_scores_by_batch_student(rows: list[VadminSportScore]) -> dict[tuple[int, str], list[VadminSportScore]]:
    result: dict[tuple[int, str], list[VadminSportScore]] = defaultdict(list)
    for row in rows:
        result[(row.batch_id, row.student_no)].append(row)
    return result


def group_scores_by_class(rows: list[VadminSportScore]) -> dict[tuple[str, str], list[VadminSportScore]]:
    result: dict[tuple[str, str], list[VadminSportScore]] = defaultdict(list)
    for row in rows:
        result[(row.school_name, row.class_name)].append(row)
    return result


def group_scores_by_grade_class(rows: list[VadminSportScore]) -> dict[str, list[VadminSportScore]]:
    result: dict[str, list[VadminSportScore]] = defaultdict(list)
    for row in rows:
        result[row.class_name].append(row)
    return result


def student_total_score(rows: list[VadminSportScore]) -> float:
    return round2(sum(to_float(r.score_value) for r in rows))


def classify_total(total_score: float, pass_line: float, excellent_line: float, full_line: float) -> dict[str, bool]:
    return {
        'is_pass': total_score >= pass_line,
        'is_excellent': total_score >= excellent_line,
        'is_full': total_score >= full_line
    }


def build_fail_risk(rows: list[VadminSportScore], exclude_item_codes: set[str] | None = None) -> dict[str, Any]:
    exclude_item_codes = exclude_item_codes or set()
    latest: dict[tuple[int, str, str], VadminSportScore] = {}
    for row in rows:
        item_code = str(row.item_code or '')
        if item_code in exclude_item_codes:
            continue
        key = (int(row.batch_id or 0), str(row.student_no or ''), item_code)
        old = latest.get(key)
        if not old or int(row.id or 0) >= int(old.id or 0):
            latest[key] = row

    scoped_rows = list(latest.values())
    fail_rows = [row for row in scoped_rows if not bool(row.is_pass)]
    by_student = group_scores_by_student(scoped_rows)
    fail_students = {str(row.student_no or '') for row in fail_rows if row.student_no}

    def _bucket(label_getter, key_name: str) -> list[dict[str, Any]]:
        buckets: dict[str, list[VadminSportScore]] = defaultdict(list)
        for row in scoped_rows:
            buckets[str(label_getter(row) or '-')].append(row)
        result = []
        for label, b_rows in buckets.items():
            b_fail = [row for row in b_rows if not bool(row.is_pass)]
            fail_student_set = {str(row.student_no or '') for row in b_fail if row.student_no}
            item_counter: dict[str, int] = defaultdict(int)
            for row in b_fail:
                item_counter[row.item_name or row.item_code or '-'] += 1
            top_item = sorted(item_counter.items(), key=lambda item: (-item[1], item[0]))[0][0] if item_counter else '-'
            result.append({
                key_name: label,
                'student_count': len(group_scores_by_student(b_rows)),
                'fail_student_count': len(fail_student_set),
                'fail_record_count': len(b_fail),
                'avg_score': avg([to_float(row.score_value) for row in b_rows]),
                'top_fail_item': top_item
            })
        return sorted(result, key=lambda item: (-item['fail_student_count'], -item['fail_record_count'], item['avg_score'], item[key_name]))

    item_buckets: dict[str, list[VadminSportScore]] = defaultdict(list)
    for row in scoped_rows:
        item_buckets[str(row.item_code or '')].append(row)
    item_risks = []
    for code, i_rows in item_buckets.items():
        i_fail = [row for row in i_rows if not bool(row.is_pass)]
        fail_student_set = {str(row.student_no or '') for row in i_fail if row.student_no}
        class_set = {str(row.class_name or '') for row in i_fail if row.class_name}
        scores = [to_float(row.score_value) for row in i_rows]
        item_risks.append({
            'item_code': code,
            'item_name': i_rows[0].item_name if i_rows else code,
            'student_count': len(group_scores_by_student(i_rows)),
            'fail_student_count': len(fail_student_set),
            'fail_record_count': len(i_fail),
            'class_count': len(class_set),
            'avg_score': avg(scores),
            'min_score': round2(min(scores)) if scores else 0.0
        })
    item_risks = sorted(item_risks, key=lambda item: (-item['fail_student_count'], -item['fail_record_count'], item['avg_score'], item['item_name']))

    student_risks = []
    for student_no, s_rows in by_student.items():
        s_fail = [row for row in s_rows if not bool(row.is_pass)]
        if not s_fail:
            continue
        first = s_rows[0]
        lowest = sorted(s_fail, key=lambda row: to_float(row.score_value))[0]
        student_risks.append({
            'school_name': first.school_name,
            'grade_name': first.grade_name,
            'class_name': first.class_name,
            'student_no': student_no,
            'student_name': first.student_name,
            'fail_item_count': len(s_fail),
            'lowest_item': lowest.item_name or lowest.item_code,
            'lowest_score': round2(to_float(lowest.score_value)),
            'fail_items_text': '、'.join([row.item_name or row.item_code or '-' for row in s_fail])
        })
    student_risks = sorted(student_risks, key=lambda item: (-item['fail_item_count'], item['lowest_score'], item['class_name'], item['student_name']))

    fail_records = [{
        'school_name': row.school_name,
        'grade_name': row.grade_name,
        'class_name': row.class_name,
        'student_no': row.student_no,
        'student_name': row.student_name,
        'item_code': row.item_code,
        'item_name': row.item_name,
        'raw_score': format_score(to_float(row.raw_score)),
        'score_value': round2(to_float(row.score_value))
    } for row in sorted(fail_rows, key=lambda r: (r.grade_name or '', r.class_name or '', r.student_name or '', r.item_name or ''))]

    top_class = _bucket(lambda row: row.class_name, 'class_name')[:1]
    top_grade = _bucket(lambda row: row.grade_name, 'grade_name')[:1]
    top_item = item_risks[:1]
    return {
        'risk_kpi': {
            'student_count': len(by_student),
            'fail_student_count': len(fail_students),
            'fail_record_count': len(fail_rows),
            'fail_rate': pct(len(fail_students), len(by_student)),
            'top_grade': top_grade[0]['grade_name'] if top_grade else '-',
            'top_class': top_class[0]['class_name'] if top_class else '-',
            'top_item': top_item[0]['item_name'] if top_item else '-'
        },
        'grade_risks': _bucket(lambda row: row.grade_name, 'grade_name'),
        'class_risks': _bucket(lambda row: row.class_name, 'class_name'),
        'item_risks': item_risks,
        'student_risks': student_risks,
        'fail_records': fail_records
    }


def first_or_none(rows: list[Any]) -> Any | None:
    return rows[0] if rows else None


def pick_items_by_keywords(
        rows: list[VadminSportScore],
        slot_keywords: dict[str, list[str]],
        fallback_size: int
) -> dict[str, str]:
    item_order: list[str] = []
    item_name_map: dict[str, str] = {}
    count_map: dict[str, int] = defaultdict(int)

    for row in rows:
        if row.item_code not in item_name_map:
            item_name_map[row.item_code] = row.item_name
            item_order.append(row.item_code)
        count_map[row.item_code] += 1

    sorted_codes = sorted(item_name_map.keys(), key=lambda c: (-count_map[c], item_order.index(c)))

    result: dict[str, str] = {}
    used: set[str] = set()

    for slot, keywords in slot_keywords.items():
        target = None
        for code in sorted_codes:
            if code in used:
                continue
            name = item_name_map.get(code, '')
            text = f"{code} {name}".lower()
            if any(k.lower() in text for k in keywords):
                target = code
                break
        if target:
            result[slot] = target
            used.add(target)

    for code in sorted_codes:
        if len(result) >= fallback_size:
            break
        if code in used:
            continue
        slot = f'item_{len(result) + 1}'
        result[slot] = code
        used.add(code)

    return result


def format_score(value: float | int | str | None, suffix: str = '') -> str:
    if value is None or value == '':
        return '-'
    if isinstance(value, str):
        return value
    num = to_float(value)
    if abs(num - int(num)) < 1e-6:
        return f"{int(num)}{suffix}"
    return f"{round2(num)}{suffix}"


def build_rate_text(pass_rate: float, excellent_rate: float, full_rate: float) -> str:
    return f"及格{round2(pass_rate)}% / 优秀{round2(excellent_rate)}% / 满分{round2(full_rate)}%"


def display_gender(value: str | int | None) -> str:
    text = str(value or '').strip().lower()
    if text in {'male', '1', '男'}:
        return '男'
    if text in {'female', '0', '女'}:
        return '女'
    return str(value or '')


def export_scores_to_excel(rows: list[VadminSportScore], filename: str) -> str:
    if not rows:
        return ""

    # 获取所有项目
    item_map: dict[str, str] = {}
    for r in rows:
        item_map.setdefault(r.item_code, r.item_name)
    
    item_codes = sorted(item_map.keys())
    
    headers = ["学生姓名", "学号", "性别", "学校", "年级", "班级"]
    for code in item_codes:
        name = item_map[code]
        headers.append(f"{name}(成绩)")
        headers.append(f"{name}(分值)")
    headers.append("总分")

    # 按学生分组
    student_groups = group_scores_by_student(rows)
    
    excel_rows = []
    for student_no, s_rows in student_groups.items():
        first = s_rows[0]
        row_data = [
            first.student_name,
            first.student_no,
            display_gender(first.gender),
            first.school_name,
            first.grade_name,
            first.class_name
        ]
        
        s_item_map = {r.item_code: r for r in s_rows}
        total_score = 0.0
        for code in item_codes:
            ir = s_item_map.get(code)
            if ir:
                row_data.append(format_score(ir.raw_score))
                row_data.append(to_float(ir.score_value))
                total_score += to_float(ir.score_value)
            else:
                row_data.append("-")
                row_data.append(0.0)
        
        row_data.append(round2(total_score))
        excel_rows.append(row_data)

    writer = WriteXlsx()
    writer.create_excel(file_path=filename, save_static=True)
    
    # 转换为 dict 结构的 headers
    header_dicts = [{"label": h} for h in headers]
    writer.generate_template(header_dicts)
    writer.write_list(excel_rows)
    writer.close()
    
    return writer.get_file_url()
