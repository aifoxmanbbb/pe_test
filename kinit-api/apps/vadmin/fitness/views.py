#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import re
from typing import Any
from fastapi import APIRouter, Depends, Body, Query
from sqlalchemy import select, false
from apps.vadmin.auth.utils.current import AllUserAuth, FullAdminAuth
from apps.vadmin.auth.utils.validation.auth import Auth
from apps.vadmin.sport.models import (
    VadminSportStandard,
    VadminSportStandardItem,
    VadminSportBatch,
    VadminSportScore
)
from apps.vadmin.sport.service.analytics_service import (
    avg,
    build_rate_text,
    format_score,
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
    to_float
)
from apps.vadmin.sport.service.rule_engine import RuleEngine
from apps.vadmin.sport.service.standard_service import list_standard_with_items
from utils.response import SuccessResponse, ErrorResponse

app = APIRouter()


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


def _stage_text(stage_type: str | None) -> str:
    if stage_type == 'mid':
        return '初中'
    if stage_type == 'high':
        return '高中'
    return stage_type or ''

def _fitness_slots(rows: list[VadminSportScore]) -> tuple[dict[str, str], dict[str, str]]:
    slot_keywords = {
        'bmi': ['bmi'],
        'lung': ['肺活量'],
        'sprint': ['50', '短跑'],
        'sit': ['坐位体前屈'],
        'rope': ['跳绳']
    }
    mapped = pick_items_by_keywords(rows, slot_keywords, fallback_size=5)
    ordered: list[str] = []
    for key in ['bmi', 'lung', 'sprint', 'sit', 'rope']:
        code = mapped.get(key)
        if code and code not in ordered:
            ordered.append(code)
    for code in mapped.values():
        if code and code not in ordered:
            ordered.append(code)
    while len(ordered) < 5:
        ordered.append('')
    item_name_map: dict[str, str] = {}
    for row in rows:
        item_name_map.setdefault(row.item_code, row.item_name)
    return {
        'bmi': ordered[0],
        'lung': ordered[1],
        'sprint': ordered[2],
        'sit': ordered[3],
        'rope': ordered[4]
    }, item_name_map


def _rows_item_avg_score(rows: list[VadminSportScore], item_code: str) -> float:
    if not item_code:
        return 0.0
    return avg([to_float(r.score_value) for r in rows if r.item_code == item_code])


def _rows_item_avg_raw(rows: list[VadminSportScore], item_code: str) -> float:
    if not item_code:
        return 0.0
    return avg([to_float(r.raw_score) for r in rows if r.item_code == item_code])


def _rate(rows: list[VadminSportScore]) -> dict[str, float]:
    total = len(rows)
    if total == 0:
        return {'pass_rate': 0.0, 'excellent_rate': 0.0, 'full_rate': 0.0}
    pass_cnt = sum(1 for r in rows if bool(r.is_pass))
    excellent_cnt = sum(1 for r in rows if bool(r.is_excellent))
    full_cnt = sum(1 for r in rows if bool(r.is_full))
    return {
        'pass_rate': round2(pass_cnt * 100.0 / total),
        'excellent_rate': round2(excellent_cnt * 100.0 / total),
        'full_rate': round2(full_cnt * 100.0 / total)
    }


def _empty_overview() -> dict[str, Any]:
    return {
        'kpi': {'total_students': 0, 'item_count': 0, 'item_records': 0, 'fail_item_records': 0, 'full_item_records': 0},
        'item_avg': {'items': [], 'values': [], 'threshold': {'pass': 60, 'excellent': 80, 'full': 100}},
        'item_rate': {'items': [], 'pass_rate': [], 'excellent_rate': [], 'full_rate': []},
        'item_trend': {'batches': [], 'series': []},
        'class_list': []
    }


