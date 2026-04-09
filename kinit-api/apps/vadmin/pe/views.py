#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import re
from typing import Any
from fastapi import APIRouter, Depends, Body, Query, File, UploadFile
from sqlalchemy import select, false, true, func, or_
from apps.vadmin.auth.utils.current import AllUserAuth, FullAdminAuth
from apps.vadmin.auth.utils.validation.auth import Auth
from apps.vadmin.sport.models import (
    VadminSportStandard,
    VadminSportStandardItem,
    VadminSportBatch,
    VadminSportScore,
    VadminPefSchool,
    VadminPefGrade,
    VadminPefClass,
    VadminPefStudent
)
from apps.vadmin.sport import schemas
from apps.vadmin.sport.service.analytics_service import (
    avg,
    classify_total,
    format_score,
    get_standard_item_thresholds,
    group_scores_by_batch,
    group_scores_by_batch_student,
    group_scores_by_class,
    group_scores_by_grade_class,
    group_scores_by_student,
    list_batches,
    list_scores,
    pick_items_by_keywords,
    round2,
    resolve_dept_filter_names,
    student_total_score,
    to_float,
    pct,
    export_scores_to_excel
)
from apps.vadmin.sport.service.rule_engine import RuleEngine
from apps.vadmin.sport.service.batch_import_service import BatchImportService
from apps.vadmin.sport.service.standard_import_service import StandardImportService
from apps.vadmin.sport.service.standard_service import list_standard_with_items
from utils.response import SuccessResponse, ErrorResponse

app = APIRouter()

PE_PASS_LINE = 30.0
PE_EXCELLENT_LINE = 40.0
PE_FULL_LINE = 50.0

def _serialize(model_obj, schema_class):
    return json.loads(schema_class.model_validate(model_obj).model_dump_json())

def _scope_tokens(auth: Auth) -> list[str]:
    if not auth.user or not hasattr(auth.user, 'depts'):
        return []
    tokens = []
    for dept in auth.user.depts:
        name = getattr(dept, 'name', None)
        key = getattr(dept, 'dept_key', None)
        if name:
            tokens.append(str(name))
        if key:
            tokens.append(str(key))
    return list(set(tokens))


def _is_global_scope(auth: Auth) -> bool:
    return auth.data_range in (None, 4) or '*' in (auth.dept_ids or [])


def _filter_rows_by_scope(auth: Auth, rows: list[dict[str, Any]], keys: list[str]) -> list[dict[str, Any]]:
    if _is_global_scope(auth):
        return rows
    tokens = _scope_tokens(auth)
    if not tokens:
        return rows
    result = []
    for row in rows:
        values = [str(row.get(k, '')) for k in keys]
        if any((tk in val) or (val in tk) for tk in tokens for val in values if val):
            result.append(row)
    return result


def _can_access_row(auth: Auth, row: dict[str, Any], keys: list[str]) -> bool:
    return len(_filter_rows_by_scope(auth, [row], keys)) > 0


def _in_scope(auth: Auth, school_name: str | None, class_name: str | None) -> bool:
    if _is_global_scope(auth):
        return True
    tokens = _scope_tokens(auth)
    if not tokens:
        return True
    values = [str(school_name or ''), str(class_name or '')]
    return any((tk in val) or (val in tk) for tk in tokens for val in values if val)


async def _get_self_student_context(db, telephone: str | None) -> dict[str, Any] | None:
    if not telephone:
        return None
    sql = (
        select(VadminPefStudent, VadminPefSchool.school_name, VadminPefGrade.grade_name, VadminPefClass.class_name)
        .select_from(VadminPefStudent)
        .join(VadminPefSchool, VadminPefStudent.school_id == VadminPefSchool.id)
        .join(VadminPefGrade, VadminPefStudent.grade_id == VadminPefGrade.id)
        .join(VadminPefClass, VadminPefStudent.class_id == VadminPefClass.id)
        .where(VadminPefStudent.is_delete == false(), VadminPefStudent.phone == telephone)
        .order_by(VadminPefStudent.update_datetime.desc(), VadminPefStudent.id.desc())
    )
    row = (await db.execute(sql)).first()
    if not row:
        return None
    student, school_name, grade_name, class_name = row
    return {
        'student': student,
        'school_name': school_name,
        'grade_name': grade_name,
        'class_name': class_name
    }


def _stage_text(stage_type: str | None) -> str:
    stage_map = {
        'primary': '小学',
        'mid': '初中',
        'high': '高中',
        'university': '大学'
    }
    return stage_map.get(stage_type, stage_type or '')

def _pe_slot_codes(rows: list[VadminSportScore]) -> tuple[dict[str, str], dict[str, str]]:
    slot_keywords = {
        'gate': ['门槛', '1000', '800', '耐力', '长跑', '跑'],
        'rope': ['跳绳'],
        'jump': ['跳远'],
        'ball': ['实心球']
    }
    mapped = pick_items_by_keywords(rows, slot_keywords, fallback_size=4)
    ordered: list[str] = []
    for key in ['gate', 'rope', 'jump', 'ball']:
        code = mapped.get(key)
        if code and code not in ordered:
            ordered.append(code)
    for code in mapped.values():
        if code and code not in ordered:
            ordered.append(code)
    while len(ordered) < 4:
        ordered.append('')
    item_name_map: dict[str, str] = {}
    for row in rows:
        item_name_map.setdefault(row.item_code, row.item_name)
    return {'gate': ordered[0], 'rope': ordered[1], 'jump': ordered[2], 'ball': ordered[3]}, item_name_map


def _rows_item_avg_score(rows: list[VadminSportScore], item_code: str) -> float:
    if not item_code:
        return 0.0
    return avg([to_float(r.score_value) for r in rows if r.item_code == item_code])


def _rows_item_avg_raw(rows: list[VadminSportScore], item_code: str) -> float:
    if not item_code:
        return 0.0
    return avg([to_float(r.raw_score) for r in rows if r.item_code == item_code])


def _student_total_map(rows: list[VadminSportScore]) -> dict[str, float]:
    grouped = group_scores_by_student(rows)
    return {student_no: student_total_score(s_rows) for student_no, s_rows in grouped.items()}


def _rate_from_totals(totals: list[float]) -> dict[str, float]:
    if not totals:
        return {'pass_rate': 0.0, 'excellent_rate': 0.0, 'full_rate': 0.0}
    pass_count = sum(1 for total in totals if total >= PE_PASS_LINE)
    excellent_count = sum(1 for total in totals if total >= PE_EXCELLENT_LINE)
    full_count = sum(1 for total in totals if total >= PE_FULL_LINE)
    total_count = len(totals)
    return {
        'pass_rate': pct(pass_count, total_count),
        'excellent_rate': pct(excellent_count, total_count),
        'full_rate': pct(full_count, total_count)
    }


