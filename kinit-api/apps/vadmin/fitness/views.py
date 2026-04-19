#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import re
import logging
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
    to_float,
    export_scores_to_excel
)
from apps.vadmin.sport.service.rule_engine import RuleEngine
from apps.vadmin.sport.service.batch_import_service import BatchImportService
from apps.vadmin.sport.service.standard_import_service import StandardImportService
from apps.vadmin.sport.service.standard_service import list_standard_with_items
from apps.vadmin.sport.service.scope_service import match_scope_by_name, is_global_scope
from utils.response import SuccessResponse, ErrorResponse
from utils.excel.write_xlsx import WriteXlsx

app = APIRouter()
logger = logging.getLogger(__name__)

def _serialize(model_obj, schema_class):
    """
    通用序列化工具，确保完全兼容 orjson
    """
    return json.loads(schema_class.model_validate(model_obj).model_dump_json())

def _is_global_scope(auth: Auth) -> bool:
    return is_global_scope(auth)


def _filter_rows_by_scope(auth: Auth, rows: list[dict[str, Any]], keys: list[str]) -> list[dict[str, Any]]:
    if _is_global_scope(auth):
        return rows
    result = []
    for row in rows:
        if match_scope_by_name(auth, row.get('school_name') or row.get('school'), row.get('class_name')):
            result.append(row)
    return result


def _can_access_row(auth: Auth, row: dict[str, Any], keys: list[str]) -> bool:
    return len(_filter_rows_by_scope(auth, [row], keys)) > 0


def _in_scope(auth: Auth, school_name: str | None, class_name: str | None) -> bool:
    return match_scope_by_name(auth, school_name, class_name)


async def _get_self_student_context(db, telephone: str | None, user_id: int | None = None) -> dict[str, Any] | None:
    if (not telephone) and (not user_id):
        return None
    base_sql = (
        select(VadminPefStudent, VadminPefSchool.school_name, VadminPefGrade.grade_name, VadminPefClass.class_name)
        .select_from(VadminPefStudent)
        .join(VadminPefSchool, VadminPefStudent.school_id == VadminPefSchool.id)
        .join(VadminPefGrade, VadminPefStudent.grade_id == VadminPefGrade.id)
        .join(VadminPefClass, VadminPefStudent.class_id == VadminPefClass.id)
        .where(VadminPefStudent.is_delete == false())
        .order_by(VadminPefStudent.update_datetime.desc(), VadminPefStudent.id.desc())
    )

    row = None
    # 优先按 user_id 精确匹配，避免同手机号/历史脏数据匹配错学生
    if user_id:
        row = (await db.execute(base_sql.where(VadminPefStudent.user_id == user_id))).first()
    if (not row) and telephone:
        row = (await db.execute(base_sql.where(VadminPefStudent.phone == telephone))).first()
    if not row:
        logger.warning(
            "[fitness.self] student context not found, telephone=%s, user_id=%s",
            telephone, user_id
        )
        return None
    student, school_name, grade_name, class_name = row
    return {
        'student': student,
        'school_name': school_name,
        'grade_name': grade_name,
        'class_name': class_name
    }


async def _get_self_score_context(db, telephone: str | None) -> dict[str, Any] | None:
    if not telephone:
        return None
    row = (await db.execute(
        select(VadminSportScore)
        .where(
            VadminSportScore.is_delete == false(),
            VadminSportScore.biz_type == 'fitness',
            VadminSportScore.mobile == telephone
        )
        .order_by(VadminSportScore.update_datetime.desc(), VadminSportScore.id.desc())
        .limit(1)
    )).scalars().first()
    if not row:
        logger.warning("[fitness.self] score fallback context not found by mobile, telephone=%s", telephone)
        return None
    return {
        'school_name': row.school_name,
        'grade_name': row.grade_name,
        'class_name': row.class_name,
        'student_no': row.student_no
    }


def _stage_text(stage_type: str | None) -> str:
    stage_map = {
        'primary': '小学',
        'mid': '初中',
        'high': '高中',
        'university': '大学'
    }
    return stage_map.get(stage_type, stage_type or '')

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


def _item_columns(rows: list[VadminSportScore]) -> list[dict[str, str]]:
    seen: set[str] = set()
    columns: list[dict[str, str]] = []
    for row in rows:
        if not row.item_code or row.item_code in seen:
            continue
        seen.add(row.item_code)
        columns.append({
            'item_code': row.item_code,
            'item_name': row.item_name or row.item_code
        })
    return columns