def _empty_student() -> dict[str, Any]:
    return {
        'profile': {},
        'stats': {},
        'item_score_trend': {'batches': [], 'series': []},
        'item_state_trend': {'batches': [], 'fail_items': [], 'pass_items': [], 'excellent_items': [], 'full_items': []},
        'detail_list': []
    }


def _empty_class() -> dict[str, Any]:
    return {
        'kpi': {'student_count': 0, 'item_count': 0, 'item_records': 0, 'fail_item_records': 0, 'full_item_records': 0},
        'history_item_avg': {'batches': [], 'series': []},
        'current_item_rate': {'items': [], 'pass_rate': [], 'excellent_rate': [], 'full_rate': []},
        'rank_list': []
    }


def _empty_grade() -> dict[str, Any]:
    return {
        'kpi': {'class_count': 0, 'student_count': 0, 'item_records': 0, 'fail_item_records': 0, 'full_item_records': 0},
        'class_item_avg': {'classes': [], 'series': []},
        'class_item_rate': {'classes': [], 'pass_rate': [], 'excellent_rate': [], 'full_rate': []},
        'class_item_history': {'batches': [], 'series': []},
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
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw).strip()
    if text == '':
        return None
    if re.fullmatch(r'-?\d+(\.\d+)?', text):
        return float(text)
    m = re.match(r'^\s*(\d+)\s*分\s*(\d+(?:\.\d+)?)\s*秒\s*$', text)
    if m:
        return float(m.group(1)) * 60 + float(m.group(2))
    nums = re.findall(r'-?\d+(?:\.\d+)?', text)
    if len(nums) == 1:
        return float(nums[0])
    return None


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
        conflict_policy: str
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
            return RuleEngine.eval_by_segment(raw_score, segments, conflict_policy=conflict_policy)
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