def _threshold_for_codes(
        threshold_map: dict[str, dict[str, float]],
        codes: list[str],
        default_pass: float,
        default_excellent: float,
        default_full: float
) -> dict[str, float]:
    pass_values = [threshold_map.get(c, {}).get('pass', 0.0) for c in codes if c]
    excellent_values = [threshold_map.get(c, {}).get('excellent', 0.0) for c in codes if c]
    full_values = [threshold_map.get(c, {}).get('full', 0.0) for c in codes if c]
    pass_values = [v for v in pass_values if v > 0]
    excellent_values = [v for v in excellent_values if v > 0]
    full_values = [v for v in full_values if v > 0]
    return {
        'pass': round2(sum(pass_values) / len(pass_values)) if pass_values else default_pass,
        'excellent': round2(sum(excellent_values) / len(excellent_values)) if excellent_values else default_excellent,
        'full': round2(max(full_values)) if full_values else default_full
    }


def _empty_overview() -> dict[str, Any]:
    return {
        'kpi': {'total_students': 0, 'avg_score': 0, 'pass_rate': 0, 'excellent_rate': 0, 'full_rate': 0},
        'item_avg': {'items': [], 'values': [], 'threshold': {'pass': 10, 'excellent': 14, 'full': 20}},
        'class_rate': {'classes': [], 'pass_rate': [], 'excellent_rate': [], 'full_rate': []},
        'batch_trend': {'batches': [], 'avg_score': [], 'pass_line': [], 'excellent_line': [], 'full_line': []},
        'class_list': []
    }


def _empty_student() -> dict[str, Any]:
    return {
        'profile': {},
        'stats': {},
        'total_trend': {'batches': [], 'total': [], 'pass_line': [], 'excellent_line': [], 'full_line': []},
        'item_trend': {'batches': [], 'series': []},
        'detail_list': []
    }


def _empty_class() -> dict[str, Any]:
    return {
        'kpi': {'avg_score': 0, 'pass_rate': 0, 'excellent_rate': 0, 'full_rate': 0},
        'history_avg': {'batches': [], 'series': []},
        'history_item_bar': {
            'batches': [],
            'rope_avg': [],
            'jump_avg': [],
            'ball_avg': [],
            'threshold': {'pass': 10, 'excellent': 14, 'full': 20}
        },
        'rank_list': []
    }


def _empty_grade() -> dict[str, Any]:
    return {
        'kpi': {'avg_score': 0, 'pass_rate': 0, 'excellent_rate': 0, 'full_rate': 0},
        'class_avg_compare': {'classes': [], 'avg_score': [], 'threshold': {'pass': 30, 'excellent': 40, 'full': 50}},
        'class_rate': {'classes': [], 'pass_rate': [], 'excellent_rate': [], 'full_rate': []},
        'class_item_compare': {
            'classes': [],
            'gate_point_avg': [],
            'rope_point_avg': [],
            'jump_point_avg': [],
            'ball_point_avg': [],
            'gate_score_avg': [],
            'rope_score_avg': [],
            'jump_score_avg': [],
            'ball_score_avg': []
        },
        'class_history_trend': {'batches': [], 'series': []},
        'class_list': []
    }


def _normalize_gender(gender: str | None) -> str:
    text = (gender or '').strip().lower()
    if ('男' in text) or ('male' in text) or text in {'m', '1'}:
        return 'male'
    if ('女' in text) or ('female' in text) or text in {'f', '0', '2'}:
        return 'female'
    return 'all'


def _parse_raw_score(raw: Any) -> float | None:
    return RuleEngine.parse_time_to_seconds(raw)


def _select_rule(item_rules: list[VadminSportStandardItem], gender: str | None) -> VadminSportStandardItem | None:
    if not item_rules:
        return None
    target = _normalize_gender(gender)
    normalized_rules = []
    for rule in item_rules:
        g = _normalize_gender(rule.gender)
        normalized_rules.append((g, rule))
    for g, rule in normalized_rules:
        if g == target:
            return rule
    for g, rule in normalized_rules:
        if g == 'all':
            return rule
    return item_rules[0]


def _calc_by_rule(
        raw_score: float | None,
        rule: VadminSportStandardItem | None,
        conflict_policy: str,
        grade_name: str = ''
) -> dict[str, Any]:
    if raw_score is None or not rule:
        return {}

    mode = (rule.calc_mode or 'segment').strip().lower()
    if mode == 'segment':
        segments = rule.segment_json
        if isinstance(segments, str):
            try:
                segments = json.loads(segments)
            except Exception:
                segments = None
        if isinstance(segments, list) and segments:
            return RuleEngine.eval_by_segment(raw_score, segments, grade_name=grade_name, conflict_policy=conflict_policy)
        return {}

    pass_v = to_float(rule.pass_threshold, default=0.0)
    excellent_v = to_float(rule.excellent_threshold, default=0.0)
    full_v = to_float(rule.full_threshold, default=0.0)
    if pass_v == 0 and excellent_v == 0 and full_v == 0:
        return {}

    is_lower_better = False
    if full_v and pass_v:
        is_lower_better = full_v < pass_v
    elif excellent_v and pass_v:
        is_lower_better = excellent_v < pass_v

    if is_lower_better:
        is_pass = raw_score <= pass_v if pass_v else False
        is_excellent = raw_score <= excellent_v if excellent_v else False
        is_full = raw_score <= full_v if full_v else False
    else:
        is_pass = raw_score >= pass_v if pass_v else False
        is_excellent = raw_score >= excellent_v if excellent_v else False
        is_full = raw_score >= full_v if full_v else False

    return {
        'is_pass': is_pass,
        'is_excellent': is_excellent,
        'is_full': is_full
    }