def _item_detail_cells(rows: list[VadminSportScore], columns: list[dict[str, str]], include_rate: bool = False) -> list[dict[str, Any]]:
    item_map = {r.item_code: r for r in rows}
    cells: list[dict[str, Any]] = []
    for col in columns:
        row = item_map.get(col['item_code'])
        rate_text = ''
        if include_rate:
            rate = _rate([r for r in rows if r.item_code == col['item_code']])
            rate_text = build_rate_text(rate['pass_rate'], rate['excellent_rate'], rate['full_rate'])
        cells.append({
            'item_code': col['item_code'],
            'item_name': col['item_name'],
            'raw_score': format_score(to_float(row.raw_score) if row else None),
            'score_value': round2(to_float(row.score_value)) if row else 0.0,
            'rate_text': rate_text
        })
    return cells


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

    return RuleEngine.eval_by_threshold(raw_score, {
        'pass': pass_v,
        'excellent': excellent_v,
        'full': full_v
    })


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
    detail_columns = _item_columns(current_rows)
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
            'sprint_rate': build_rate_text(_rate(sprint_rows)['pass_rate'], _rate(sprint_rows)['excellent_rate'], _rate(sprint_rows)['full_rate']),
            'items': _item_detail_cells(rows, detail_columns, True)
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
        'detail_columns': detail_columns,
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
    if student_no:
        student_no = str(student_no).strip()

    async def _fallback_batches_by_student(
            _school_name: str | None,
            _grade_name: str | None,
            _class_name: str | None
    ) -> list[VadminSportBatch]:
        if not student_no:
            return []
        score_sql = select(VadminSportScore.batch_id).where(
            VadminSportScore.is_delete == false(),
            VadminSportScore.biz_type == 'fitness',
            VadminSportScore.student_no == student_no
        )
        if _school_name:
            score_sql = score_sql.where(VadminSportScore.school_name == _school_name)
        if _grade_name:
            score_sql = score_sql.where(VadminSportScore.grade_name == _grade_name)
        if _class_name:
            score_sql = score_sql.where(VadminSportScore.class_name == _class_name)
        batch_ids = (await auth.db.scalars(score_sql.distinct().order_by(VadminSportScore.batch_id.desc()))).all()
        if not batch_ids:
            return []
        batch_sql = select(VadminSportBatch).where(
            VadminSportBatch.is_delete == false(),
            VadminSportBatch.biz_type == 'fitness',
            VadminSportBatch.id.in_(batch_ids)
        ).order_by(VadminSportBatch.id.desc()).limit(24)
        return (await auth.db.scalars(batch_sql)).all()

    batches = await list_batches(
        auth.db,
        biz_type='fitness',
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
            biz_type='fitness',
            stage_type=None,
            school_name=school_name,
            grade_name=grade_name,
            class_name=class_name,
            limit=24
        )
    # 兼容基础档案与批次字段不一致场景：按学生号回退推导批次
    if not batches and student_no:
        for candidate in [
            (school_name, grade_name, class_name),
            (school_name, grade_name, None),
            (school_name, None, None),
            (None, None, None)
        ]:
            batches = await _fallback_batches_by_student(*candidate)
            if batches:
                break
    batches = [b for b in batches if _in_scope(auth, b.school_name, b.class_name)]
    if not batches:
        logger.info(
            "[fitness.analysis.student] empty: no batches, student_no=%s, school=%s, grade=%s, class=%s, stage_type=%s",
            student_no, school_name, grade_name, class_name, stage_type
        )
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
    # 兼容历史数据：若按组织维度无结果，且已明确 student_no，则放宽组织维度重查
    if not all_rows and student_no:
        all_rows = await list_scores(
            auth.db,
            biz_type='fitness',
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
        logger.info(
            "[fitness.analysis.student] empty: no rows, student_no=%s, school=%s, grade=%s, class=%s, batches=%s",
            student_no, school_name, grade_name, class_name, [b.id for b in batches]
        )
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

    # 多维雷达指标：来源于“最新批次对应标准”的标准项（按 sort 排序）
    standard_item_all = (await auth.db.scalars(
        select(VadminSportStandardItem).where(
            VadminSportStandardItem.is_delete == false(),
            VadminSportStandardItem.standard_id == latest_batch.standard_id
        ).order_by(VadminSportStandardItem.sort.asc(), VadminSportStandardItem.id.asc())
    )).all()
    student_gender = str(latest_first.gender or '').lower()
    standard_item_rows: list[VadminSportStandardItem] = []
    seen_item_codes: set[str] = set()
    for it in standard_item_all:
        g = str(it.gender or 'all').lower()
        if g not in ('all', student_gender):
            continue
        if it.item_code in seen_item_codes:
            continue
        seen_item_codes.add(it.item_code)
        standard_item_rows.append(it)
    radar_item_names = [it.item_name for it in standard_item_rows if it.item_name]
    if not radar_item_names:
        radar_item_names = [item_name_map.get(code, code) for code in item_codes]

    latest_item_point_map: dict[str, float] = {}
    for r in latest_rows:
        latest_item_point_map[r.item_code] = round2(to_float(r.score_value))

    radar_values = []
    radar_max = []
    for it in standard_item_rows:
        val = latest_item_point_map.get(it.item_code, 0.0)
        radar_values.append(val)
        max_v = round2(to_float(it.max_score))
        radar_max.append(max_v if max_v > 0 else 100.0)

    if not standard_item_rows:
        # 回退：基于当前已录入项目
        for code in item_codes:
            radar_values.append(latest_item_point_map.get(code, 0.0))
            radar_max.append(100.0)

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

    detail_items = [
        {
            'item_code': it.item_code,
            'item_name': it.item_name
        }
        for it in standard_item_rows
    ]
    if not detail_items:
        detail_items = [
            {
                'item_code': code,
                'item_name': item_name_map.get(code, code)
            }
            for code in item_codes
        ]

    detail_list = []
    for batch in sorted(sorted_batches, key=lambda b: b.id, reverse=True):
        b_rows = by_batch.get(batch.id, [])
        item_map = {r.item_code: r for r in b_rows}
        comment = next((r.teacher_comment for r in b_rows if r.teacher_comment), '')
        detail_row = {
            'batch_name': batch.batch_name,
            'teacher_comment': comment
        }
        detail_item_values = []
        for item in detail_items:
            row = item_map.get(item['item_code'])
            detail_item_values.append({
                'item_code': item['item_code'],
                'item_name': item['item_name'],
                'raw_score': format_score(to_float(row.raw_score) if row else None),
                'score_value': round2(to_float(row.score_value)) if row else 0.0
            })
        detail_row['items'] = detail_item_values
        detail_list.append(detail_row)

    return SuccessResponse({
        'profile': profile,
        'stats': stats,
        'multi_dim_radar': {
            'items': radar_item_names,
            'values': radar_values,
            'max': radar_max
        },
        'item_score_trend': {'batches': [b.batch_name for b in sorted_batches], 'series': item_score_series},
        'item_state_trend': item_state,
        'detail_columns': detail_items,
        'detail_list': detail_list
    })

@app.get('/analysis/student/self', summary='体测学生本人视图')
async def get_student_analysis_self(
        stage_type: str | None = Query(None),
        school_name: str | None = Query(None),
        grade_name: str | None = Query(None),
        class_name: str | None = Query(None),
        student_no: str | None = Query(None),
        auth: Auth = Depends(AllUserAuth())
):
    logger.info(
        "[fitness.self] enter, user_id=%s, telephone=%s, is_staff=%s, query_student_no=%s",
        getattr(auth.user, 'id', None), getattr(auth.user, 'telephone', None),
        getattr(auth.user, 'is_staff', None), student_no
    )
    if getattr(auth.user, 'is_staff', False):
        if not student_no:
            return SuccessResponse(_empty_student())
        return await get_student_analysis(
            stage_type=stage_type,
            school_name=school_name,
            grade_name=grade_name,
            class_name=class_name,
            student_no=student_no,
            student_keyword=None,
            student_id=None,
            school_id=None,
            grade_id=None,
            class_id=None,
            auth=auth
        )

    telephone = getattr(auth.user, 'telephone', None)
    ctx = await _get_self_student_context(
        auth.db,
        telephone,
        getattr(auth.user, 'id', None)
    )
    resp = None
    if ctx:
        logger.info(
            "[fitness.self] student context hit: student_no=%s, school=%s, grade=%s, class=%s",
            ctx['student'].student_no, ctx['school_name'], ctx['grade_name'], ctx['class_name']
        )
        resp = await get_student_analysis(
            stage_type=None,
            school_name=None,
            grade_name=None,
            class_name=None,
            student_no=ctx['student'].student_no,
            student_keyword=None,
            student_id=None,
            school_id=None,
            grade_id=None,
            class_id=None,
            auth=auth
        )

    # 档案匹配失败或该档案暂无成绩时，按手机号从成绩表反查最近一条成绩进行兜底
    payload = getattr(resp, 'data', {}).get('data') if resp else None
    if not isinstance(payload, dict) or not payload.get('profile'):
        score_ctx = await _get_self_score_context(auth.db, telephone)
        if score_ctx:
            logger.info(
                "[fitness.self] score fallback hit: student_no=%s, school=%s, grade=%s, class=%s",
                score_ctx['student_no'], score_ctx['school_name'], score_ctx['grade_name'], score_ctx['class_name']
            )
            resp = await get_student_analysis(
                stage_type=None,
                school_name=None,
                grade_name=None,
                class_name=None,
                student_no=score_ctx['student_no'],
                student_keyword=None,
                student_id=None,
                school_id=None,
                grade_id=None,
                class_id=None,
                auth=auth
            )

    if not resp:
        logger.warning("[fitness.self] final empty: no context and no fallback")
        return SuccessResponse(_empty_student())
    payload = getattr(resp, 'data', {}).get('data')
    if ctx and isinstance(payload, dict) and isinstance(payload.get('profile'), dict):
        payload['profile']['student_name'] = ctx['student'].name
        payload['profile']['gender'] = ctx['student'].gender
        payload['profile']['mobile'] = ctx['student'].phone
        payload['profile']['school'] = ctx['school_name']
        payload['profile']['grade'] = ctx['grade_name']
        payload['profile']['class_name'] = ctx['class_name']
        payload['profile']['student_no'] = ctx['student'].student_no
    return resp


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

    detail_columns = _item_columns(current_rows)
    rank_data = []
    slots, _slot_names = _fitness_slots(current_rows)
    for student_no, s_rows in by_student.items():
        item_map = {r.item_code: r for r in s_rows}
        avg_score = avg([to_float(r.score_value) for r in s_rows])
        first = s_rows[0]
        comment = next((r.teacher_comment for r in s_rows if r.teacher_comment), '')
        rank_data.append({
            'student_name': first.student_name,
            'gender': first.gender,
            'student_no': student_no,
            'teacher_comment': comment,
            'avg_score': avg_score,
            'items': _item_detail_cells(s_rows, detail_columns, False)
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
        'detail_columns': detail_columns,
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
    detail_columns = _item_columns(current_rows)
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
            'sprint_rate': build_rate_text(_rate(sprint_rows)['pass_rate'], _rate(sprint_rows)['excellent_rate'], _rate(sprint_rows)['full_rate']),
            'items': _item_detail_cells(rows, detail_columns, True)
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
        'detail_columns': detail_columns,
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


@app.get('/batch/options', summary='体测批次选项')
async def get_batch_options(
        stage_type: str | None = Query(None),
        auth: Auth = Depends(FullAdminAuth(permissions=['fitness.score.entry']))
):
    sql = select(VadminSportBatch).where(
        VadminSportBatch.is_delete == false(),
        VadminSportBatch.biz_type == 'fitness'
    )
    if stage_type:
        sql = sql.where(VadminSportBatch.stage_type == stage_type)
    sql = sql.order_by(VadminSportBatch.id.desc())
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
            row.mobile = mobile
            row.item_name = item_name
        else:
            auth.db.add(VadminSportScore(
                biz_type='fitness',
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


@app.get('/batch/list', summary='体测批次列表')
async def get_batch_list(
        page: int = Query(1),
        limit: int = Query(10),
        batch_name: str | None = Query(None),
        auth: Auth = Depends(FullAdminAuth(permissions=['fitness.score.entry']))
):
    sql = select(VadminSportBatch).where(
        VadminSportBatch.is_delete == false(),
        VadminSportBatch.biz_type == 'fitness'
    )
    if batch_name:
        sql = sql.where(VadminSportBatch.batch_name.like(f"%{batch_name}%"))
    
    sql = sql.order_by(VadminSportBatch.id.desc())
    
    rows = (await auth.db.scalars(sql)).all()
    rows = [r for r in rows if _in_scope(auth, r.school_name, r.class_name)]

    standard_ids = list({r.standard_id for r in rows if getattr(r, 'standard_id', None)})
    standard_map: dict[int, VadminSportStandard] = {}
    if standard_ids:
        standards = (await auth.db.scalars(select(VadminSportStandard).where(
            VadminSportStandard.is_delete == false(),
            VadminSportStandard.id.in_(standard_ids)
        ))).all()
        standard_map = {s.id: s for s in standards}
    
    total = len(rows)
    start = (page - 1) * limit
    end = start + limit
    paged_rows = rows[start:end]
    
    items = []
    for r in paged_rows:
        item = json.loads(schemas.BatchOut.model_validate(r).model_dump_json())
        standard = standard_map.get(r.standard_id)
        if standard:
            item['standard_name'] = standard.name
            item['standard_version'] = standard.version
        items.append(item)

    return SuccessResponse({
        'total': total,
        'items': items
    })


@app.put('/batch/{id}', summary='更新体测批次')
async def update_batch(
        id: int,
        payload: dict = Body(...),
        auth: Auth = Depends(FullAdminAuth(permissions=['fitness.score.entry']))
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


@app.delete('/batch/{id}', summary='删除体测批次')
async def delete_batch(
        id: int,
        auth: Auth = Depends(FullAdminAuth(permissions=['fitness.score.entry']))
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
        auth: Auth = Depends(FullAdminAuth(permissions=['fitness.analysis.student']))
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
    if not _is_global_scope(auth):
        if auth.class_ids:
            class_scope = set(auth.class_ids)
            rows = [r for r in rows if r.class_id in class_scope]
        elif auth.school_ids:
            school_scope = set(auth.school_ids)
            rows = [r for r in rows if r.school_id in school_scope]
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


@app.get('/report/export', summary='体测报表导出')
async def export_report(
        batch_id: int | None = Query(None),
        school_name: str | None = Query(None),
        grade_name: str | None = Query(None),
        class_name: str | None = Query(None),
        auth: Auth = Depends(FullAdminAuth(permissions=['fitness.report.export']))
):
    if not batch_id:
        return ErrorResponse('请选择批次')
    
    rows = await list_scores(
        auth.db,
        biz_type='fitness',
        batch_ids=[batch_id],
        school_name=school_name,
        grade_name=grade_name,
        class_name=class_name
    )
    rows = [r for r in rows if _in_scope(auth, r.school_name, r.class_name)]
    
    if not rows:
        return ErrorResponse('暂无数据可导出')
    
    filename = f"体测成绩报表_{batch_id}.xlsx"
    url = export_scores_to_excel(rows, filename)
    
    return SuccessResponse({'url': url})


@app.get('/score/template', summary='下载体测成绩导入模板')
async def download_score_template(
        auth: Auth = Depends(FullAdminAuth(permissions=['fitness.score.entry']))
):
    headers = ["学号", "姓名", "性别", "学校", "年级", "班级", "项目编码", "项目名称", "成绩"]
    writer = WriteXlsx()
    filename = "体测成绩导入模板.xlsx"
    writer.create_excel(file_path=filename, save_static=True)
    header_dicts = [{"label": h} for h in headers]
    writer.generate_template(header_dicts)
    writer.close()
    return SuccessResponse({'url': writer.get_file_url()})


@app.post('/standard/import', summary='体测标准 Excel 导入解析')
async def import_standard(
        file: UploadFile = File(...),
        auth: Auth = Depends(FullAdminAuth(permissions=['fitness.standard.list']))
):
    content = await file.read()
    items = StandardImportService.parse_standard_excel(content)
    return SuccessResponse(items)


@app.post('/standard/confirm', summary='体测标准人工确认保存')
async def confirm_standard(
        payload: dict = Body(...),
        auth: Auth = Depends(FullAdminAuth(permissions=['fitness.standard.list']))
):
    payload['source_type'] = 'excel'
    payload['status'] = 'draft'
    return await create_standard(payload, auth)


@app.post('/score/import', summary='体测成绩 Excel 导入解析')
async def import_scores(
        file: UploadFile = File(...),
        auth: Auth = Depends(FullAdminAuth(permissions=['fitness.score.entry']))
):
    content = await file.read()
    scores = BatchImportService.parse_score_excel(content)
    return SuccessResponse(scores)


@app.post('/score/confirm', summary='体测成绩导入人工确认保存')
async def confirm_scores(
        payload: dict = Body(...),
        auth: Auth = Depends(FullAdminAuth(permissions=['fitness.score.entry']))
):
    return await upsert_scores(payload, auth)


@app.get('/score/batch/students', summary='按项目获取批次学生成绩')
async def get_batch_item_scores(
        batch_id: int = Query(...),
        item_code: str = Query(...),
        auth: Auth = Depends(FullAdminAuth(permissions=['fitness.score.entry']))
):
    sql = select(VadminSportScore).where(
        VadminSportScore.batch_id == batch_id,
        VadminSportScore.item_code == item_code,
        VadminSportScore.is_delete == false()
    )
    rows = (await auth.db.scalars(sql)).all()
    # 使用 model_dump_json() 彻底解决 orjson 兼容性问题
    return SuccessResponse([json.loads(schemas.ScoreOut.model_validate(r).model_dump_json()) for r in rows])