@app.get('/overview', summary='体测总览')
async def get_overview(
        batch_id: int | None = Query(None),
        stage_type: str | None = Query(None),
        school_name: str | None = Query(None),
        grade_name: str | None = Query(None),
        class_name: str | None = Query(None),
        school_id: int | None = Query(None),
        grade_id: int | None = Query(None),
        class_id: int | None = Query(None),
        auth: Auth = Depends(FullAdminAuth(permissions=['fitness.analysis.overview']))
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
        biz_type='fitness',
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
        biz_type='fitness',
        batch_ids=[target_batch.id],
        school_name=school_name,
        grade_name=grade_name,
        class_name=class_name
    )
    current_rows = [r for r in current_rows if _in_scope(auth, r.school_name, r.class_name)]
    if not current_rows:
        return SuccessResponse(_empty_overview())

    item_codes = sorted({r.item_code for r in current_rows})
    item_name_map: dict[str, str] = {}
    for row in current_rows:
        item_name_map.setdefault(row.item_code, row.item_name)

    by_student = group_scores_by_student(current_rows)
    kpi = {
        'total_students': len(by_student),
        'item_count': len(item_codes),
        'item_records': len(current_rows),
        'fail_item_records': sum(1 for r in current_rows if not bool(r.is_pass)),
        'full_item_records': sum(1 for r in current_rows if bool(r.is_full))
    }

    item_avg_items = []
    item_avg_values = []
    item_rate_pass = []
    item_rate_excellent = []
    item_rate_full = []
    for code in item_codes:
        rows = [r for r in current_rows if r.item_code == code]
        rate = _rate(rows)
        item_avg_items.append(item_name_map.get(code, code))
        item_avg_values.append(_rows_item_avg_score(rows, code))
        item_rate_pass.append(rate['pass_rate'])
        item_rate_excellent.append(rate['excellent_rate'])
        item_rate_full.append(rate['full_rate'])

    trend_batches = sorted(batches, key=lambda x: x.id)
    trend_rows = await list_scores(
        auth.db,
        biz_type='fitness',
        batch_ids=[b.id for b in trend_batches],
        school_name=school_name,
        grade_name=grade_name,
        class_name=class_name
    )
    trend_rows = [r for r in trend_rows if _in_scope(auth, r.school_name, r.class_name)]
    trend_group = group_scores_by_batch(trend_rows)

    top_codes = item_codes[:3]
    item_trend_series = []
    for code in top_codes:
        values = []
        for batch in trend_batches:
            b_rows = [r for r in trend_group.get(batch.id, []) if r.item_code == code]
            values.append(_rows_item_avg_score(b_rows, code))
        item_trend_series.append({'name': f"{item_name_map.get(code, code)}均分", 'values': values})

    class_groups = group_scores_by_class(current_rows)
    slots, _slot_name_map = _fitness_slots(current_rows)
    class_list = []
    for (school, cls), rows in sorted(class_groups.items(), key=lambda x: (x[0][0], x[0][1])):
        bmi_rows = [r for r in rows if r.item_code == slots['bmi']]
        lung_rows = [r for r in rows if r.item_code == slots['lung']]
        sprint_rows = [r for r in rows if r.item_code == slots['sprint']]
        class_list.append({
            'school_name': school,
            'class_name': cls,
            'bmi_score': format_score(_rows_item_avg_raw(rows, slots['bmi'])),
            'bmi_point': _rows_item_avg_score(rows, slots['bmi']),
            'bmi_rate': build_rate_text(_rate(bmi_rows)['pass_rate'], _rate(bmi_rows)['excellent_rate'], _rate(bmi_rows)['full_rate']),
            'lung_score': format_score(_rows_item_avg_raw(rows, slots['lung'])),
            'lung_point': _rows_item_avg_score(rows, slots['lung']),
            'lung_rate': build_rate_text(_rate(lung_rows)['pass_rate'], _rate(lung_rows)['excellent_rate'], _rate(lung_rows)['full_rate']),
            'sprint_score': format_score(_rows_item_avg_raw(rows, slots['sprint'])),
            'sprint_point': _rows_item_avg_score(rows, slots['sprint']),
            'sprint_rate': build_rate_text(_rate(sprint_rows)['pass_rate'], _rate(sprint_rows)['excellent_rate'], _rate(sprint_rows)['full_rate'])
        })

    data = {
        'kpi': kpi,
        'item_avg': {
            'items': item_avg_items,
            'values': item_avg_values,
            'threshold': {'pass': 60, 'excellent': 80, 'full': 100}
        },
        'item_rate': {
            'items': item_avg_items,
            'pass_rate': item_rate_pass,
            'excellent_rate': item_rate_excellent,
            'full_rate': item_rate_full
        },
        'item_trend': {
            'batches': [b.batch_name for b in trend_batches],
            'series': item_trend_series
        },
        'class_list': class_list
    }
    data['class_list'] = _filter_rows_by_scope(auth, data['class_list'], ['school_name', 'class_name'])
    return SuccessResponse(data)