@app.get('/overview', summary='体考成绩总览')
async def get_overview(
        batch_id: int | None = Query(None),
        stage_type: str | None = Query(None),
        school_name: str | None = Query(None),
        grade_name: str | None = Query(None),
        class_name: str | None = Query(None),
        school_id: int | None = Query(None),
        grade_id: int | None = Query(None),
        class_id: int | None = Query(None),
        auth: Auth = Depends(FullAdminAuth(permissions=['pe.analysis.overview']))
):
    school_name, grade_name, class_name = await resolve_dept_filter_names(
        auth.db,
        school_id=school_id,
        grade_id=grade_id,
        class_id=class_id,
        school_name=school_name,
        grade_name=grade_name,
        class_name=class_name
    )

    batches = await list_batches(
        auth.db,
        biz_type='pe',
        stage_type=stage_type,
        batch_id=batch_id,
        school_name=school_name,
        grade_name=grade_name,
        class_name=class_name,
        limit=8 if not batch_id else 1
    )
    batches = [b for b in batches if _in_scope(auth, b.school_name, b.class_name)]
    if not batches:
        return SuccessResponse(_empty_overview())

    target_batch = batches[0]
    current_rows = await list_scores(
        auth.db,
        biz_type='pe',
        batch_ids=[target_batch.id],
        school_name=school_name,
        grade_name=grade_name,
        class_name=class_name
    )
    current_rows = [r for r in current_rows if _in_scope(auth, r.school_name, r.class_name)]
    if not current_rows:
        data = _empty_overview()
        trend_batches = sorted(batches, key=lambda x: x.id)
        data['batch_trend']['batches'] = [b.batch_name for b in trend_batches]
        data['batch_trend']['pass_line'] = [PE_PASS_LINE for _ in trend_batches]
        data['batch_trend']['excellent_line'] = [PE_EXCELLENT_LINE for _ in trend_batches]
        data['batch_trend']['full_line'] = [PE_FULL_LINE for _ in trend_batches]
        data['batch_trend']['avg_score'] = [0 for _ in trend_batches]
        return SuccessResponse(data)

    slot_codes, item_name_map = _pe_slot_codes(current_rows)
    threshold_map = await get_standard_item_thresholds(auth.db, target_batch.standard_id)

    student_totals = list(_student_total_map(current_rows).values())
    rate = _rate_from_totals(student_totals)
    kpi = {
        'total_students': len(student_totals),
        'avg_score': avg(student_totals),
        'pass_rate': rate['pass_rate'],
        'excellent_rate': rate['excellent_rate'],
        'full_rate': rate['full_rate']
    }

    class_groups = group_scores_by_class(current_rows)
    class_list = []
    chart_classes = []
    pass_rates = []
    excellent_rates = []
    full_rates = []
    for (school, cls), rows in sorted(class_groups.items(), key=lambda x: (x[0][0], x[0][1])):
        class_totals = list(_student_total_map(rows).values())
        class_rate = _rate_from_totals(class_totals)
        class_list.append({
            'school_name': school,
            'class_name': cls,
            'gate_score': format_score(_rows_item_avg_raw(rows, slot_codes['gate'])),
            'gate_point': _rows_item_avg_score(rows, slot_codes['gate']),
            'rope_score': format_score(_rows_item_avg_raw(rows, slot_codes['rope'])),
            'rope_point': _rows_item_avg_score(rows, slot_codes['rope']),
            'jump_score': format_score(_rows_item_avg_raw(rows, slot_codes['jump'])),
            'jump_point': _rows_item_avg_score(rows, slot_codes['jump']),
            'ball_score': format_score(_rows_item_avg_raw(rows, slot_codes['ball'])),
            'ball_point': _rows_item_avg_score(rows, slot_codes['ball']),
            'avg_total': avg(class_totals),
            'pass_rate': class_rate['pass_rate'],
            'excellent_rate': class_rate['excellent_rate'],
            'full_rate': class_rate['full_rate']
        })
        chart_classes.append(f'{school}-{cls}')
        pass_rates.append(class_rate['pass_rate'])
        excellent_rates.append(class_rate['excellent_rate'])
        full_rates.append(class_rate['full_rate'])

    item_codes = [slot_codes['gate'], slot_codes['rope'], slot_codes['jump'], slot_codes['ball']]
    item_avg = {
        'items': [item_name_map.get(code, code or '-') for code in item_codes],
        'values': [_rows_item_avg_score(current_rows, code) for code in item_codes],
        'threshold': _threshold_for_codes(threshold_map, item_codes, 10, 14, 20)
    }

    trend_batches = sorted(batches, key=lambda x: x.id)
    trend_rows = await list_scores(
        auth.db,
        biz_type='pe',
        batch_ids=[b.id for b in trend_batches],
        school_name=school_name,
        grade_name=grade_name,
        class_name=class_name
    )
    trend_rows = [r for r in trend_rows if _in_scope(auth, r.school_name, r.class_name)]
    trend_group = group_scores_by_batch(trend_rows)
    trend_avg = []
    for batch in trend_batches:
        batch_totals = list(_student_total_map(trend_group.get(batch.id, [])).values())
        trend_avg.append(avg(batch_totals))

    data = {
        'kpi': kpi,
        'item_avg': item_avg,
        'class_rate': {
            'classes': chart_classes,
            'pass_rate': pass_rates,
            'excellent_rate': excellent_rates,
            'full_rate': full_rates
        },
        'batch_trend': {
            'batches': [b.batch_name for b in trend_batches],
            'avg_score': trend_avg,
            'pass_line': [PE_PASS_LINE for _ in trend_batches],
            'excellent_line': [PE_EXCELLENT_LINE for _ in trend_batches],
            'full_line': [PE_FULL_LINE for _ in trend_batches]
        },
        'class_list': class_list
    }
    data['class_list'] = _filter_rows_by_scope(auth, data['class_list'], ['school_name', 'class_name'])
    return SuccessResponse(data)

@app.get('/analysis/student', summary='体考学生阶段对比')
async def get_student_analysis(
        stage_type: str | None = Query(None),
        school_name: str | None = Query(None),
        grade_name: str | None = Query(None),
        class_name: str | None = Query(None),
        student_no: str | None = Query(None),
        student_keyword: str | None = Query(None),
        student_id: int | None = Query(None),
        school_id: int | None = Query(None),
        grade_id: int | None = Query(None),
        class_id: int | None = Query(None),
        auth: Auth = Depends(FullAdminAuth(permissions=['pe.analysis.student']))
):
    school_name, grade_name, class_name = await resolve_dept_filter_names(
        auth.db,
        school_id=school_id,
        grade_id=grade_id,
        class_id=class_id,
        school_name=school_name,
        grade_name=grade_name,
        class_name=class_name
    )
    if (not student_no) and student_id:
        student_no = str(student_id)

    batches = await list_batches(
        auth.db,
        biz_type='pe',
        stage_type=stage_type,
        school_name=school_name,
        grade_name=grade_name,
        class_name=class_name,
        limit=24
    )
    # 兼容历史数据：若传入 stage_type 无匹配，自动回退到不限制学段再查一次
    if not batches and stage_type:
        batches = await list_batches(
            auth.db,
            biz_type='pe',
            stage_type=None,
            school_name=school_name,
            grade_name=grade_name,
            class_name=class_name,
            limit=24
        )
    batches = [b for b in batches if _in_scope(auth, b.school_name, b.class_name)]
    if not batches:
        return SuccessResponse(_empty_student())

    batch_map = {b.id: b for b in batches}
    all_rows = await list_scores(
        auth.db,
        biz_type='pe',
        batch_ids=list(batch_map.keys()),
        school_name=school_name,
        grade_name=grade_name,
        class_name=class_name,
        student_no=student_no,
        student_keyword=student_keyword
    )
    # 兼容历史数据：若按组织维度无结果，且已明确 student_no，则放宽组织维度重查
    if not all_rows and student_no:
        all_rows = await list_scores(
            auth.db,
            biz_type='pe',
            batch_ids=list(batch_map.keys()),
            school_name=None,
            grade_name=None,
            class_name=None,
            student_no=student_no,
            student_keyword=student_keyword
        )
    all_rows = [r for r in all_rows if _in_scope(auth, r.school_name, r.class_name)]
    if not all_rows:
        return SuccessResponse(_empty_student())

    by_student = group_scores_by_student(all_rows)
    selected_student_no = student_no
    if selected_student_no and selected_student_no not in by_student:
        return SuccessResponse(_empty_student())
    if not selected_student_no:
        selected_student_no = sorted(
            by_student.keys(),
            key=lambda no: (len(by_student[no]), max(r.batch_id for r in by_student[no])),
            reverse=True
        )[0]

    rows = by_student.get(selected_student_no, [])
    if not rows:
        return SuccessResponse(_empty_student())

    slot_codes, _item_name_map = _pe_slot_codes(rows)
    by_batch = group_scores_by_batch(rows)
    sorted_batches = sorted((batch_map[bid] for bid in by_batch.keys() if bid in batch_map), key=lambda b: b.id)
    if not sorted_batches:
        return SuccessResponse(_empty_student())

    latest_batch = sorted_batches[-1]
    latest_rows = by_batch.get(latest_batch.id, [])
    latest_first = latest_rows[0]
    profile = {
        'student_name': latest_first.student_name,
        'gender': latest_first.gender,
        'mobile': latest_first.mobile,
        'school': latest_first.school_name,
        'enrollment_year': 0,
        'grade': latest_first.grade_name,
        'class_name': latest_first.class_name,
        'student_no': latest_first.student_no,
        'exam_type': _stage_text(latest_batch.stage_type)
    }

    if not _can_access_row(auth, profile, ['school', 'class_name']):
        return SuccessResponse(_empty_student())

    total_by_batch = {b.id: student_total_score(by_batch.get(b.id, [])) for b in sorted_batches}
    latest_total = total_by_batch.get(latest_batch.id, 0.0)

    pass_items = sum(1 for r in latest_rows if bool(r.is_pass))
    fail_items = sum(1 for r in latest_rows if not bool(r.is_pass))
    excellent_items_list = [r.item_name for r in latest_rows if bool(r.is_excellent)]
    full_items_list = [r.item_name for r in latest_rows if bool(r.is_full)]

    stats = {
        'latest_total': latest_total,
        'history_max_total': max(total_by_batch.values()) if total_by_batch else 0.0,
        'pass_items': pass_items,
        'fail_items': fail_items,
        'excellent_item_count': len(excellent_items_list),
        'full_item_count': len(full_items_list),
        'excellent_items': '、'.join(excellent_items_list) if excellent_items_list else '-',
        'full_items': '、'.join(full_items_list) if full_items_list else '-'
    }

    total_trend = {
        'batches': [b.batch_name for b in sorted_batches],
        'total': [total_by_batch.get(b.id, 0.0) for b in sorted_batches],
        'pass_line': [PE_PASS_LINE for _ in sorted_batches],
        'excellent_line': [PE_EXCELLENT_LINE for _ in sorted_batches],
        'full_line': [PE_FULL_LINE for _ in sorted_batches]
    }

    trend_codes = [slot_codes['rope'], slot_codes['jump'], slot_codes['ball']]
    trend_codes = [code for code in trend_codes if code]
    if not trend_codes:
        trend_codes = sorted({r.item_code for r in rows})[:3]

    series = []
    for code in trend_codes:
        item_name = next((r.item_name for r in rows if r.item_code == code), code)
        values = []
        for batch in sorted_batches:
            batch_rows = [r for r in by_batch.get(batch.id, []) if r.item_code == code]
            values.append(avg([to_float(r.score_value) for r in batch_rows]))
        series.append({'name': item_name, 'values': values})

    item_trend = {'batches': [b.batch_name for b in sorted_batches], 'series': series}

    detail_list = []
    for batch in sorted(sorted_batches, key=lambda b: b.id, reverse=True):
        b_rows = by_batch.get(batch.id, [])
        item_map = {r.item_code: r for r in b_rows}
        gate_row = item_map.get(slot_codes['gate'])
        rope_row = item_map.get(slot_codes['rope'])
        jump_row = item_map.get(slot_codes['jump'])
        ball_row = item_map.get(slot_codes['ball'])
        total_score = student_total_score(b_rows)
        state = classify_total(total_score, PE_PASS_LINE, PE_EXCELLENT_LINE, PE_FULL_LINE)
        comment = next((r.teacher_comment for r in b_rows if r.teacher_comment), '')
        detail_list.append({
            'batch_name': batch.batch_name,
            'gate_score': format_score(to_float(gate_row.raw_score) if gate_row else None),
            'gate_point': round2(to_float(gate_row.score_value)) if gate_row else 0.0,
            'rope_score': format_score(to_float(rope_row.raw_score) if rope_row else None),
            'rope_point': round2(to_float(rope_row.score_value)) if rope_row else 0.0,
            'jump_score': format_score(to_float(jump_row.raw_score) if jump_row else None),
            'jump_point': round2(to_float(jump_row.score_value)) if jump_row else 0.0,
            'ball_score': format_score(to_float(ball_row.raw_score) if ball_row else None),
            'ball_point': round2(to_float(ball_row.score_value)) if ball_row else 0.0,
            'total_score': total_score,
            'pass_state': state['is_pass'],
            'excellent_state': state['is_excellent'],
            'teacher_comment': comment
        })

    return SuccessResponse({
        'profile': profile,
        'stats': stats,
        'total_trend': total_trend,
        'item_trend': item_trend,
        'detail_list': detail_list
    })

@app.get('/analysis/student/self', summary='体考学生本人视图')
async def get_student_analysis_self(auth: Auth = Depends(AllUserAuth())):
    ctx = await _get_self_student_context(auth.db, getattr(auth.user, 'telephone', None))
    if not ctx:
        return SuccessResponse(_empty_student())
    resp = await get_student_analysis(
        stage_type=None,
        school_name=ctx['school_name'],
        grade_name=ctx['grade_name'],
        class_name=ctx['class_name'],
        student_no=ctx['student'].student_no,
        auth=auth
    )
    payload = getattr(resp, 'data', {}).get('data')
    if isinstance(payload, dict) and isinstance(payload.get('profile'), dict):
        payload['profile']['student_name'] = ctx['student'].name
        payload['profile']['gender'] = ctx['student'].gender
        payload['profile']['mobile'] = ctx['student'].phone
        payload['profile']['school'] = ctx['school_name']
        payload['profile']['grade'] = ctx['grade_name']
        payload['profile']['class_name'] = ctx['class_name']
        payload['profile']['student_no'] = ctx['student'].student_no
    return resp