@app.get('/analysis/student', summary='学生体测分析')
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
        auth: Auth = Depends(FullAdminAuth(permissions=['fitness.analysis.student']))
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
        biz_type='fitness',
        stage_type=stage_type,
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
        biz_type='fitness',
        batch_ids=list(batch_map.keys()),
        school_name=school_name,
        grade_name=grade_name,
        class_name=class_name,
        student_no=student_no,
        student_keyword=student_keyword
    )
    all_rows = [r for r in all_rows if _in_scope(auth, r.school_name, r.class_name)]
    if not all_rows:
        return SuccessResponse(_empty_student())

    by_student = group_scores_by_student(all_rows)
    selected_student_no = student_no
    if not selected_student_no or selected_student_no not in by_student:
        selected_student_no = sorted(
            by_student.keys(),
            key=lambda no: (len(by_student[no]), max(r.batch_id for r in by_student[no])),
            reverse=True
        )[0]

    rows = by_student.get(selected_student_no, [])
    if not rows:
        return SuccessResponse(_empty_student())

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
        'stage_type': _stage_text(latest_batch.stage_type)
    }

    if not _can_access_row(auth, profile, ['school', 'class_name']):
        return SuccessResponse(_empty_student())

    pass_items = sum(1 for r in latest_rows if bool(r.is_pass))
    fail_items = sum(1 for r in latest_rows if not bool(r.is_pass))
    excellent_items_list = [r.item_name for r in latest_rows if bool(r.is_excellent)]
    full_items_list = [r.item_name for r in latest_rows if bool(r.is_full)]

    stats = {
        'tested_item_count': len(latest_rows),
        'pass_items': pass_items,
        'fail_items': fail_items,
        'excellent_item_count': len(excellent_items_list),
        'full_item_count': len(full_items_list),
        'fail_items_text': '、'.join([r.item_name for r in latest_rows if not bool(r.is_pass)]) or '-',
        'excellent_items': '、'.join(excellent_items_list) if excellent_items_list else '-',
        'full_items': '、'.join(full_items_list) if full_items_list else '-'
    }

    item_codes = sorted({r.item_code for r in rows})
    item_name_map: dict[str, str] = {}
    for row in rows:
        item_name_map.setdefault(row.item_code, row.item_name)

    trend_codes = item_codes[:4]
    item_score_series = []
    for code in trend_codes:
        values = []
        for batch in sorted_batches:
            b_rows = [r for r in by_batch.get(batch.id, []) if r.item_code == code]
            values.append(_rows_item_avg_score(b_rows, code))
        item_score_series.append({'name': item_name_map.get(code, code), 'values': values})

    item_state = {
        'batches': [b.batch_name for b in sorted_batches],
        'fail_items': [sum(1 for r in by_batch.get(b.id, []) if not bool(r.is_pass)) for b in sorted_batches],
        'pass_items': [sum(1 for r in by_batch.get(b.id, []) if bool(r.is_pass)) for b in sorted_batches],
        'excellent_items': [sum(1 for r in by_batch.get(b.id, []) if bool(r.is_excellent)) for b in sorted_batches],
        'full_items': [sum(1 for r in by_batch.get(b.id, []) if bool(r.is_full)) for b in sorted_batches]
    }

    slots, _slot_names = _fitness_slots(rows)
    detail_list = []
    for batch in sorted(sorted_batches, key=lambda b: b.id, reverse=True):
        b_rows = by_batch.get(batch.id, [])
        item_map = {r.item_code: r for r in b_rows}
        bmi_row = item_map.get(slots['bmi'])
        lung_row = item_map.get(slots['lung'])
        sprint_row = item_map.get(slots['sprint'])
        sit_row = item_map.get(slots['sit'])
        rope_row = item_map.get(slots['rope'])
        comment = next((r.teacher_comment for r in b_rows if r.teacher_comment), '')
        detail_list.append({
            'batch_name': batch.batch_name,
            'bmi_score': format_score(to_float(bmi_row.raw_score) if bmi_row else None),
            'bmi_point': round2(to_float(bmi_row.score_value)) if bmi_row else 0.0,
            'lung_score': format_score(to_float(lung_row.raw_score) if lung_row else None),
            'lung_point': round2(to_float(lung_row.score_value)) if lung_row else 0.0,
            'sprint_score': format_score(to_float(sprint_row.raw_score) if sprint_row else None),
            'sprint_point': round2(to_float(sprint_row.score_value)) if sprint_row else 0.0,
            'sit_score': format_score(to_float(sit_row.raw_score) if sit_row else None),
            'sit_point': round2(to_float(sit_row.score_value)) if sit_row else 0.0,
            'rope_score': format_score(to_float(rope_row.raw_score) if rope_row else None),
            'rope_point': round2(to_float(rope_row.score_value)) if rope_row else 0.0,
            'teacher_comment': comment
        })

    return SuccessResponse({
        'profile': profile,
        'stats': stats,
        'item_score_trend': {'batches': [b.batch_name for b in sorted_batches], 'series': item_score_series},
        'item_state_trend': item_state,
        'detail_list': detail_list
    })