@app.get('/analysis/class', summary='体考班级对比分析')
async def get_class_analysis(
        batch_id: int | None = Query(None),
        stage_type: str | None = Query(None),
        school_name: str | None = Query(None),
        grade_name: str | None = Query(None),
        class_name: str | None = Query(None),
        school_id: int | None = Query(None),
        grade_id: int | None = Query(None),
        class_id: int | None = Query(None),
        auth: Auth = Depends(FullAdminAuth(permissions=['pe.analysis.class']))
):
    school_name, grade_name, class_name = await resolve_dept_filter_names(
        auth.db,
        school_id=school_id,
        grade_id=grade_id,
        class_id=class_id,
        school_name=school_name,
        grade_name=grade_name,
        class_name=class_name
    )

    batch_candidates = await list_batches(
        auth.db,
        biz_type='pe',
        stage_type=stage_type,
        batch_id=batch_id,
        school_name=school_name,
        grade_name=grade_name,
        class_name=class_name,
        limit=1
    )
    batch_candidates = [b for b in batch_candidates if _in_scope(auth, b.school_name, b.class_name)]
    if not batch_candidates:
        return SuccessResponse(_empty_class())

    target_batch = batch_candidates[0]
    target_school = school_name or target_batch.school_name
    target_grade = grade_name or target_batch.grade_name
    target_class = class_name or target_batch.class_name

    current_rows = await list_scores(
        auth.db,
        biz_type='pe',
        batch_ids=[target_batch.id],
        school_name=target_school,
        grade_name=target_grade,
        class_name=target_class
    )
    current_rows = [r for r in current_rows if _in_scope(auth, r.school_name, r.class_name)]
    if not current_rows:
        return SuccessResponse(_empty_class())

    slot_codes, item_name_map = _pe_slot_codes(current_rows)
    threshold_map = await get_standard_item_thresholds(auth.db, target_batch.standard_id)

    student_groups = group_scores_by_student(current_rows)
    total_list = [student_total_score(rows) for rows in student_groups.values()]
    rate = _rate_from_totals(total_list)
    kpi = {
        'avg_score': avg(total_list),
        'pass_rate': rate['pass_rate'],
        'excellent_rate': rate['excellent_rate'],
        'full_rate': rate['full_rate']
    }

    rank_data = []
    for student_no, s_rows in student_groups.items():
        item_map = {r.item_code: r for r in s_rows}
        gate_row = item_map.get(slot_codes['gate'])
        rope_row = item_map.get(slot_codes['rope'])
        jump_row = item_map.get(slot_codes['jump'])
        ball_row = item_map.get(slot_codes['ball'])
        total_score = student_total_score(s_rows)
        state = classify_total(total_score, PE_PASS_LINE, PE_EXCELLENT_LINE, PE_FULL_LINE)
        first = s_rows[0]
        comment = next((r.teacher_comment for r in s_rows if r.teacher_comment), '')
        rank_data.append({
            'student_name': first.student_name,
            'gender': first.gender,
            'student_no': student_no,
            'gate_score': format_score(to_float(gate_row.raw_score) if gate_row else None),
            'gate_point': round2(to_float(gate_row.score_value)) if gate_row else 0.0,
            'rope_score': format_score(to_float(rope_row.raw_score) if rope_row else None),
            'rope_point': round2(to_float(rope_row.score_value)) if rope_row else 0.0,
            'jump_score': format_score(to_float(jump_row.raw_score) if jump_row else None),
            'jump_point': round2(to_float(jump_row.score_value)) if jump_row else 0.0,
            'ball_score': format_score(to_float(ball_row.raw_score) if ball_row else None),
            'ball_point': round2(to_float(ball_row.score_value)) if ball_row else 0.0,
            'total_score': total_score,
            'pass_state': state['is_pass'],
            'excellent_state': state['is_excellent'],
            'teacher_comment': comment
        })

    rank_data = sorted(rank_data, key=lambda x: x['total_score'], reverse=True)
    for idx, row in enumerate(rank_data, start=1):
        row['rank'] = idx

    history_batches = await list_batches(
        auth.db,
        biz_type='pe',
        stage_type=target_batch.stage_type,
        school_name=target_school,
        grade_name=target_grade,
        class_name=target_class,
        limit=8
    )
    history_batches = [b for b in history_batches if _in_scope(auth, b.school_name, b.class_name)]
    history_batches = sorted(history_batches, key=lambda b: b.id)
    history_rows = await list_scores(
        auth.db,
        biz_type='pe',
        batch_ids=[b.id for b in history_batches],
        school_name=target_school,
        grade_name=target_grade,
        class_name=target_class
    ) if history_batches else []
    history_rows = [r for r in history_rows if _in_scope(auth, r.school_name, r.class_name)]
    history_by_batch = group_scores_by_batch(history_rows)

    history_series = []
    for key in ['gate', 'rope', 'jump', 'ball']:
        code = slot_codes.get(key)
        if not code:
            continue
        values = []
        for batch in history_batches:
            values.append(_rows_item_avg_score(history_by_batch.get(batch.id, []), code))
        history_series.append({'name': f"{item_name_map.get(code, code)}均分", 'values': values})

    history_item_threshold = _threshold_for_codes(
        threshold_map,
        [slot_codes['rope'], slot_codes['jump'], slot_codes['ball']],
        10,
        14,
        20
    )

    data = {
        'kpi': kpi,
        'history_avg': {
            'batches': [b.batch_name for b in history_batches],
            'series': history_series
        },
        'history_item_bar': {
            'batches': [b.batch_name for b in history_batches],
            'rope_avg': [_rows_item_avg_score(history_by_batch.get(b.id, []), slot_codes['rope']) for b in history_batches],
            'jump_avg': [_rows_item_avg_score(history_by_batch.get(b.id, []), slot_codes['jump']) for b in history_batches],
            'ball_avg': [_rows_item_avg_score(history_by_batch.get(b.id, []), slot_codes['ball']) for b in history_batches],
            'threshold': history_item_threshold
        },
        'rank_list': rank_data
    }
    return SuccessResponse(data)

@app.get('/analysis/grade', summary='体考年级对比分析')
async def get_grade_analysis(
        batch_id: int | None = Query(None),
        stage_type: str | None = Query(None),
        school_name: str | None = Query(None),
        grade_name: str | None = Query(None),
        school_id: int | None = Query(None),
        grade_id: int | None = Query(None),
        auth: Auth = Depends(FullAdminAuth(permissions=['pe.analysis.grade']))
):
    school_name, grade_name, _ = await resolve_dept_filter_names(
        auth.db,
        school_id=school_id,
        grade_id=grade_id,
        class_id=None,
        school_name=school_name,
        grade_name=grade_name,
        class_name=None
    )

    batch_candidates = await list_batches(
        auth.db,
        biz_type='pe',
        stage_type=stage_type,
        batch_id=batch_id,
        school_name=school_name,
        grade_name=grade_name,
        limit=1
    )
    batch_candidates = [b for b in batch_candidates if _in_scope(auth, b.school_name, b.class_name)]
    if not batch_candidates:
        return SuccessResponse(_empty_grade())

    target_batch = batch_candidates[0]
    target_school = school_name or target_batch.school_name
    target_grade = grade_name or target_batch.grade_name

    current_rows = await list_scores(
        auth.db,
        biz_type='pe',
        batch_ids=[target_batch.id],
        school_name=target_school,
        grade_name=target_grade
    )
    current_rows = [r for r in current_rows if _in_scope(auth, r.school_name, r.class_name)]
    if not current_rows:
        return SuccessResponse(_empty_grade())

    slot_codes, _item_name_map = _pe_slot_codes(current_rows)

    student_totals = list(_student_total_map(current_rows).values())
    total_rate = _rate_from_totals(student_totals)
    kpi = {
        'avg_score': avg(student_totals),
        'pass_rate': total_rate['pass_rate'],
        'excellent_rate': total_rate['excellent_rate'],
        'full_rate': total_rate['full_rate']
    }

    class_groups = group_scores_by_grade_class(current_rows)
    class_names = sorted(class_groups.keys())

    class_avg_values = []
    class_pass_rates = []
    class_excellent_rates = []
    class_full_rates = []
    class_list = []

    gate_point_avg = []
    rope_point_avg = []
    jump_point_avg = []
    ball_point_avg = []
    gate_score_avg = []
    rope_score_avg = []
    jump_score_avg = []
    ball_score_avg = []

    for cls in class_names:
        rows = class_groups[cls]
        totals = list(_student_total_map(rows).values())
        c_rate = _rate_from_totals(totals)

        g_score = _rows_item_avg_raw(rows, slot_codes['gate'])
        r_score = _rows_item_avg_raw(rows, slot_codes['rope'])
        j_score = _rows_item_avg_raw(rows, slot_codes['jump'])
        b_score = _rows_item_avg_raw(rows, slot_codes['ball'])
        g_point = _rows_item_avg_score(rows, slot_codes['gate'])
        r_point = _rows_item_avg_score(rows, slot_codes['rope'])
        j_point = _rows_item_avg_score(rows, slot_codes['jump'])
        b_point = _rows_item_avg_score(rows, slot_codes['ball'])

        class_avg_values.append(avg(totals))
        class_pass_rates.append(c_rate['pass_rate'])
        class_excellent_rates.append(c_rate['excellent_rate'])
        class_full_rates.append(c_rate['full_rate'])

        gate_score_avg.append(g_score)
        rope_score_avg.append(r_score)
        jump_score_avg.append(j_score)
        ball_score_avg.append(b_score)
        gate_point_avg.append(g_point)
        rope_point_avg.append(r_point)
        jump_point_avg.append(j_point)
        ball_point_avg.append(b_point)

        class_list.append({
            'class_name': cls,
            'gate_score': format_score(g_score),
            'gate_point': g_point,
            'rope_score': format_score(r_score),
            'rope_point': r_point,
            'jump_score': format_score(j_score),
            'jump_point': j_point,
            'ball_score': format_score(b_score),
            'ball_point': b_point,
            'avg_score': avg(totals),
            'pass_rate': c_rate['pass_rate'],
            'excellent_rate': c_rate['excellent_rate'],
            'full_rate': c_rate['full_rate']
        })

    history_batches = await list_batches(
        auth.db,
        biz_type='pe',
        stage_type=target_batch.stage_type,
        school_name=target_school,
        grade_name=target_grade,
        limit=8
    )
    history_batches = [b for b in history_batches if _in_scope(auth, b.school_name, b.class_name)]
    history_batches = sorted(history_batches, key=lambda b: b.id)

    history_rows = await list_scores(
        auth.db,
        biz_type='pe',
        batch_ids=[b.id for b in history_batches],
        school_name=target_school,
        grade_name=target_grade
    ) if history_batches else []
    history_rows = [r for r in history_rows if _in_scope(auth, r.school_name, r.class_name)]

    history_by_batch_student = group_scores_by_batch_student(history_rows)
    class_history_series = []
    for cls in class_names:
        values = []
        for batch in history_batches:
            student_scores: dict[str, float] = {}
            for (bid, student_no), rows in history_by_batch_student.items():
                if bid != batch.id:
                    continue
                first = rows[0] if rows else None
                if not first or first.class_name != cls:
                    continue
                student_scores[student_no] = student_total_score(rows)
            values.append(avg(student_scores.values()))
        class_history_series.append({'name': cls, 'values': values})

    data = {
        'kpi': kpi,
        'class_avg_compare': {
            'classes': class_names,
            'avg_score': class_avg_values,
            'threshold': {'pass': PE_PASS_LINE, 'excellent': PE_EXCELLENT_LINE, 'full': PE_FULL_LINE}
        },
        'class_rate': {
            'classes': class_names,
            'pass_rate': class_pass_rates,
            'excellent_rate': class_excellent_rates,
            'full_rate': class_full_rates
        },
        'class_item_compare': {
            'classes': class_names,
            'gate_point_avg': gate_point_avg,
            'rope_point_avg': rope_point_avg,
            'jump_point_avg': jump_point_avg,
            'ball_point_avg': ball_point_avg,
            'gate_score_avg': gate_score_avg,
            'rope_score_avg': rope_score_avg,
            'jump_score_avg': jump_score_avg,
            'ball_score_avg': ball_score_avg
        },
        'class_history_trend': {
            'batches': [b.batch_name for b in history_batches],
            'series': class_history_series
        },
        'class_list': class_list
    }
    return SuccessResponse(data)

@app.get('/entry/template', summary='体考录入模板配置')
async def get_entry_template(auth: Auth = Depends(FullAdminAuth(permissions=['pe.score.entry']))):
    data = {
        'items': ['门槛项', '跳绳', '跳远', '实心球'],
        'calc_policy': '支持仅录入成绩，自动计算分值',
        'conflict_policy': '就低不就高'
    }
    return SuccessResponse(data)


@app.get('/report/config', summary='体考报表配置')
async def get_report_config(auth: Auth = Depends(FullAdminAuth(permissions=['pe.report']))):
    data = {
        'report_types': ['学生报表', '班级报表', '年级报表'],
        'default_fields': ['学生基础信息', '项目成绩', '项目评分成绩', '总分', '及格/优秀/满分状态', '标准版本号'],
        'history': [
            {
                'id': 1,
                'time': '2026-03-20 10:00',
                'type': '学生报表',
                'status': '成功',
                'version': 'V2026.1'
            },
            {
                'id': 2,
                'time': '2026-03-19 15:30',
                'type': '班级报表',
                'status': '失败',
                'version': 'V2026.1'
            }
        ]
    }
    return SuccessResponse(data)


@app.get('/standard/list', summary='体考标准列表')
async def get_standard_list(auth: Auth = Depends(FullAdminAuth(permissions=['pe.standard']))):
    try:
        stage_type = None
        data = await list_standard_with_items(
            auth.db,
            biz_type='pe',
            stage_type=stage_type
        )
        if data:
            return SuccessResponse(data)
    except Exception:
        pass

    data = [
        {
            'id': 1,
            'name': '重庆市2026年体育初中标准',
            'region': '重庆市',
            'year': 2026,
            'exam_type': '初中',
            'version': 'V2026.1',
            'status': '已发布'
        }
    ]
    return SuccessResponse(data)


@app.post('/standard', summary='创建体考标准')
async def create_standard(
        payload: dict = Body(...),
        auth: Auth = Depends(FullAdminAuth(permissions=['pe.standard']))
):
    standard = VadminSportStandard(
        biz_type='pe',
        name=payload.get('name'),
        region=payload.get('region'),
        year=int(payload.get('year')),
        stage_type=payload.get('stage_type', 'mid'),
        version=payload.get('version'),
        status=payload.get('status', 'draft'),
        source_type=payload.get('source_type', 'manual'),
        conflict_policy=payload.get('conflict_policy', 'lower_priority'),
        remark=payload.get('remark')
    )
    auth.db.add(standard)
    await auth.db.flush()

    items = payload.get('items') or []
    for idx, item in enumerate(items):
        auth.db.add(VadminSportStandardItem(
            standard_id=standard.id,
            item_code=item.get('item_code', f'item_{idx + 1}'),
            item_name=item.get('item_name', f'项目{idx + 1}'),
            gender=item.get('gender', 'all'),
            calc_mode=item.get('calc_mode', 'segment'),
            pass_threshold=item.get('pass_threshold'),
            excellent_threshold=item.get('excellent_threshold'),
            full_threshold=item.get('full_threshold'),
            segment_json=item.get('segment_json'),
            is_required=bool(item.get('is_required', True)),
            is_gate_item=bool(item.get('is_gate_item', False)),
            max_score=item.get('max_score', 0),
            sort=item.get('sort', idx + 1)
        ))
    await auth.db.flush()
    return SuccessResponse({'id': standard.id})