@app.get('/analysis/student/self', summary='体测学生本人视图')
async def get_student_analysis_self(auth: Auth = Depends(AllUserAuth())):
    own_student_no = getattr(auth.user, 'username', None) or getattr(auth.user, 'name', None)
    return await get_student_analysis(stage_type=None, student_no=own_student_no, auth=auth)


@app.get('/analysis/class', summary='班级体测分析')
async def get_class_analysis(
        batch_id: int | None = Query(None),
        stage_type: str | None = Query(None),
        school_name: str | None = Query(None),
        grade_name: str | None = Query(None),
        class_name: str | None = Query(None),
        school_id: int | None = Query(None),
        grade_id: int | None = Query(None),
        class_id: int | None = Query(None),
        auth: Auth = Depends(FullAdminAuth(permissions=['fitness.analysis.class']))
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
        biz_type='fitness',
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
        biz_type='fitness',
        batch_ids=[target_batch.id],
        school_name=target_school,
        grade_name=target_grade,
        class_name=target_class
    )
    current_rows = [r for r in current_rows if _in_scope(auth, r.school_name, r.class_name)]
    if not current_rows:
        return SuccessResponse(_empty_class())

    by_student = group_scores_by_student(current_rows)
    item_codes = sorted({r.item_code for r in current_rows})
    kpi = {
        'student_count': len(by_student),
        'item_count': len(item_codes),
        'item_records': len(current_rows),
        'fail_item_records': sum(1 for r in current_rows if not bool(r.is_pass)),
        'full_item_records': sum(1 for r in current_rows if bool(r.is_full))
    }

    item_name_map: dict[str, str] = {}
    for row in current_rows:
        item_name_map.setdefault(row.item_code, row.item_name)

    rank_data = []
    slots, _slot_names = _fitness_slots(current_rows)
    for student_no, s_rows in by_student.items():
        item_map = {r.item_code: r for r in s_rows}
        bmi_row = item_map.get(slots['bmi'])
        lung_row = item_map.get(slots['lung'])
        sprint_row = item_map.get(slots['sprint'])
        sit_row = item_map.get(slots['sit'])
        rope_row = item_map.get(slots['rope'])
        avg_score = avg([to_float(r.score_value) for r in s_rows])
        first = s_rows[0]
        comment = next((r.teacher_comment for r in s_rows if r.teacher_comment), '')
        rank_data.append({
            'student_name': first.student_name,
            'gender': first.gender,
            'student_no': student_no,
            'bmi_score': format_score(to_float(bmi_row.raw_score) if bmi_row else None),
            'bmi_point': round2(to_float(bmi_row.score_value)) if bmi_row else 0.0,
            'lung_score': format_score(to_float(lung_row.raw_score) if lung_row else None),
            'lung_point': round2(to_float(lung_row.score_value)) if lung_row else 0.0,
            'sprint_score': format_score(to_float(sprint_row.raw_score) if sprint_row else None),
            'sprint_point': round2(to_float(sprint_row.score_value)) if sprint_row else 0.0,
            'sit_score': format_score(to_float(sit_row.raw_score) if sit_row else None),
            'sit_point': round2(to_float(sit_row.score_value)) if sit_row else 0.0,
            'rope_score': format_score(to_float(rope_row.raw_score) if rope_row else None),
            'rope_point': round2(to_float(rope_row.score_value)) if rope_row else 0.0,
            'teacher_comment': comment,
            'avg_score': avg_score
        })

    rank_data = sorted(rank_data, key=lambda x: x['avg_score'], reverse=True)
    for idx, row in enumerate(rank_data, start=1):
        row['rank'] = idx

    history_batches = await list_batches(
        auth.db,
        biz_type='fitness',
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
        biz_type='fitness',
        batch_ids=[b.id for b in history_batches],
        school_name=target_school,
        grade_name=target_grade,
        class_name=target_class
    ) if history_batches else []
    history_rows = [r for r in history_rows if _in_scope(auth, r.school_name, r.class_name)]
    history_by_batch = group_scores_by_batch(history_rows)

    top_codes = item_codes[:4]
    history_series = []
    for code in top_codes:
        values = []
        for batch in history_batches:
            b_rows = [r for r in history_by_batch.get(batch.id, []) if r.item_code == code]
            values.append(_rows_item_avg_score(b_rows, code))
        history_series.append({'name': f"{item_name_map.get(code, code)}均分", 'values': values})

    current_items = item_codes[:5]
    current_pass = []
    current_excellent = []
    current_full = []
    for code in current_items:
        rows = [r for r in current_rows if r.item_code == code]
        rate = _rate(rows)
        current_pass.append(rate['pass_rate'])
        current_excellent.append(rate['excellent_rate'])
        current_full.append(rate['full_rate'])

    data = {
        'kpi': kpi,
        'history_item_avg': {'batches': [b.batch_name for b in history_batches], 'series': history_series},
        'current_item_rate': {
            'items': [item_name_map.get(code, code) for code in current_items],
            'pass_rate': current_pass,
            'excellent_rate': current_excellent,
            'full_rate': current_full
        },
        'rank_list': rank_data
    }
    return SuccessResponse(data)