@app.post('/batch', summary='创建体考测试批次')
async def create_batch(
        payload: dict = Body(...),
        auth: Auth = Depends(FullAdminAuth(permissions=['pe.score.entry']))
):
    if not _in_scope(auth, payload.get('school_name'), payload.get('class_name')):
        return ErrorResponse('无权限操作当前学校/班级数据')
    batch = VadminSportBatch(
        biz_type='pe',
        batch_name=payload.get('batch_name'),
        standard_id=int(payload.get('standard_id')),
        school_name=payload.get('school_name') or '',
        grade_name=payload.get('grade_name') or '',
        class_name=payload.get('class_name') or '',
        stage_type=payload.get('stage_type', 'mid'),
        start_date=payload.get('start_date'),
        end_date=payload.get('end_date'),
        status=payload.get('status', 'draft'),
        remark=payload.get('remark')
    )
    auth.db.add(batch)
    await auth.db.flush()
    return SuccessResponse({'id': batch.id})


@app.get('/batch/options', summary='体考批次选项')
async def get_batch_options(
        stage_type: str | None = Query(None),
        auth: Auth = Depends(FullAdminAuth(permissions=['pe.score.entry']))
):
    sql = select(VadminSportBatch).where(
        VadminSportBatch.is_delete == false(),
        VadminSportBatch.biz_type == 'pe'
    )
    if stage_type:
        sql = sql.where(VadminSportBatch.stage_type == stage_type)
    sql = sql.order_by(VadminSportBatch.id.desc())
    rows = (await auth.db.scalars(sql)).all()
    rows = [r for r in rows if _in_scope(auth, r.school_name, r.class_name)]
    data = [{'label': r.batch_name, 'value': r.id} for r in rows]
    return SuccessResponse(data)


@app.post('/score/upsert', summary='体考成绩录入/更新')
async def upsert_scores(
        payload: dict = Body(...),
        auth: Auth = Depends(FullAdminAuth(permissions=['pe.score.entry']))
):
    batch_id = int(payload.get('batch_id'))
    batch = (await auth.db.scalars(select(VadminSportBatch).where(
        VadminSportBatch.is_delete == false(),
        VadminSportBatch.biz_type == 'pe',
        VadminSportBatch.id == batch_id
    ).limit(1))).first()
    if not batch:
        return ErrorResponse('批次不存在')

    standard = (await auth.db.scalars(select(VadminSportStandard).where(
        VadminSportStandard.is_delete == false(),
        VadminSportStandard.id == batch.standard_id
    ).limit(1))).first()
    conflict_policy = (standard.conflict_policy if standard else None) or 'lower_priority'
    standard_items = (await auth.db.scalars(select(VadminSportStandardItem).where(
        VadminSportStandardItem.is_delete == false(),
        VadminSportStandardItem.standard_id == batch.standard_id
    ))).all()
    item_rule_map: dict[str, list[VadminSportStandardItem]] = {}
    for rule in standard_items:
        item_rule_map.setdefault(rule.item_code, []).append(rule)

    scores = payload.get('scores') or []
    count = 0

    student_nos = [item.get('student_no') for item in scores if item.get('student_no')]
    if student_nos:
        students = (await auth.db.scalars(select(VadminPefStudent).where(VadminPefStudent.student_no.in_(student_nos)))).all()
        student_map = {s.student_no: s for s in students}
    else:
        student_map = {}

    for item in scores:
        if not _in_scope(auth, item.get('school_name'), item.get('class_name')):
            continue

        raw_score_parsed = _parse_raw_score(item.get('raw_score'))
        item_rules = item_rule_map.get(item.get('item_code') or '', [])
        selected_rule = _select_rule(item_rules, item.get('gender'))
        calc_result = _calc_by_rule(raw_score_parsed, selected_rule, conflict_policy, item.get('grade_name', ''))

        student = student_map.get(item.get('student_no'))
        mobile = student.phone if student else item.get('mobile')
        item_name = selected_rule.item_name if selected_rule else item.get('item_name')

        score_value = item.get('score_value')
        if (score_value is None or score_value == '') and ('score_value' in calc_result):
            score_value = calc_result.get('score_value')
        is_pass = item.get('is_pass')
        is_excellent = item.get('is_excellent')
        is_full = item.get('is_full')
        if is_pass is None:
            is_pass = calc_result.get('is_pass')
        if is_excellent is None:
            is_excellent = calc_result.get('is_excellent')
        if is_full is None:
            is_full = calc_result.get('is_full')

        sql = select(VadminSportScore).where(
            VadminSportScore.is_delete == false(),
            VadminSportScore.biz_type == 'pe',
            VadminSportScore.batch_id == batch_id,
            VadminSportScore.student_no == item.get('student_no'),
            VadminSportScore.item_code == item.get('item_code')
        ).limit(1)
        row = (await auth.db.scalars(sql)).first()
        if row:
            row.raw_score = raw_score_parsed
            row.score_value = score_value
            row.is_pass = is_pass
            row.is_excellent = is_excellent
            row.is_full = is_full
            row.teacher_comment = item.get('teacher_comment')
            row.test_date = item.get('test_date')
            row.mobile = mobile
            row.item_name = item_name
        else:
            auth.db.add(VadminSportScore(
                biz_type='pe',
                batch_id=batch_id,
                student_no=item.get('student_no'),
                student_name=item.get('student_name'),
                gender=item.get('gender'),
                mobile=mobile,
                school_name=item.get('school_name'),
                grade_name=item.get('grade_name'),
                class_name=item.get('class_name'),
                item_code=item.get('item_code'),
                item_name=item_name,
                raw_score=raw_score_parsed,
                score_value=score_value,
                is_pass=is_pass,
                is_excellent=is_excellent,
                is_full=is_full,
                teacher_comment=item.get('teacher_comment'),
                test_date=item.get('test_date')
            ))
        count += 1
    await auth.db.flush()
    return SuccessResponse({'upsert_count': count})


@app.get('/batch/list', summary='体考批次列表')
async def get_batch_list(
        page: int = Query(1),
        limit: int = Query(10),
        batch_name: str | None = Query(None),
        auth: Auth = Depends(FullAdminAuth(permissions=['pe.score.entry']))
):
    sql = select(VadminSportBatch).where(
        VadminSportBatch.is_delete == false(),
        VadminSportBatch.biz_type == 'pe'
    )
    if batch_name:
        sql = sql.where(VadminSportBatch.batch_name.like(f"%{batch_name}%"))
    
    sql = sql.order_by(VadminSportBatch.id.desc())
    rows = (await auth.db.scalars(sql)).all()
    rows = [r for r in rows if _in_scope(auth, r.school_name, r.class_name)]
    
    total = len(rows)
    start = (page - 1) * limit
    end = start + limit
    paged_rows = rows[start:end]
    
    # 转换为 Pydantic 序列化对象字典列表
    return SuccessResponse({
        'total': total,
        'items': [json.loads(schemas.BatchOut.model_validate(r).model_dump_json()) for r in paged_rows]
    })


@app.put('/batch/{id}', summary='更新体考批次')
async def update_batch(
        id: int,
        payload: dict = Body(...),
        auth: Auth = Depends(FullAdminAuth(permissions=['pe.score.entry']))
):
    batch = (await auth.db.scalars(select(VadminSportBatch).where(
        VadminSportBatch.is_delete == false(),
        VadminSportBatch.id == id
    ).limit(1))).first()
    if not batch:
        return ErrorResponse('批次不存在')
    
    if not _in_scope(auth, batch.school_name, batch.class_name):
        return ErrorResponse('无权限操作该数据')

    for key in ['batch_name', 'standard_id', 'status', 'start_date', 'end_date', 'remark', 'school_name', 'grade_name', 'class_name', 'stage_type']:
        if key in payload:
            setattr(batch, key, payload[key])
    
    await auth.db.flush()
    return SuccessResponse('更新成功')


@app.delete('/batch/{id}', summary='删除体考批次')
async def delete_batch(
        id: int,
        auth: Auth = Depends(FullAdminAuth(permissions=['pe.score.entry']))
):
    batch = (await auth.db.scalars(select(VadminSportBatch).where(
        VadminSportBatch.is_delete == false(),
        VadminSportBatch.id == id
    ).limit(1))).first()
    if not batch:
        return ErrorResponse('批次不存在')
    
    if not _in_scope(auth, batch.school_name, batch.class_name):
        return ErrorResponse('无权限操作该数据')

    batch.is_delete = True
    await auth.db.flush()
    return SuccessResponse('删除成功')


@app.get('/students/options', summary='获取学生选项')
async def get_student_options(
        school_id: int | None = Query(None),
        school_name: str | None = Query(None),
        grade_id: int | None = Query(None),
        grade_name: str | None = Query(None),
        class_id: int | None = Query(None),
        class_name: str | None = Query(None),
        stage_type: str | None = Query(None),
        student_keyword: str | None = Query(None),
        auth: Auth = Depends(FullAdminAuth(permissions=['pe.analysis.student']))
):
    joined_school = False
    joined_grade = False
    joined_class = False
    sql = select(VadminPefStudent).where(
        VadminPefStudent.is_delete == false(),
        VadminPefStudent.is_active == true()
    )
    if school_id:
        sql = sql.where(VadminPefStudent.school_id == school_id)
    if school_name:
        sql = sql.join(VadminPefSchool, VadminPefStudent.school_id == VadminPefSchool.id)
        joined_school = True
        sql = sql.where(VadminPefSchool.school_name == school_name)
    if grade_id:
        sql = sql.where(VadminPefStudent.grade_id == grade_id)
    if grade_name:
        if not joined_grade:
            sql = sql.join(VadminPefGrade, VadminPefStudent.grade_id == VadminPefGrade.id)
            joined_grade = True
        sql = sql.where(VadminPefGrade.grade_name == grade_name)
    if class_id:
        sql = sql.where(VadminPefStudent.class_id == class_id)
    if class_name:
        if not joined_class:
            sql = sql.join(VadminPefClass, VadminPefStudent.class_id == VadminPefClass.id)
            joined_class = True
        sql = sql.where(VadminPefClass.class_name == class_name)
    if stage_type:
        if not joined_school:
            sql = sql.join(VadminPefSchool, VadminPefStudent.school_id == VadminPefSchool.id)
            joined_school = True
        sql = sql.where(
            or_(
                func.find_in_set(stage_type, VadminPefSchool.stage_types) > 0,
                VadminPefSchool.stage_types.is_(None),
                VadminPefSchool.stage_types == ''
            )
        )
    rows = (await auth.db.scalars(sql)).all()
    if student_keyword:
        kw = str(student_keyword).strip()
        if kw:
            rows = [
                r for r in rows
                if kw in (r.student_no or '')
                or kw in (r.name or '')
                or kw in (r.phone or '')
            ]
    
    data = []
    for r in rows:
        data.append({
            'label': f"{r.name} ({r.student_no})",
            'value': r.student_no,
            'gender': r.gender,
            'student_name': r.name,
            'student_no': r.student_no
        })
    return SuccessResponse(data)


@app.get('/report/export', summary='体考报表导出')
async def export_report(
        batch_id: int | None = Query(None),
        school_name: str | None = Query(None),
        grade_name: str | None = Query(None),
        class_name: str | None = Query(None),
        auth: Auth = Depends(FullAdminAuth(permissions=['pe.report']))
):
    if not batch_id:
        return ErrorResponse('请选择批次')
    
    rows = await list_scores(
        auth.db,
        biz_type='pe',
        batch_ids=[batch_id],
        school_name=school_name,
        grade_name=grade_name,
        class_name=class_name
    )
    rows = [r for r in rows if _in_scope(auth, r.school_name, r.class_name)]
    
    if not rows:
        return ErrorResponse('暂无数据可导出')
    
    filename = f"体考成绩报表_{batch_id}.xlsx"
    url = export_scores_to_excel(rows, filename)
    
    return SuccessResponse({'url': url})


@app.get('/score/template', summary='下载体考成绩导入模板')
async def download_score_template(
        auth: Auth = Depends(FullAdminAuth(permissions=['pe.score.entry']))
):
    headers = ["学号", "姓名", "性别", "学校", "年级", "班级", "项目编码", "项目名称", "成绩"]
    from utils.excel.write_xlsx import WriteXlsx
    writer = WriteXlsx()
    filename = "体考成绩导入模板.xlsx"
    writer.create_excel(file_path=filename, save_static=True)
    header_dicts = [{"label": h} for h in headers]
    writer.generate_template(header_dicts)
    writer.close()
    return SuccessResponse({'url': writer.get_file_url()})


@app.post('/standard/import', summary='体考标准 Excel 导入解析')
async def import_standard(
        file: UploadFile = File(...),
        auth: Auth = Depends(FullAdminAuth(permissions=['pe.standard']))
):
    content = await file.read()
    items = StandardImportService.parse_standard_excel(content)
    return SuccessResponse(items)


@app.post('/standard/confirm', summary='体考标准人工确认保存')
async def confirm_standard(
        payload: dict = Body(...),
        auth: Auth = Depends(FullAdminAuth(permissions=['pe.standard']))
):
    payload['source_type'] = 'excel'
    payload['status'] = 'draft'
    return await create_standard(payload, auth)


@app.post('/score/import', summary='体考成绩 Excel 导入解析')
async def import_scores(
        file: UploadFile = File(...),
        auth: Auth = Depends(FullAdminAuth(permissions=['pe.score.entry']))
):
    content = await file.read()
    scores = BatchImportService.parse_score_excel(content)
    return SuccessResponse(scores)


@app.post('/score/confirm', summary='体考成绩导入人工确认保存')
async def confirm_scores(
        payload: dict = Body(...),
        auth: Auth = Depends(FullAdminAuth(permissions=['pe.score.entry']))
):
    return await upsert_scores(payload, auth)


@app.get('/score/batch/students', summary='按项目获取批次学生成绩')
async def get_batch_item_scores(
        batch_id: int = Query(...),
        item_code: str = Query(...),
        auth: Auth = Depends(FullAdminAuth(permissions=['pe.score.entry']))
):
    sql = select(VadminSportScore).where(
        VadminSportScore.batch_id == batch_id,
        VadminSportScore.item_code == item_code,
        VadminSportScore.is_delete == false()
    )
    rows = (await auth.db.scalars(sql)).all()
    # 使用 model_dump_json() 彻底解决 orjson 兼容性问题
    return SuccessResponse([json.loads(schemas.ScoreOut.model_validate(r).model_dump_json()) for r in rows])