@app.get('/analysis/grade', summary='年级体测分析')
async def get_grade_analysis(
        batch_id: int | None = Query(None),
        stage_type: str | None = Query(None),
        school_name: str | None = Query(None),
        grade_name: str | None = Query(None),
        school_id: int | None = Query(None),
        grade_id: int | None = Query(None),
        auth: Auth = Depends(FullAdminAuth(permissions=['fitness.analysis.grade']))
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
        biz_type='fitness',
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
        biz_type='fitness',
        batch_ids=[target_batch.id],
        school_name=target_school,
        grade_name=target_grade
    )
    current_rows = [r for r in current_rows if _in_scope(auth, r.school_name, r.class_name)]
    if not current_rows:
        return SuccessResponse(_empty_grade())

    class_groups = group_scores_by_grade_class(current_rows)
    class_names = sorted(class_groups.keys())
    item_codes = sorted({r.item_code for r in current_rows})
    item_name_map: dict[str, str] = {}
    for row in current_rows:
        item_name_map.setdefault(row.item_code, row.item_name)

    student_count = len(group_scores_by_student(current_rows))
    kpi = {
        'class_count': len(class_names),
        'student_count': student_count,
        'item_records': len(current_rows),
        'fail_item_records': sum(1 for r in current_rows if not bool(r.is_pass)),
        'full_item_records': sum(1 for r in current_rows if bool(r.is_full))
    }

    top_codes = item_codes[:4]
    class_item_avg_series = []
    for code in top_codes:
        values = []
        for cls in class_names:
            c_rows = [r for r in class_groups[cls] if r.item_code == code]
            values.append(_rows_item_avg_score(c_rows, code))
        class_item_avg_series.append({'name': f"{item_name_map.get(code, code)}均分", 'values': values})

    focus_code = item_codes[0] if item_codes else ''
    rate_pass = []
    rate_excellent = []
    rate_full = []
    for cls in class_names:
        c_rows = [r for r in class_groups[cls] if r.item_code == focus_code]
        rate = _rate(c_rows)
        rate_pass.append(rate['pass_rate'])
        rate_excellent.append(rate['excellent_rate'])
        rate_full.append(rate['full_rate'])

    history_batches = await list_batches(
        auth.db,
        biz_type='fitness',
        stage_type=target_batch.stage_type,
        school_name=target_school,
        grade_name=target_grade,
        limit=8
    )
    history_batches = [b for b in history_batches if _in_scope(auth, b.school_name, b.class_name)]
    history_batches = sorted(history_batches, key=lambda b: b.id)
    history_rows = await list_scores(
        auth.db,
        biz_type='fitness',
        batch_ids=[b.id for b in history_batches],
        school_name=target_school,
        grade_name=target_grade
    ) if history_batches else []
    history_rows = [r for r in history_rows if _in_scope(auth, r.school_name, r.class_name)]

    history_by_batch_class = {}
    for cls in class_names:
        history_by_batch_class[cls] = []
        for batch in history_batches:
            rows = [r for r in history_rows if r.batch_id == batch.id and r.class_name == cls and r.item_code == focus_code]
            history_by_batch_class[cls].append(_rows_item_avg_score(rows, focus_code))

    class_history_series = [{'name': cls, 'values': values} for cls, values in history_by_batch_class.items()]

    slots, _slot_names = _fitness_slots(current_rows)
    class_list = []
    for cls in class_names:
        rows = class_groups[cls]
        bmi_rows = [r for r in rows if r.item_code == slots['bmi']]
        lung_rows = [r for r in rows if r.item_code == slots['lung']]
        sprint_rows = [r for r in rows if r.item_code == slots['sprint']]
        class_list.append({
            'class_name': cls,
            'bmi_score': format_score(_rows_item_avg_raw(rows, slots['bmi'])),
            'bmi_point': _rows_item_avg_score(rows, slots['bmi']),
            'bmi_rate': build_rate_text(_rate(bmi_rows)['pass_rate'], _rate(bmi_rows)['excellent_rate'], _rate(bmi_rows)['full_rate']),
            'lung_score': format_score(_rows_item_avg_raw(rows, slots['lung'])),
            'lung_point': _rows_item_avg_score(rows, slots['lung']),
            'lung_rate': build_rate_text(_rate(lung_rows)['pass_rate'], _rate(lung_rows)['excellent_rate'], _rate(lung_rows)['full_rate']),
            'sprint_score': format_score(_rows_item_avg_raw(rows, slots['sprint'])),
            'sprint_point': _rows_item_avg_score(rows, slots['sprint']),
            'sprint_rate': build_rate_text(_rate(sprint_rows)['pass_rate'], _rate(sprint_rows)['excellent_rate'], _rate(sprint_rows)['full_rate'])
        })

    data = {
        'kpi': kpi,
        'class_item_avg': {'classes': class_names, 'series': class_item_avg_series},
        'class_item_rate': {
            'classes': class_names,
            'pass_rate': rate_pass,
            'excellent_rate': rate_excellent,
            'full_rate': rate_full
        },
        'class_item_history': {
            'batches': [b.batch_name for b in history_batches],
            'series': class_history_series
        },
        'class_list': class_list
    }
    return SuccessResponse(data)

@app.get('/entry/template', summary='体测录入模板配置')
async def get_entry_template(auth: Auth = Depends(FullAdminAuth(permissions=['fitness.score.entry']))):
    data = {
        'items': ['BMI', '肺活量', '50米', '坐位体前屈', '跳绳', '跳远', '力量项', '耐力跑'],
        'calc_policy': '仅录入成绩可自动计算分值',
        'conflict_policy': '就低不就高'
    }
    return SuccessResponse(data)


@app.get('/report/config', summary='体测报表配置')
async def get_report_config(auth: Auth = Depends(FullAdminAuth(permissions=['fitness.report.export']))):
    data = {
        'report_types': ['学生报表', '班级报表', '年级报表'],
        'default_fields': ['学生基础信息', '项目成绩', '项目评分成绩', '单项及格/优秀/满分状态', '标准版本号']
    }
    return SuccessResponse(data)


@app.get('/standard/list', summary='体测标准列表')
async def get_standard_list(auth: Auth = Depends(FullAdminAuth(permissions=['fitness.standard.list']))):
    try:
        stage_type = None
        data = await list_standard_with_items(
            auth.db,
            biz_type='fitness',
            stage_type=stage_type
        )
        if data:
            return SuccessResponse(data)
    except Exception:
        # 表未初始化或查询失败时回退到样例数据，避免阻塞前端联调
        pass

    data = [
        {
            'id': 1,
            'name': '重庆市2026体测标准',
            'region': '重庆市',
            'year': 2026,
            'stage': '初中',
            'version': 'FT-2026.1',
            'status': '已发布'
        },
        {
            'id': 2,
            'name': '重庆市2025体测标准',
            'region': '重庆市',
            'year': 2025,
            'stage': '初中',
            'version': 'FT-2025.2',
            'status': '草稿'
        }
    ]
    return SuccessResponse(data)


@app.post('/standard', summary='创建体测标准')
async def create_standard(
        payload: dict = Body(...),
        auth: Auth = Depends(FullAdminAuth(permissions=['fitness.standard.list']))
):
    standard = VadminSportStandard(
        biz_type='fitness',
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


@app.post('/batch', summary='创建体测测试批次')
async def create_batch(
        payload: dict = Body(...),
        auth: Auth = Depends(FullAdminAuth(permissions=['fitness.score.entry']))
):
    if not _in_scope(auth, payload.get('school_name'), payload.get('class_name')):
        return ErrorResponse('无权限操作当前学校/班级数据')
    batch = VadminSportBatch(
        biz_type='fitness',
        batch_name=payload.get('batch_name'),
        standard_id=int(payload.get('standard_id')),
        school_name=payload.get('school_name'),
        grade_name=payload.get('grade_name'),
        class_name=payload.get('class_name'),
        stage_type=payload.get('stage_type', 'mid'),
        start_date=payload.get('start_date'),
        end_date=payload.get('end_date'),
        status=payload.get('status', 'draft'),
        remark=payload.get('remark')
    )
    auth.db.add(batch)
    await auth.db.flush()
    return SuccessResponse({'id': batch.id})


@app.get('/batch/options', summary='体测批次选项')
async def get_batch_options(auth: Auth = Depends(FullAdminAuth(permissions=['fitness.score.entry']))):
    sql = select(VadminSportBatch).where(
        VadminSportBatch.is_delete == false(),
        VadminSportBatch.biz_type == 'fitness'
    ).order_by(VadminSportBatch.id.desc())
    rows = (await auth.db.scalars(sql)).all()
    rows = [r for r in rows if _in_scope(auth, r.school_name, r.class_name)]
    data = [{'label': r.batch_name, 'value': r.id} for r in rows]
    return SuccessResponse(data)


@app.post('/score/upsert', summary='体测成绩录入/更新')
async def upsert_scores(
        payload: dict = Body(...),
        auth: Auth = Depends(FullAdminAuth(permissions=['fitness.score.entry']))
):
    batch_id = int(payload.get('batch_id'))
    batch = (await auth.db.scalars(select(VadminSportBatch).where(
        VadminSportBatch.is_delete == false(),
        VadminSportBatch.biz_type == 'fitness',
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
    for item in scores:
        if not _in_scope(auth, item.get('school_name'), item.get('class_name')):
            continue

        raw_score_parsed = _parse_raw_score(item.get('raw_score'))
        item_rules = item_rule_map.get(item.get('item_code') or '', [])
        selected_rule = _select_rule(item_rules, item.get('gender'))
        calc_result = _calc_by_rule(raw_score_parsed, selected_rule, conflict_policy)

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
            VadminSportScore.biz_type == 'fitness',
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
        else:
            auth.db.add(VadminSportScore(
                biz_type='fitness',
                batch_id=batch_id,
                student_no=item.get('student_no'),
                student_name=item.get('student_name'),
                gender=item.get('gender'),
                mobile=item.get('mobile'),
                school_name=item.get('school_name'),
                grade_name=item.get('grade_name'),
                class_name=item.get('class_name'),
                item_code=item.get('item_code'),
                item_name=item.get('item_name'),
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

