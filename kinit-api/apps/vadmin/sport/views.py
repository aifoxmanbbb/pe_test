#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
from fastapi import APIRouter, Body, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import ValidationError
from sqlalchemy import select, false, true, func, or_
from xlsxwriter.utility import xl_col_to_name
from apps.vadmin.auth import models as auth_models
from apps.vadmin.auth.models import VadminMenu, VadminRole, VadminUser
from apps.vadmin.auth.utils.current import FullAdminAuth, OpenAuth, AllUserAuth
from apps.vadmin.auth.utils.validation.auth import Auth
from application import settings
from typing import Any
from core.validator import vali_id_card
from utils.excel.import_manage import ImportManage
from utils.excel.write_xlsx import WriteXlsx
from utils.response import SuccessResponse, ErrorResponse
from .models import (
    VadminPefSchool,
    VadminPefGrade,
    VadminPefClass,
    VadminPefStudent,
    VadminSportStandard,
    VadminSportStandardItem,
    VadminSportBatch,
    VadminSportScore,
    vadmin_pef_school_leaders,
    vadmin_pef_class_coaches
)
from .service.analytics_service import round2, to_float
from .service.batch_import_service import BatchImportService
from .service.rule_engine import RuleEngine
from .service.scope_service import (
    ROLE_SCHOOL_LEADER,
    ROLE_TEACHER_COACH,
    is_global_scope
)
from . import schemas
import traceback
import json

app = APIRouter()

STAGE_SET = {'primary', 'mid', 'high', 'university'}
STUDENT_ROLE_KEY = 'student_parent'
STUDENT_ROLE_NAME = '学生'
STUDENT_ROOT_PERM = 'sport.student'
STUDENT_SCORE_PERM = 'sport.student.scores'
STUDENT_ENTRY_PERM = 'sport.student.entry'
SCHOOL_PERM = 'sport.foundation.school'
GRADE_PERM = 'sport.foundation.grade'
CLASS_PERM = 'sport.foundation.class'
STUDENT_PERM = 'sport.foundation.student'


def _normalize_stage_types(value) -> str:
    if value is None:
        return ''
    if isinstance(value, str):
        tokens = [s.strip() for s in value.split(',') if s.strip()]
    elif isinstance(value, (list, tuple, set)):
        tokens = [str(s).strip() for s in value if str(s).strip()]
    else:
        tokens = [str(value).strip()]
    normalized: list[str] = []
    for token in tokens:
        if token in STAGE_SET and token not in normalized:
            normalized.append(token)
    return ','.join(normalized)


def _serialize(model_obj, schema_class, school_name=None, grade_name=None, class_name=None):
    data = json.loads(schema_class.model_validate(model_obj).model_dump_json())
    if 'stage_types' in data:
        data['stage_types'] = _normalize_stage_types(data.get('stage_types'))
    if school_name: data['school_name'] = school_name
    if grade_name: data['grade_name'] = grade_name
    if class_name: data['class_name'] = class_name
    return data


def _default_student_password(id_card: str) -> str:
    return str(id_card or '')[-8:] if settings.DEFAULT_PASSWORD == "0" else settings.DEFAULT_PASSWORD


def _normalize_auth_gender(value: str | int | None) -> str:
    text = str(value or '').strip().lower()
    if text in {'1', 'male', 'm', '男'}:
        return '1'
    if text in {'0', 'female', 'f', '女', '2'}:
        return '0'
    return '0'


def _display_gender(value: str | None) -> str:
    text = str(value or '').strip().lower()
    if text in {'male', 'm', '1', '男', 'ç”·'}:
        return '男'
    if text in {'female', 'f', '0', '2', '女', 'å¥³'}:
        return '女'
    return '通用'


def _format_rule_range(value) -> str:
    if value is None:
        return ''
    if isinstance(value, (int, float)):
        return str(value)
    return str(value).strip()


def _format_rule_score(score, max_score) -> str:
    score_value = to_float(score, default=0.0)
    max_value = to_float(max_score, default=0.0)
    if max_value > 0 and max_value < score_value <= 100:
        return f"{round2((score_value / 100.0) * max_value):g}"
    return str(score if score not in (None, '') else 0)


def _build_standard_item_help_lines(items: list[VadminSportStandardItem]) -> list[str]:
    lines: list[str] = []
    for item in items:
        prefix = _display_gender(item.gender)
        mode = str(item.calc_mode or 'segment').strip().lower()
        if mode == 'segment':
            segments = item.segment_json
            if isinstance(segments, str):
                try:
                    segments = json.loads(segments)
                except Exception:
                    segments = None
            if isinstance(segments, list):
                for seg in segments:
                    if not isinstance(seg, dict):
                        continue
                    if 'grade' in seg and isinstance(seg.get('rules'), list):
                        grade = str(seg.get('grade') or '').strip()
                        for rule in seg.get('rules') or []:
                            if not isinstance(rule, dict):
                                continue
                            grade_prefix = f'/{grade}' if grade else ''
                            lines.append(
                                f"{prefix}{grade_prefix}：{_format_rule_range(rule.get('range'))} -> {_format_rule_score(rule.get('score'), item.max_score)}分"
                            )
                    else:
                        lines.append(
                            f"{prefix}：{_format_rule_range(seg.get('range'))} -> {_format_rule_score(seg.get('score'), item.max_score)}分"
                        )
            continue

        threshold_parts: list[str] = []
        if item.pass_threshold not in (None, ''):
            threshold_parts.append(f"及格 {item.pass_threshold}")
        if item.excellent_threshold not in (None, ''):
            threshold_parts.append(f"优秀 {item.excellent_threshold}")
        if item.full_threshold not in (None, ''):
            threshold_parts.append(f"满分 {item.full_threshold}")
        if threshold_parts:
            suffix = '，'.join(threshold_parts)
            if item.max_score not in (None, '') and float(item.max_score or 0) > 0:
                suffix = f"{suffix}，该项满分 {item.max_score}分"
            lines.append(f"{prefix}：{suffix}")
    return lines


def _has_role(auth: Auth, role_key: str) -> bool:
    return role_key in (auth.role_keys or [])


def _can_manage_school(auth: Auth) -> bool:
    return is_global_scope(auth)


def _can_manage_grade(auth: Auth) -> bool:
    return is_global_scope(auth) or _has_role(auth, ROLE_SCHOOL_LEADER)


def _can_manage_class(auth: Auth) -> bool:
    return is_global_scope(auth) or _has_role(auth, ROLE_SCHOOL_LEADER)


def _can_manage_student(auth: Auth) -> bool:
    return is_global_scope(auth) or _has_role(auth, ROLE_SCHOOL_LEADER) or _has_role(auth, ROLE_TEACHER_COACH)


def _school_id_in_scope(auth: Auth, school_id: int | None) -> bool:
    if school_id is None:
        return False
    if is_global_scope(auth):
        return True
    return school_id in set(auth.school_ids or [])


def _class_id_in_scope(auth: Auth, class_id: int | None) -> bool:
    if class_id is None:
        return False
    if is_global_scope(auth):
        return True
    return class_id in set(auth.class_ids or [])


def _grade_visible(auth: Auth, school_id: int) -> bool:
    return _school_id_in_scope(auth, school_id)


def _class_visible(auth: Auth, school_id: int, class_id: int) -> bool:
    if is_global_scope(auth):
        return True
    if _has_role(auth, ROLE_TEACHER_COACH):
        return _class_id_in_scope(auth, class_id)
    return _school_id_in_scope(auth, school_id)


def _student_visible(auth: Auth, school_id: int, class_id: int) -> bool:
    return _class_visible(auth, school_id, class_id)


async def _get_school_leader_map(db, school_ids: list[int]) -> tuple[dict[int, list[int]], dict[int, list[str]]]:
    if not school_ids:
        return {}, {}
    rows = (await db.execute(
        select(vadmin_pef_school_leaders.c.school_id, VadminUser.id, VadminUser.name)
        .select_from(vadmin_pef_school_leaders)
        .join(VadminUser, VadminUser.id == vadmin_pef_school_leaders.c.user_id)
        .where(
            vadmin_pef_school_leaders.c.school_id.in_(school_ids),
            VadminUser.is_delete == false()
        )
        .order_by(vadmin_pef_school_leaders.c.school_id.asc(), VadminUser.id.asc())
    )).all()
    id_map: dict[int, list[int]] = {}
    name_map: dict[int, list[str]] = {}
    for school_id, user_id, user_name in rows:
        id_map.setdefault(int(school_id), []).append(int(user_id))
        if user_name:
            name_map.setdefault(int(school_id), []).append(str(user_name))
    return id_map, name_map


async def _get_class_coach_map(db, class_ids: list[int]) -> tuple[dict[int, list[int]], dict[int, list[str]]]:
    if not class_ids:
        return {}, {}
    rows = (await db.execute(
        select(vadmin_pef_class_coaches.c.class_id, VadminUser.id, VadminUser.name)
        .select_from(vadmin_pef_class_coaches)
        .join(VadminUser, VadminUser.id == vadmin_pef_class_coaches.c.user_id)
        .where(
            vadmin_pef_class_coaches.c.class_id.in_(class_ids),
            VadminUser.is_delete == false()
        )
        .order_by(vadmin_pef_class_coaches.c.class_id.asc(), VadminUser.id.asc())
    )).all()
    id_map: dict[int, list[int]] = {}
    name_map: dict[int, list[str]] = {}
    for class_id, user_id, user_name in rows:
        id_map.setdefault(int(class_id), []).append(int(user_id))
        if user_name:
            name_map.setdefault(int(class_id), []).append(str(user_name))
    return id_map, name_map


async def _sync_school_leaders(db, school_id: int, leader_user_ids: list[int] | None):
    target_ids = sorted({int(user_id) for user_id in (leader_user_ids or []) if user_id})
    await db.execute(vadmin_pef_school_leaders.delete().where(
        vadmin_pef_school_leaders.c.school_id == school_id
    ))
    if target_ids:
        await db.execute(vadmin_pef_school_leaders.insert(), [
            {'school_id': school_id, 'user_id': user_id} for user_id in target_ids
        ])


async def _sync_class_coaches(db, class_id: int, coach_user_ids: list[int] | None):
    target_ids = sorted({int(user_id) for user_id in (coach_user_ids or []) if user_id})
    await db.execute(vadmin_pef_class_coaches.delete().where(
        vadmin_pef_class_coaches.c.class_id == class_id
    ))
    if target_ids:
        await db.execute(vadmin_pef_class_coaches.insert(), [
            {'class_id': class_id, 'user_id': user_id} for user_id in target_ids
        ])


async def _load_school_or_none(db, school_id: int | None) -> VadminPefSchool | None:
    if not school_id:
        return None
    return await db.scalar(select(VadminPefSchool).where(
        VadminPefSchool.id == school_id,
        VadminPefSchool.is_delete == false()
    ))


async def _load_grade_or_none(db, grade_id: int | None) -> VadminPefGrade | None:
    if not grade_id:
        return None
    return await db.scalar(select(VadminPefGrade).where(
        VadminPefGrade.id == grade_id,
        VadminPefGrade.is_delete == false()
    ))


async def _load_class_or_none(db, class_id: int | None) -> VadminPefClass | None:
    if not class_id:
        return None
    return await db.scalar(select(VadminPefClass).where(
        VadminPefClass.id == class_id,
        VadminPefClass.is_delete == false()
    ))


async def _validate_leader_users(db, leader_user_ids: list[int]) -> bool:
    if not leader_user_ids:
        return True
    role_rows = (await db.execute(
        select(VadminUser.id)
        .select_from(VadminUser)
        .join(auth_models.vadmin_auth_user_roles, auth_models.vadmin_auth_user_roles.c.user_id == VadminUser.id)
        .join(VadminRole, VadminRole.id == auth_models.vadmin_auth_user_roles.c.role_id)
        .where(
            VadminUser.is_delete == false(),
            VadminUser.is_staff == true(),
            VadminRole.role_key == ROLE_SCHOOL_LEADER,
            VadminUser.id.in_(leader_user_ids)
        )
    )).all()
    return len({int(row.id) for row in role_rows}) == len(set(leader_user_ids))


async def _validate_coach_users(db, coach_user_ids: list[int]) -> bool:
    if not coach_user_ids:
        return True
    role_rows = (await db.execute(
        select(VadminUser.id)
        .select_from(VadminUser)
        .join(auth_models.vadmin_auth_user_roles, auth_models.vadmin_auth_user_roles.c.user_id == VadminUser.id)
        .join(VadminRole, VadminRole.id == auth_models.vadmin_auth_user_roles.c.role_id)
        .where(
            VadminUser.is_delete == false(),
            VadminUser.is_staff == true(),
            VadminRole.role_key == ROLE_TEACHER_COACH,
            VadminUser.id.in_(coach_user_ids)
        )
    )).all()
    return len({int(row.id) for row in role_rows}) == len(set(coach_user_ids))


async def _ensure_student_menu_role(db):
    root_menu = await db.scalar(select(VadminMenu).where(
        VadminMenu.perms == STUDENT_ROOT_PERM,
        VadminMenu.is_delete == false()
    ))
    if not root_menu:
        root_menu = VadminMenu(
            title='我的体育',
            icon='ant-design:user-outlined',
            redirect='/sport/self-entry',
            component='#',
            path='/sport',
            disabled=False,
            hidden=False,
            order=12,
            menu_type='0',
            parent_id=None,
            perms=STUDENT_ROOT_PERM,
            noCache=False,
            breadcrumb=True,
            affix=False,
            noTagsView=False,
            canTo=False,
            alwaysShow=True
        )
        db.add(root_menu)
        await db.flush()
    root_menu.title = '我的体育'
    root_menu.icon = 'ant-design:user-outlined'
    root_menu.redirect = '/sport/self-entry'
    root_menu.component = '#'
    root_menu.path = '/sport'
    root_menu.disabled = False
    root_menu.hidden = False
    root_menu.order = 12
    root_menu.menu_type = '0'
    root_menu.parent_id = None
    root_menu.perms = STUDENT_ROOT_PERM
    root_menu.noCache = False
    root_menu.breadcrumb = True
    root_menu.affix = False
    root_menu.noTagsView = False
    root_menu.canTo = False
    root_menu.alwaysShow = True

    score_menu = await db.scalar(select(VadminMenu).where(
        VadminMenu.perms == STUDENT_ENTRY_PERM,
        VadminMenu.is_delete == false()
    ))
    if not score_menu:
        score_menu = VadminMenu(
            title='成绩录入',
            icon=None,
            redirect=None,
            component='views/Vadmin/Sport/Student/SelfEntry',
            path='self-entry',
            disabled=False,
            hidden=False,
            order=1,
            menu_type='1',
            parent_id=root_menu.id,
            perms=STUDENT_ENTRY_PERM,
            noCache=False,
            breadcrumb=True,
            affix=False,
            noTagsView=False,
            canTo=False,
            alwaysShow=False
        )
        db.add(score_menu)
        await db.flush()
    score_menu.title = '成绩录入'
    score_menu.icon = None
    score_menu.redirect = None
    score_menu.component = 'views/Vadmin/Sport/Student/SelfEntry'
    score_menu.path = 'self-entry'
    score_menu.disabled = False
    score_menu.hidden = False
    score_menu.order = 1
    score_menu.menu_type = '1'
    score_menu.parent_id = root_menu.id
    score_menu.perms = STUDENT_ENTRY_PERM
    score_menu.noCache = False
    score_menu.breadcrumb = True
    score_menu.affix = False
    score_menu.noTagsView = False
    score_menu.canTo = False
    score_menu.alwaysShow = False

    role = await db.scalar(select(VadminRole).where(
        VadminRole.role_key == STUDENT_ROLE_KEY,
        VadminRole.is_delete == false()
    ))
    if not role:
        role = VadminRole(
            name=STUDENT_ROLE_NAME,
            role_key=STUDENT_ROLE_KEY,
            data_range=0,
            disabled=False,
            order=999,
            desc='学生/家长自助账号，仅可录入本人体育成绩',
            is_admin=False
        )
        db.add(role)
        await db.flush()
    else:
        role.disabled = False
    role.name = STUDENT_ROLE_NAME
    role.desc = '学生/家长自助账号，仅可录入本人体育成绩'

    target_menu_ids = {root_menu.id, score_menu.id}
    current_menu_ids = set((await db.scalars(select(auth_models.vadmin_auth_role_menus.c.menu_id).where(
        auth_models.vadmin_auth_role_menus.c.role_id == role.id
    ))).all())
    if current_menu_ids != target_menu_ids:
        await db.execute(auth_models.vadmin_auth_role_menus.delete().where(
            auth_models.vadmin_auth_role_menus.c.role_id == role.id
        ))
        await db.execute(auth_models.vadmin_auth_role_menus.insert(), [
            {'role_id': role.id, 'menu_id': root_menu.id},
            {'role_id': role.id, 'menu_id': score_menu.id}
        ])
    return role


async def _sync_student_login_user(
    db,
    student: VadminPefStudent | None,
    data: schemas.StudentIn | schemas.StudentUpdate
):
    phone = str(data.phone or '').strip()
    if phone:
        duplicate_student = await db.scalar(select(VadminPefStudent).where(
            VadminPefStudent.phone == phone,
            VadminPefStudent.is_delete == false(),
            VadminPefStudent.id != (student.id if student else 0)
        ))
        if duplicate_student:
            return None, '该手机号已绑定其他学生'

    duplicate_id_card = await db.scalar(select(VadminPefStudent).where(
        VadminPefStudent.id_card == data.id_card,
        VadminPefStudent.is_delete == false(),
        VadminPefStudent.id != (student.id if student else 0)
    ))
    if duplicate_id_card:
        return None, '该身份证号已绑定其他学生'

    role = await _ensure_student_menu_role(db)

    current_user = None
    if student and student.user_id:
        current_user = await db.scalar(select(VadminUser).where(
            VadminUser.id == student.user_id,
            VadminUser.is_delete == false()
        ))

    user_by_phone = None
    if phone:
        user_by_phone = await db.scalar(select(VadminUser).where(
            VadminUser.telephone == phone,
            VadminUser.is_delete == false()
        ))

    if user_by_phone and current_user and user_by_phone.id != current_user.id:
        return None, '该手机号已被其他系统账号占用'

    if user_by_phone and user_by_phone.is_staff and (not current_user or user_by_phone.id != current_user.id):
        return None, '该手机号已被其他系统账号占用'

    user = current_user
    id_card_changed = bool(user and student and student.id_card != data.id_card)

    if not user and user_by_phone:
        other_student = await db.scalar(select(VadminPefStudent).where(
            VadminPefStudent.user_id == user_by_phone.id,
            VadminPefStudent.is_delete == false(),
            VadminPefStudent.id != (student.id if student else 0)
        ))
        if other_student:
            return None, '该手机号已绑定其他学生'
        user = user_by_phone

    if not user:
        user = VadminUser(
            avatar=settings.DEFAULT_AVATAR,
            telephone=phone,
            name=data.name,
            nickname=None,
            password=VadminUser.get_password_hash(_default_student_password(data.id_card)),
            gender=_normalize_auth_gender(data.gender),
            is_active=data.is_active,
            is_reset_password=False,
            is_staff=False
        )
        db.add(user)
        await db.flush()

    user.telephone = phone
    user.name = data.name
    user.gender = _normalize_auth_gender(data.gender)
    user.is_active = data.is_active
    user.is_staff = False

    if id_card_changed:
        user.password = VadminUser.get_password_hash(_default_student_password(data.id_card))
        user.is_reset_password = False

    await db.execute(auth_models.vadmin_auth_user_roles.delete().where(
        auth_models.vadmin_auth_user_roles.c.user_id == user.id
    ))
    await db.execute(auth_models.vadmin_auth_user_roles.insert().values(
        user_id=user.id,
        role_id=role.id
    ))
    return user, None


async def _sync_student_score_identity(db, old_student_no: str | None, student: schemas.StudentIn | schemas.StudentUpdate):
    new_student_no = str(student.student_no or '').strip()
    old_student_no = str(old_student_no or '').strip()
    if not old_student_no or not new_student_no or old_student_no == new_student_no:
        return
    rows = (await db.scalars(select(VadminSportScore).where(
        VadminSportScore.student_no == old_student_no,
        VadminSportScore.is_delete == false()
    ))).all()
    for row in rows:
        row.student_no = new_student_no
        row.student_name = student.name
        row.gender = student.gender
        row.mobile = student.phone


def _normalize_entry_gender(value: str | None) -> str:
    text = str(value or '').strip().lower()
    if text in {'male', 'm', '1', '男'}:
        return 'male'
    if text in {'female', 'f', '0', '2', '女'}:
        return 'female'
    return 'all'


def _scope_value_unlimited(value: str | None) -> bool:
    return str(value or '').strip().lower() in {'', '*', 'all', '全部', '不限', '不区分', '全校', '全年级', '全部班级'}


def _batch_matches_student(batch: VadminSportBatch, school_name: str, grade_name: str, class_name: str) -> bool:
    return (
        (_scope_value_unlimited(batch.school_name) or batch.school_name == school_name)
        and (_scope_value_unlimited(batch.grade_name) or batch.grade_name == grade_name)
        and (_scope_value_unlimited(batch.class_name) or batch.class_name == class_name)
    )


def _item_matches_student_gender(item, gender: str | None) -> bool:
    item_gender = _normalize_entry_gender(getattr(item, 'gender', None))
    student_gender = _normalize_entry_gender(gender)
    return item_gender in {student_gender, 'all'}


def _build_entry_item_options(items: list, gender: str | None) -> list[dict]:
    grouped: dict[str, list] = {}
    for item in items:
        if not _item_matches_student_gender(item, gender):
            continue
        grouped.setdefault(item.item_code, []).append(item)

    result: list[dict] = []
    for item_code, code_items in grouped.items():
        first = code_items[0]
        help_lines = _build_standard_item_help_lines(code_items)
        if not help_lines and item_code in {'height', 'weight'}:
            help_lines = [f"{first.item_name}仅记录原始测量值，不向学生展示得分。"]
        result.append({
            "label": first.item_name,
            "value": item_code,
            "item_name": first.item_name,
            "help_lines": help_lines,
            "calc_mode": getattr(first, 'calc_mode', None)
        })
    return result


async def _get_self_student_context(db, user: VadminUser | None) -> dict | None:
    if not user:
        return None
    base_sql = (
        select(VadminPefStudent, VadminPefSchool.school_name, VadminPefGrade.grade_name, VadminPefClass.class_name)
        .select_from(VadminPefStudent)
        .join(VadminPefSchool, VadminPefStudent.school_id == VadminPefSchool.id)
        .join(VadminPefGrade, VadminPefStudent.grade_id == VadminPefGrade.id)
        .join(VadminPefClass, VadminPefStudent.class_id == VadminPefClass.id)
        .where(
            VadminPefStudent.is_delete == false(),
            VadminPefStudent.is_active == true(),
            VadminPefSchool.is_delete == false(),
            VadminPefGrade.is_delete == false(),
            VadminPefClass.is_delete == false()
        )
        .order_by(VadminPefStudent.update_datetime.desc(), VadminPefStudent.id.desc())
    )
    row = None
    if user.id:
        row = (await db.execute(base_sql.where(VadminPefStudent.user_id == user.id))).first()
    if not row and user.telephone:
        row = (await db.execute(base_sql.where(VadminPefStudent.phone == user.telephone))).first()
    if not row:
        return None
    student, school_name, grade_name, class_name = row
    return {
        "student": student,
        "school_name": school_name,
        "grade_name": grade_name,
        "class_name": class_name
    }


def _parse_entry_raw_score(raw, item_code: str | None = None) -> float | None:
    parsed = RuleEngine.parse_time_to_seconds(raw)
    if parsed is None:
        return None
    code = str(item_code or '').lower()
    if parsed < 0 and code != 'sit':
        return None
    if code in {'jump', 'ball'} and parsed > 30:
        return round2(parsed / 100.0)
    return parsed


def _normalize_entry_item_code(item_code: Any) -> str:
    return str(item_code or '').strip().lower()


def _calc_bmi(height: float | None, weight: float | None) -> float | None:
    if height is None or weight is None:
        return None
    if height <= 0:
        return None
    if height > 10:
        height = height / 100
    if height <= 0:
        return None
    return round2(weight / (height * height))


def _select_entry_rule(item_rules: list, gender: str | None):
    if not item_rules:
        return None
    target = _normalize_entry_gender(gender)
    for rule in item_rules:
        if _normalize_entry_gender(getattr(rule, 'gender', None)) == target:
            return rule
    for rule in item_rules:
        if _normalize_entry_gender(getattr(rule, 'gender', None)) == 'all':
            return rule
    return None


def _calc_entry_score(
        raw_score: float | None,
        rule,
        conflict_policy: str,
        grade_name: str,
        item_code: str | None = None
) -> dict:
    normalized_item_code = (str(item_code or '').strip().lower())
    if normalized_item_code in {'height', 'weight'}:
        return {
            'score_value': 0.0,
            'is_pass': True,
            'is_excellent': True,
            'is_full': True
        }
    if raw_score is None or not rule:
        return {}
    mode = str(getattr(rule, 'calc_mode', None) or 'segment').strip().lower()
    if mode == 'segment':
        segments = getattr(rule, 'segment_json', None)
        if isinstance(segments, str):
            try:
                segments = json.loads(segments)
            except Exception:
                segments = None
        if not isinstance(segments, list) or not segments:
            return {}
        result = RuleEngine.eval_by_segment(raw_score, segments, grade_name=grade_name, conflict_policy=conflict_policy)
        max_score = to_float(getattr(rule, 'max_score', 0), default=0.0)
        score_value = to_float(result.get('score_value'), default=0.0)
        if max_score > 0 and max_score < score_value <= 100:
            result['score_value'] = round2((score_value / 100.0) * max_score)
        return result
    if mode == 'threshold':
        pass_v = to_float(getattr(rule, 'pass_threshold', 0), default=0.0)
        excellent_v = to_float(getattr(rule, 'excellent_threshold', 0), default=0.0)
        full_v = to_float(getattr(rule, 'full_threshold', 0), default=0.0)
        if pass_v == 0 and excellent_v == 0 and full_v == 0:
            return {}
        result = RuleEngine.eval_by_threshold(raw_score, {
            'pass': pass_v,
            'excellent': excellent_v,
            'full': full_v
        })
        if to_float(getattr(rule, 'max_score', 0), default=0.0) <= 0:
            result['score_value'] = 0.0
        return result
    return {}


def _clean_import_text(value) -> str:
    if value is None:
        return ''
    text = str(value).strip()
    if text.endswith('.0') and text[:-2].isdigit():
        return text[:-2]
    return text


def _normalize_student_import_birthday(value) -> str | None:
    text = _clean_import_text(value)
    if not text:
        return None
    text = text.replace('/', '-').replace('.', '-').split(' ')[0]
    try:
        return datetime.strptime(text, '%Y-%m-%d').date().isoformat()
    except ValueError:
        raise ValueError('出生日期格式应为 YYYY-MM-DD')


def _normalize_student_import_active(value) -> bool:
    text = _clean_import_text(value).lower()
    if not text:
        return True
    return text not in {'0', 'false', 'no', 'n', '否', '停用', '禁用'}


STUDENT_IMPORT_FIELD_LABELS = {
    "name": "姓名",
    "id_card": "身份证",
    "phone": "手机号",
    "gender": "性别",
    "school_id": "学校",
    "grade_id": "年级",
    "class_id": "班级",
    "birthday": "出生日期",
    "is_active": "是否启用",
    "remark": "备注"
}


def _format_student_import_validation_error(exc: ValidationError) -> str:
    messages: list[str] = []
    for error in exc.errors():
        loc = error.get("loc") or []
        field = str(loc[-1]) if loc else ""
        label = STUDENT_IMPORT_FIELD_LABELS.get(field, field or "数据")
        error_type = str(error.get("type") or "")
        message = str(error.get("msg") or "").replace("Value error, ", "")
        if error_type == "missing" or message == "Field required":
            messages.append(f"{label}不能为空")
        elif "Input should be a valid integer" in message:
            messages.append(f"{label}格式不正确")
        elif "Input should be a valid boolean" in message:
            messages.append(f"{label}只能填写 是/否")
        else:
            messages.append(f"{label}：{message}")
    return "；".join(messages) or "数据格式不正确"


def _student_import_headers() -> list[dict]:
    return [
        {"label": "姓名", "field": "name", "required": True},
        {"label": "身份证", "field": "id_card", "required": True, "rules": [vali_id_card]},
        {"label": "手机号", "field": "phone", "required": False},
        {
            "label": "性别",
            "field": "gender",
            "required": True,
            "options": [
                {"label": "男", "value": "male"},
                {"label": "女", "value": "female"}
            ]
        },
        {"label": "学校", "field": "school_name", "required": True},
        {"label": "年级", "field": "grade_name", "required": True},
        {"label": "班级", "field": "class_name", "required": True},
        {"label": "出生日期", "field": "birthday", "required": False},
        {
            "label": "是否启用",
            "field": "is_active",
            "required": False,
            "options": [
                {"label": "是", "value": True},
                {"label": "否", "value": False}
            ]
        },
        {"label": "备注", "field": "remark", "required": False}
    ]


async def _build_student_import_headers(db, auth: Auth) -> list[dict]:
    headers = _student_import_headers()
    school_sql = select(VadminPefSchool).where(
        VadminPefSchool.is_delete == false(),
        VadminPefSchool.is_active == true()
    ).order_by(VadminPefSchool.sort.asc(), VadminPefSchool.id.asc())
    grade_sql = select(VadminPefGrade).where(
        VadminPefGrade.is_delete == false(),
        VadminPefGrade.is_active == true()
    ).order_by(VadminPefGrade.sort.asc(), VadminPefGrade.id.asc())
    class_sql = select(VadminPefClass).where(
        VadminPefClass.is_delete == false(),
        VadminPefClass.is_active == true()
    ).order_by(VadminPefClass.sort.asc(), VadminPefClass.id.asc())

    if not is_global_scope(auth):
        school_ids = auth.school_ids or [-1]
        school_sql = school_sql.where(VadminPefSchool.id.in_(school_ids))
        grade_sql = grade_sql.where(VadminPefGrade.school_id.in_(school_ids))
        if _has_role(auth, ROLE_TEACHER_COACH):
            class_sql = class_sql.where(VadminPefClass.id.in_(auth.class_ids or [-1]))
        else:
            class_sql = class_sql.where(VadminPefClass.school_id.in_(school_ids))

    schools = (await db.scalars(school_sql)).all()
    grades = (await db.scalars(grade_sql)).all()
    classes = (await db.scalars(class_sql)).all()

    header_map = {item["field"]: item for item in headers}
    header_map["school_name"]["options"] = [{"label": item.school_name, "value": item.school_name} for item in schools]
    header_map["grade_name"]["options"] = [{"label": item.grade_name, "value": item.grade_name} for item in grades]
    header_map["class_name"]["options"] = [{"label": item.class_name, "value": item.class_name} for item in classes]
    return headers


def _append_unique(target: list[str], value: str | None):
    text = str(value or "").strip()
    if text and text not in target:
        target.append(text)


async def _build_student_import_scope_options(db, auth: Auth) -> dict:
    sql = (
        select(
            VadminPefSchool.id,
            VadminPefSchool.school_name,
            VadminPefGrade.id,
            VadminPefGrade.grade_name,
            VadminPefClass.id,
            VadminPefClass.class_name
        )
        .select_from(VadminPefClass)
        .join(VadminPefSchool, VadminPefClass.school_id == VadminPefSchool.id)
        .join(VadminPefGrade, VadminPefClass.grade_id == VadminPefGrade.id)
        .where(
            VadminPefSchool.is_delete == false(),
            VadminPefGrade.is_delete == false(),
            VadminPefClass.is_delete == false(),
            VadminPefSchool.is_active == true(),
            VadminPefGrade.is_active == true(),
            VadminPefClass.is_active == true()
        )
        .order_by(VadminPefSchool.sort.asc(), VadminPefGrade.sort.asc(), VadminPefClass.sort.asc())
    )
    if not is_global_scope(auth):
        school_ids = auth.school_ids or [-1]
        sql = sql.where(VadminPefSchool.id.in_(school_ids))
        if _has_role(auth, ROLE_TEACHER_COACH):
            sql = sql.where(VadminPefClass.id.in_(auth.class_ids or [-1]))

    schools: list[str] = []
    grades_by_school: dict[str, list[str]] = {}
    classes_by_school_grade: dict[str, list[str]] = {}
    for _, school_name, _, grade_name, _, class_name in (await db.execute(sql)).all():
        school = str(school_name or "").strip()
        grade = str(grade_name or "").strip()
        class_text = str(class_name or "").strip()
        if not school or not grade or not class_text:
            continue
        _append_unique(schools, school)
        grades_by_school.setdefault(school, [])
        _append_unique(grades_by_school[school], grade)
        key = f"{school}|{grade}"
        classes_by_school_grade.setdefault(key, [])
        _append_unique(classes_by_school_grade[key], class_text)

    return {
        "schools": schools,
        "grades_by_school": grades_by_school,
        "classes_by_school_grade": classes_by_school_grade
    }


def _apply_student_import_template_validations(writer: WriteXlsx, options: dict, max_row: int = 1000):
    if not writer or not writer.wb or not writer.sheet:
        return

    wb = writer.wb
    sheet = writer.sheet
    option_sheet = wb.add_worksheet("_student_options")
    option_sheet.hide()

    def unique_values(values: list[str]) -> list[str]:
        clean_values: list[str] = []
        for value in values:
            _append_unique(clean_values, value)
        return clean_values

    def write_column(col: int, values: list[str]) -> list[str]:
        clean_values = unique_values(values)
        for row_idx, value in enumerate(clean_values):
            option_sheet.write(row_idx, col, value)
        return clean_values

    def define_column_name(name: str, col: int, values: list[str]) -> str | None:
        clean_values = write_column(col, values)
        if not clean_values:
            return None
        col_name = xl_col_to_name(col)
        wb.define_name(name, f"='_student_options'!${col_name}$1:${col_name}${len(clean_values)}")
        return name

    school_name = define_column_name("student_school_list", 0, options.get("schools") or [])
    if school_name:
        sheet.data_validation(1, 4, max_row, 4, {'validate': 'list', 'source': f"={school_name}"})

    grade_start_col = 10
    schools = options.get("schools") or []
    grades_by_school = options.get("grades_by_school") or {}
    school_grade_map_rows = 0
    for index, school in enumerate(schools):
        grades = unique_values(grades_by_school.get(school) or [])
        if not grades:
            continue
        name = f"student_grade_{index + 1}"
        define_column_name(name, grade_start_col + index, grades)
        option_sheet.write(school_grade_map_rows, 1, school)
        option_sheet.write(school_grade_map_rows, 2, name)
        school_grade_map_rows += 1
    if school_grade_map_rows:
        wb.define_name("student_school_grade_map", f"='_student_options'!$B$1:$C${school_grade_map_rows}")
        sheet.data_validation(
            1,
            5,
            max_row,
            5,
            {
                'validate': 'list',
                'source': '=INDIRECT(VLOOKUP($E2,student_school_grade_map,2,FALSE))'
            }
        )

    class_start_col = 80
    classes_by_school_grade = options.get("classes_by_school_grade") or {}
    class_keys = list(classes_by_school_grade.keys())
    grade_class_map_rows = 0
    for index, key in enumerate(class_keys):
        classes = unique_values(classes_by_school_grade.get(key) or [])
        if not classes:
            continue
        name = f"student_class_{index + 1}"
        define_column_name(name, class_start_col + index, classes)
        option_sheet.write(grade_class_map_rows, 3, key)
        option_sheet.write(grade_class_map_rows, 4, name)
        grade_class_map_rows += 1
    if grade_class_map_rows:
        wb.define_name("student_grade_class_map", f"='_student_options'!$D$1:$E${grade_class_map_rows}")
        sheet.data_validation(
            1,
            6,
            max_row,
            6,
            {
                'validate': 'list',
                'source': '=INDIRECT(VLOOKUP($E2&"|"&$F2,student_grade_class_map,2,FALSE))'
            }
        )


async def _build_student_import_template_config(db, auth: Auth) -> tuple[list[dict], dict]:
    headers = await _build_student_import_headers(db, auth)
    scope_options = await _build_student_import_scope_options(db, auth)
    template_headers = [dict(item) for item in headers]
    for item in template_headers:
        if item.get("field") in {"school_name", "grade_name", "class_name"}:
            item.pop("options", None)
    return template_headers, scope_options


async def _resolve_student_import_scope(db, auth: Auth, school_name: str, grade_name: str, class_name: str):
    school = await db.scalar(select(VadminPefSchool).where(
        VadminPefSchool.school_name == school_name,
        VadminPefSchool.is_delete == false(),
        VadminPefSchool.is_active == true()
    ))
    if not school:
        raise ValueError('学校不存在或未启用')

    grade = await db.scalar(select(VadminPefGrade).where(
        VadminPefGrade.school_id == school.id,
        VadminPefGrade.grade_name == grade_name,
        VadminPefGrade.is_delete == false(),
        VadminPefGrade.is_active == true()
    ))
    if not grade:
        raise ValueError('年级不存在或未启用')

    class_obj = await db.scalar(select(VadminPefClass).where(
        VadminPefClass.school_id == school.id,
        VadminPefClass.grade_id == grade.id,
        VadminPefClass.class_name == class_name,
        VadminPefClass.is_delete == false(),
        VadminPefClass.is_active == true()
    ))
    if not class_obj:
        raise ValueError('班级不存在或未启用')
    if not _student_visible(auth, school.id, class_obj.id):
        raise ValueError('无权限导入该班级学生')
    return school, grade, class_obj

# ─── 基础选项接口 ──────────────────────────────────────────

@app.get("/public/options/schools", summary="公开学校选项")
async def get_public_school_options(stage_type: str = Query(None), auth: Auth = Depends(OpenAuth())):
    sql = select(VadminPefSchool).where(
        VadminPefSchool.is_delete == false(),
        VadminPefSchool.is_active == true()
    ).order_by(VadminPefSchool.sort.asc(), VadminPefSchool.id.asc())
    if stage_type:
        sql = sql.where(
            or_(
                func.find_in_set(stage_type, VadminPefSchool.stage_types) > 0,
                VadminPefSchool.stage_types.is_(None),
                VadminPefSchool.stage_types == ''
            )
        )
    items = (await auth.db.scalars(sql)).all()
    return SuccessResponse([
        {
            "label": i.school_name,
            "value": i.id,
            "school_name": i.school_name,
            "stage_types": _normalize_stage_types(i.stage_types)
        } for i in items
    ])


@app.get("/public/options/grades", summary="公开年级选项")
async def get_public_grade_options(
    school_id: int = Query(None),
    school_name: str = Query(None),
    auth: Auth = Depends(OpenAuth())
):
    sql = select(VadminPefGrade).where(
        VadminPefGrade.is_delete == false(),
        VadminPefGrade.is_active == true()
    ).order_by(VadminPefGrade.sort.asc(), VadminPefGrade.id.asc())
    if school_id:
        sql = sql.where(VadminPefGrade.school_id == school_id)
    if school_name:
        sql = sql.join(VadminPefSchool, VadminPefGrade.school_id == VadminPefSchool.id).where(
            VadminPefSchool.school_name == school_name
        )
    items = (await auth.db.scalars(sql)).all()
    return SuccessResponse([{"label": i.grade_name, "value": i.id, "grade_name": i.grade_name} for i in items])


@app.get("/public/options/classes", summary="公开班级选项")
async def get_public_class_options(
    grade_id: int = Query(None),
    grade_name: str = Query(None),
    school_id: int = Query(None),
    school_name: str = Query(None),
    auth: Auth = Depends(OpenAuth())
):
    sql = select(VadminPefClass).where(
        VadminPefClass.is_delete == false(),
        VadminPefClass.is_active == true()
    ).order_by(VadminPefClass.sort.asc(), VadminPefClass.id.asc())
    joined_school = False
    if grade_id:
        sql = sql.where(VadminPefClass.grade_id == grade_id)
    if school_id:
        sql = sql.where(VadminPefClass.school_id == school_id)
    if grade_name:
        sql = sql.join(VadminPefGrade, VadminPefClass.grade_id == VadminPefGrade.id)
        sql = sql.where(VadminPefGrade.grade_name == grade_name)
    if school_name:
        if not joined_school:
            sql = sql.join(VadminPefSchool, VadminPefClass.school_id == VadminPefSchool.id)
            joined_school = True
        sql = sql.where(VadminPefSchool.school_name == school_name)
    items = (await auth.db.scalars(sql)).all()
    return SuccessResponse([{"label": i.class_name, "value": i.id, "class_name": i.class_name} for i in items])


@app.get("/options/schools", summary="学校选项")
async def get_school_options(stage_type: str = Query(None), auth: Auth = Depends(FullAdminAuth())):
    sql = select(VadminPefSchool).where(VadminPefSchool.is_delete == false(), VadminPefSchool.is_active == true())
    if not is_global_scope(auth):
        sql = sql.where(VadminPefSchool.id.in_(auth.school_ids or [-1]))
    if stage_type:
        sql = sql.where(
            or_(
                func.find_in_set(stage_type, VadminPefSchool.stage_types) > 0,
                VadminPefSchool.stage_types.is_(None),
                VadminPefSchool.stage_types == ''
            )
        )
    items = (await auth.db.scalars(sql)).all()
    return SuccessResponse([
        {
            "label": i.school_name,
            "value": i.id,
            "school_name": i.school_name,
            "stage_types": _normalize_stage_types(i.stage_types)
        } for i in items
    ])

@app.get("/options/grades", summary="年级选项")
async def get_grade_options(school_id: int = Query(None), school_name: str = Query(None), auth: Auth = Depends(FullAdminAuth())):
    sql = select(VadminPefGrade).where(VadminPefGrade.is_delete == false(), VadminPefGrade.is_active == true())
    if not is_global_scope(auth):
        sql = sql.where(VadminPefGrade.school_id.in_(auth.school_ids or [-1]))
    if school_id:
        sql = sql.where(VadminPefGrade.school_id == school_id)
    if school_name:
        sql = sql.join(VadminPefSchool, VadminPefGrade.school_id == VadminPefSchool.id).where(
            VadminPefSchool.school_name == school_name
        )
    items = (await auth.db.scalars(sql)).all()
    return SuccessResponse([{"label": i.grade_name, "value": i.id, "grade_name": i.grade_name} for i in items])

@app.get("/options/classes", summary="班级选项")
async def get_class_options(
    grade_id: int = Query(None),
    grade_name: str = Query(None),
    school_id: int = Query(None),
    school_name: str = Query(None),
    auth: Auth = Depends(FullAdminAuth())
):
    sql = select(VadminPefClass).where(VadminPefClass.is_delete == false(), VadminPefClass.is_active == true())
    joined_school = False
    if not is_global_scope(auth):
        if _has_role(auth, ROLE_TEACHER_COACH):
            sql = sql.where(VadminPefClass.id.in_(auth.class_ids or [-1]))
        else:
            sql = sql.where(VadminPefClass.school_id.in_(auth.school_ids or [-1]))
    if grade_id:
        sql = sql.where(VadminPefClass.grade_id == grade_id)
    if school_id:
        sql = sql.where(VadminPefClass.school_id == school_id)
    if grade_name:
        sql = sql.join(VadminPefGrade, VadminPefClass.grade_id == VadminPefGrade.id)
        sql = sql.where(VadminPefGrade.grade_name == grade_name)
    if school_name:
        if not joined_school:
            sql = sql.join(VadminPefSchool, VadminPefClass.school_id == VadminPefSchool.id)
            joined_school = True
        sql = sql.where(VadminPefSchool.school_name == school_name)
    items = (await auth.db.scalars(sql)).all()
    return SuccessResponse([{"label": i.class_name, "value": i.id, "class_name": i.class_name} for i in items])

@app.get("/options/users/leaders", summary="校领导选项")
async def get_school_leader_options(auth: Auth = Depends(FullAdminAuth(permissions=[SCHOOL_PERM]))):
    sql = (
        select(VadminUser)
        .join(auth_models.vadmin_auth_user_roles, auth_models.vadmin_auth_user_roles.c.user_id == VadminUser.id)
        .join(VadminRole, VadminRole.id == auth_models.vadmin_auth_user_roles.c.role_id)
        .where(
            VadminUser.is_delete == false(),
            VadminUser.is_staff == true(),
            VadminRole.is_delete == false(),
            VadminRole.role_key == ROLE_SCHOOL_LEADER
        )
        .order_by(VadminUser.id.asc())
    )
    items = (await auth.db.scalars(sql)).all()
    return SuccessResponse([
        {
            "label": f"{item.name} ({item.telephone})",
            "value": item.id,
            "name": item.name,
            "telephone": item.telephone
        } for item in items
    ])


@app.get("/options/users/coaches", summary="老师教练选项")
async def get_teacher_coach_options(auth: Auth = Depends(FullAdminAuth(permissions=[CLASS_PERM]))):
    sql = (
        select(VadminUser)
        .join(auth_models.vadmin_auth_user_roles, auth_models.vadmin_auth_user_roles.c.user_id == VadminUser.id)
        .join(VadminRole, VadminRole.id == auth_models.vadmin_auth_user_roles.c.role_id)
        .where(
            VadminUser.is_delete == false(),
            VadminUser.is_staff == true(),
            VadminRole.is_delete == false(),
            VadminRole.role_key == ROLE_TEACHER_COACH
        )
        .order_by(VadminUser.id.asc())
    )
    items = (await auth.db.scalars(sql)).all()
    return SuccessResponse([
        {
            "label": f"{item.name} ({item.telephone})",
            "value": item.id,
            "name": item.name,
            "telephone": item.telephone
        } for item in items
    ])

@app.get("/options/standard/items", summary="标准项目选项")
async def get_standard_item_options(standard_id: int = Query(...), auth: Auth = Depends(FullAdminAuth())):
    standard = await auth.db.get(VadminSportStandard, standard_id)
    sql = select(VadminSportStandardItem).where(
        VadminSportStandardItem.standard_id == standard_id,
        VadminSportStandardItem.is_delete == false()
    ).order_by(VadminSportStandardItem.sort.asc())
    items = (await auth.db.scalars(sql)).all()
    items = BatchImportService.normalize_standard_items(
        getattr(standard, 'biz_type', ''),
        standard_id,
        items
    )
    
    grouped: dict[str, list[VadminSportStandardItem]] = {}
    for item in items:
        grouped.setdefault(item.item_code, []).append(item)

    result = []
    for item_code, code_items in grouped.items():
        first = code_items[0]
        result.append({
            "label": first.item_name,
            "value": item_code,
            "help_lines": _build_standard_item_help_lines(code_items),
            "calc_mode": first.calc_mode,
            "item_name": first.item_name
        })
    return SuccessResponse(result)

# ─── 学校管理 ─────────────────────────────────────────────

@app.get("/school/list", summary="学校列表")
async def get_school_list(auth: Auth = Depends(FullAdminAuth(permissions=[SCHOOL_PERM]))):
    if not _can_manage_school(auth):
        return ErrorResponse("无权限操作")
    sql = select(VadminPefSchool).where(VadminPefSchool.is_delete == false()).order_by(VadminPefSchool.sort.asc())
    queryset = await auth.db.scalars(sql)
    rows = queryset.all()
    leader_ids_map, leader_names_map = await _get_school_leader_map(auth.db, [item.id for item in rows])
    data = []
    for item in rows:
        row = _serialize(item, schemas.SchoolOut)
        row["leader_user_ids"] = leader_ids_map.get(item.id, [])
        row["leader_names"] = leader_names_map.get(item.id, [])
        data.append(row)
    return SuccessResponse(data)

@app.post("/school", summary="创建学校")
async def create_school(data: schemas.SchoolIn = Body(...), auth: Auth = Depends(FullAdminAuth(permissions=[SCHOOL_PERM]))):
    if not _can_manage_school(auth):
        return ErrorResponse("无权限操作")
    payload = data.model_dump()
    payload['stage_types'] = _normalize_stage_types(payload.get('stage_types'))
    leader_user_ids = payload.pop('leader_user_ids', [])
    if not await _validate_leader_users(auth.db, leader_user_ids):
        return ErrorResponse("存在无效的校领导账号")
    obj = VadminPefSchool(**payload)
    auth.db.add(obj)
    await auth.db.flush()
    await _sync_school_leaders(auth.db, obj.id, leader_user_ids)
    return SuccessResponse("创建成功")

@app.put("/school/{id}", summary="更新学校")
async def update_school(id: int, data: schemas.SchoolUpdate = Body(...), auth: Auth = Depends(FullAdminAuth(permissions=[SCHOOL_PERM]))):
    if not _can_manage_school(auth):
        return ErrorResponse("无权限操作")
    obj = await auth.db.get(VadminPefSchool, id)
    if not obj:
        return ErrorResponse("学校不存在")
    payload = data.model_dump()
    payload['stage_types'] = _normalize_stage_types(payload.get('stage_types'))
    leader_user_ids = payload.pop('leader_user_ids', [])
    if not await _validate_leader_users(auth.db, leader_user_ids):
        return ErrorResponse("存在无效的校领导账号")
    for k, v in payload.items():
        setattr(obj, k, v)
    await auth.db.flush()
    await _sync_school_leaders(auth.db, obj.id, leader_user_ids)
    return SuccessResponse("更新成功")

# ─── 年级管理 ─────────────────────────────────────────────

@app.get("/grade/list", summary="年级列表")
async def get_grade_list(auth: Auth = Depends(FullAdminAuth(permissions=[GRADE_PERM]))):
    if not _can_manage_grade(auth):
        return ErrorResponse("无权限操作")
    sql = select(VadminPefGrade, VadminPefSchool.school_name)\
        .select_from(VadminPefGrade)\
        .join(VadminPefSchool, VadminPefGrade.school_id == VadminPefSchool.id)\
        .where(VadminPefGrade.is_delete == false())
    result = await auth.db.execute(sql)
    data = []
    for grade, school_name in result.all():
        if not _grade_visible(auth, grade.school_id):
            continue
        data.append(_serialize(grade, schemas.GradeOut, school_name=school_name))
    return SuccessResponse(data)

@app.post("/grade", summary="创建年级")
async def create_grade(data: schemas.GradeIn = Body(...), auth: Auth = Depends(FullAdminAuth(permissions=[GRADE_PERM]))):
    if not _can_manage_grade(auth):
        return ErrorResponse("无权限操作")
    school = await _load_school_or_none(auth.db, data.school_id)
    if not school:
        return ErrorResponse("学校不存在")
    if not _school_id_in_scope(auth, school.id):
        return ErrorResponse("无权限操作该学校")
    grade = VadminPefGrade(**data.model_dump())
    auth.db.add(grade)
    await auth.db.flush()
    return SuccessResponse("创建成功")

@app.put("/grade/{id}", summary="更新年级")
async def update_grade(id: int, data: schemas.GradeUpdate = Body(...), auth: Auth = Depends(FullAdminAuth(permissions=[GRADE_PERM]))):
    if not _can_manage_grade(auth):
        return ErrorResponse("无权限操作")
    grade = await auth.db.get(VadminPefGrade, id)
    if not grade:
        return ErrorResponse("数据不存在")
    old_school = await _load_school_or_none(auth.db, grade.school_id)
    new_school = await _load_school_or_none(auth.db, data.school_id)
    if not old_school or not new_school:
        return ErrorResponse("学校不存在")
    if (not _school_id_in_scope(auth, old_school.id)) or (not _school_id_in_scope(auth, new_school.id)):
        return ErrorResponse("无权限操作该学校")
    for k, v in data.model_dump().items():
        setattr(grade, k, v)
    await auth.db.flush()
    return SuccessResponse("更新成功")

# ─── 班级管理 ─────────────────────────────────────────────

@app.get("/class/list", summary="班级列表")
async def get_class_list(auth: Auth = Depends(FullAdminAuth(permissions=[CLASS_PERM]))):
    if not _can_manage_class(auth):
        return ErrorResponse("无权限操作")
    sql = select(VadminPefClass, VadminPefSchool.school_name, VadminPefGrade.grade_name)\
        .select_from(VadminPefClass)\
        .join(VadminPefSchool, VadminPefClass.school_id == VadminPefSchool.id)\
        .join(VadminPefGrade, VadminPefClass.grade_id == VadminPefGrade.id)\
        .where(VadminPefClass.is_delete == false())
    result = await auth.db.execute(sql)
    rows = result.all()
    coach_ids_map, coach_names_map = await _get_class_coach_map(auth.db, [row[0].id for row in rows])
    data = []
    for obj, school_name, grade_name in rows:
        if not _class_visible(auth, obj.school_id, obj.id):
            continue
        row = _serialize(obj, schemas.ClassOut, school_name=school_name, grade_name=grade_name)
        row["coach_user_ids"] = coach_ids_map.get(obj.id, [])
        row["coach_names"] = coach_names_map.get(obj.id, [])
        data.append(row)
    return SuccessResponse(data)

@app.post("/class", summary="创建班级")
async def create_class(data: schemas.ClassIn = Body(...), auth: Auth = Depends(FullAdminAuth(permissions=[CLASS_PERM]))):
    if not _can_manage_class(auth):
        return ErrorResponse("无权限操作")
    school = await _load_school_or_none(auth.db, data.school_id)
    grade = await _load_grade_or_none(auth.db, data.grade_id)
    if not school or not grade:
        return ErrorResponse("学校或年级不存在")
    if grade.school_id != school.id:
        return ErrorResponse("年级与学校不匹配")
    if not _school_id_in_scope(auth, school.id):
        return ErrorResponse("无权限操作该学校")
    payload = data.model_dump()
    coach_user_ids = payload.pop("coach_user_ids", [])
    if not await _validate_coach_users(auth.db, coach_user_ids):
        return ErrorResponse("存在无效的老师教练账号")
    obj = VadminPefClass(**payload)
    auth.db.add(obj)
    await auth.db.flush()
    await _sync_class_coaches(auth.db, obj.id, coach_user_ids)
    return SuccessResponse("创建成功")

@app.put("/class/{id}", summary="更新班级")
async def update_class(id: int, data: schemas.ClassUpdate = Body(...), auth: Auth = Depends(FullAdminAuth(permissions=[CLASS_PERM]))):
    if not _can_manage_class(auth):
        return ErrorResponse("无权限操作")
    obj = await auth.db.get(VadminPefClass, id)
    if not obj:
        return ErrorResponse("数据不存在")
    old_school = await _load_school_or_none(auth.db, obj.school_id)
    new_school = await _load_school_or_none(auth.db, data.school_id)
    grade = await _load_grade_or_none(auth.db, data.grade_id)
    if not old_school or not new_school or not grade:
        return ErrorResponse("学校或年级不存在")
    if grade.school_id != new_school.id:
        return ErrorResponse("年级与学校不匹配")
    if (not _school_id_in_scope(auth, old_school.id)) or (not _school_id_in_scope(auth, new_school.id)):
        return ErrorResponse("无权限操作该学校")
    payload = data.model_dump()
    coach_user_ids = payload.pop("coach_user_ids", [])
    if not await _validate_coach_users(auth.db, coach_user_ids):
        return ErrorResponse("存在无效的老师教练账号")
    for k, v in payload.items():
        setattr(obj, k, v)
    await auth.db.flush()
    await _sync_class_coaches(auth.db, obj.id, coach_user_ids)
    return SuccessResponse("更新成功")

# ─── 学生管理 ─────────────────────────────────────────────

@app.post("/student/register", summary="学生自主注册")
async def register_student(data: schemas.StudentRegisterIn = Body(...), auth: Auth = Depends(OpenAuth())):
    school = await _load_school_or_none(auth.db, data.school_id)
    grade = await _load_grade_or_none(auth.db, data.grade_id)
    class_obj = await _load_class_or_none(auth.db, data.class_id)
    if not school or not grade or not class_obj:
        return ErrorResponse("学校/年级/班级不存在或已停用")
    if not school.is_active or not grade.is_active or not class_obj.is_active:
        return ErrorResponse("学校/年级/班级不存在或已停用")
    if grade.school_id != school.id or class_obj.school_id != school.id or class_obj.grade_id != grade.id:
        return ErrorResponse("学校、年级、班级不匹配")

    student = await auth.db.scalar(select(VadminPefStudent).where(
        VadminPefStudent.id_card == data.id_card,
        VadminPefStudent.is_delete == false()
    ))
    if student:
        if (
            student.name != data.name
            or _normalize_entry_gender(student.gender) != _normalize_entry_gender(data.gender)
            or student.school_id != data.school_id
            or student.grade_id != data.grade_id
            or student.class_id != data.class_id
        ):
            return ErrorResponse("身份证对应的学生档案信息不一致，请核对后再注册")

    student_data = schemas.StudentIn(
        name=data.name,
        gender=data.gender,
        id_card=data.id_card,
        school_id=data.school_id,
        grade_id=data.grade_id,
        class_id=data.class_id,
        phone=data.phone,
        is_active=True
    )
    user, error = await _sync_student_login_user(auth.db, student, student_data)
    if error:
        return ErrorResponse(error)

    payload = student_data.model_dump()
    payload["user_id"] = user.id
    if student:
        await _sync_student_score_identity(auth.db, student.student_no, student_data)
        for key, value in payload.items():
            setattr(student, key, value)
    else:
        auth.db.add(VadminPefStudent(**payload))
    await auth.db.flush()
    return SuccessResponse(
        {"password_tip": "默认密码为身份证后8位"},
        msg="注册成功，请使用身份证号和默认密码登录"
    )


@app.get("/student/self-entry/options", summary="学生本人录入批次与项目")
async def get_student_self_entry_options(auth: Auth = Depends(AllUserAuth())):
    if getattr(auth.user, 'is_staff', False):
        return ErrorResponse("当前入口仅支持学生/家长账号使用")
    ctx = await _get_self_student_context(auth.db, auth.user)
    if not ctx:
        return ErrorResponse("未找到学生档案，请先完成学生注册")

    student = ctx["student"]
    batch_rows = (await auth.db.scalars(select(VadminSportBatch).where(
        VadminSportBatch.is_delete == false(),
        VadminSportBatch.biz_type.in_(['pe', 'fitness'])
    ).order_by(VadminSportBatch.id.desc()))).all()
    batches = [
        batch for batch in batch_rows
        if _batch_matches_student(batch, ctx["school_name"], ctx["grade_name"], ctx["class_name"])
    ]
    standard_ids = sorted({batch.standard_id for batch in batches if batch.standard_id})
    item_map: dict[int, list] = {}
    if standard_ids:
        item_rows = (await auth.db.scalars(select(VadminSportStandardItem).where(
            VadminSportStandardItem.is_delete == false(),
            VadminSportStandardItem.standard_id.in_(standard_ids)
        ).order_by(VadminSportStandardItem.sort.asc(), VadminSportStandardItem.id.asc()))).all()
        for item in item_rows:
            item_map.setdefault(item.standard_id, []).append(item)

    data_batches = []
    for batch in batches:
        items = BatchImportService.normalize_standard_items(batch.biz_type, batch.standard_id, item_map.get(batch.standard_id, []))
        data_batches.append({
            "label": batch.batch_name,
            "value": batch.id,
            "batch_id": batch.id,
            "biz_type": batch.biz_type,
            "biz_name": "体考" if batch.biz_type == "pe" else "体测",
            "standard_id": batch.standard_id,
            "items": _build_entry_item_options(items, student.gender)
        })

    return SuccessResponse({
        "profile": {
            "student_no": student.student_no,
            "student_name": student.name,
            "gender": student.gender,
            "school_name": ctx["school_name"],
            "grade_name": ctx["grade_name"],
            "class_name": ctx["class_name"]
        },
        "batches": data_batches
    })


@app.post("/student/self-entry/submit", summary="学生本人提交成绩")
async def submit_student_self_entry(payload: dict = Body(...), auth: Auth = Depends(AllUserAuth())):
    if getattr(auth.user, 'is_staff', False):
        return ErrorResponse("当前入口仅支持学生/家长账号使用")
    ctx = await _get_self_student_context(auth.db, auth.user)
    if not ctx:
        return ErrorResponse("未找到学生档案，请先完成学生注册")
    if not payload.get("batch_id"):
        return ErrorResponse("请选择批次")
    batch = await auth.db.scalar(select(VadminSportBatch).where(
        VadminSportBatch.id == int(payload.get("batch_id")),
        VadminSportBatch.is_delete == false(),
        VadminSportBatch.biz_type.in_(['pe', 'fitness'])
    ))
    if not batch:
        return ErrorResponse("批次不存在")
    if not _batch_matches_student(batch, ctx["school_name"], ctx["grade_name"], ctx["class_name"]):
        return ErrorResponse("当前批次不适用于该学生")

    standard = await auth.db.get(VadminSportStandard, batch.standard_id)
    conflict_policy = (standard.conflict_policy if standard else None) or 'lower_priority'
    standard_items = (await auth.db.scalars(select(VadminSportStandardItem).where(
        VadminSportStandardItem.standard_id == batch.standard_id,
        VadminSportStandardItem.is_delete == false()
    ).order_by(VadminSportStandardItem.sort.asc(), VadminSportStandardItem.id.asc()))).all()
    standard_items = BatchImportService.normalize_standard_items(batch.biz_type, batch.standard_id, standard_items)

    item_rule_map: dict[str, list] = {}
    for item in standard_items:
        if _item_matches_student_gender(item, ctx["student"].gender):
            item_rule_map.setdefault(_normalize_entry_item_code(item.item_code), []).append(item)

    scores = payload.get("scores") or []
    if not isinstance(scores, list) or not scores:
        return ErrorResponse("请填写至少一项成绩")

    student = ctx["student"]
    submitted_hw: dict[str, float] = {}
    submitted_bmi_students: set[str] = set()
    existing_hw: dict[str, float] = {}
    existing_bmi_row: VadminSportScore | None = None

    existing_rows = (await auth.db.scalars(select(VadminSportScore).where(
        VadminSportScore.is_delete == false(),
        VadminSportScore.biz_type == batch.biz_type,
        VadminSportScore.batch_id == batch.id,
        VadminSportScore.student_no == student.student_no,
        VadminSportScore.item_code.in_(['height', 'weight', 'bmi'])
    ))).all()
    for row in existing_rows:
        code = _normalize_entry_item_code(row.item_code)
        if code in {'height', 'weight'}:
            existing_hw[code] = to_float(row.raw_score)
        elif code == 'bmi':
            existing_bmi_row = row

    count = 0
    for item in scores:
        item_code = _normalize_entry_item_code(item.get("item_code"))
        if not item_code or item_code not in item_rule_map:
            return ErrorResponse("存在不适用于当前学生的项目")
        raw_text = str(item.get("raw_score") or "").strip()
        raw_score = None
        if raw_text:
            raw_score = _parse_entry_raw_score(raw_text, item_code)
            if raw_score is None:
                return ErrorResponse(f"成绩格式不正确：{raw_text}")
        if item_code in {'height', 'weight'}:
            if raw_score is not None and raw_score > 0:
                submitted_hw[item_code] = raw_score
        if item_code == 'bmi':
            submitted_bmi_students.add(student.student_no)
        if item_code == 'bmi' and raw_text == '':
            merged_hw = {
                **existing_hw,
                **submitted_hw
            }
            raw_score = _calc_bmi(merged_hw.get('height'), merged_hw.get('weight'))
            if raw_score is None:
                continue
        if raw_text == '':
            continue
        item_rules = item_rule_map.get(item_code) or []
        selected_rule = _select_entry_rule(item_rules, student.gender)
        calc_result = _calc_entry_score(
            raw_score,
            selected_rule,
            conflict_policy,
            ctx["grade_name"],
            item_code
        )
        item_name = getattr(selected_rule, 'item_name', None) or item.get("item_name") or item_code
        score_value = calc_result.get('score_value') if 'score_value' in calc_result else None

        row = await auth.db.scalar(select(VadminSportScore).where(
            VadminSportScore.is_delete == false(),
            VadminSportScore.biz_type == batch.biz_type,
            VadminSportScore.batch_id == batch.id,
            VadminSportScore.student_no == student.student_no,
            VadminSportScore.item_code == item_code
        ).limit(1))
        if row:
            row.raw_score = raw_score
            row.score_value = score_value
            row.is_pass = calc_result.get('is_pass')
            row.is_excellent = calc_result.get('is_excellent')
            row.is_full = calc_result.get('is_full')
            row.mobile = student.phone
            row.item_name = item_name
        else:
            auth.db.add(VadminSportScore(
                biz_type=batch.biz_type,
                batch_id=batch.id,
                student_no=student.student_no,
                student_name=student.name,
                gender=student.gender,
                mobile=student.phone,
                school_name=ctx["school_name"],
                grade_name=ctx["grade_name"],
                class_name=ctx["class_name"],
                item_code=item_code,
                item_name=item_name,
                raw_score=raw_score,
                score_value=score_value,
                is_pass=calc_result.get('is_pass'),
                is_excellent=calc_result.get('is_excellent'),
                is_full=calc_result.get('is_full')
            ))
        count += 1
    if 'bmi' in item_rule_map and student.student_no not in submitted_bmi_students:
        merged_hw = {
            **existing_hw,
            **submitted_hw
        }
        bmi_raw = _calc_bmi(merged_hw.get('height'), merged_hw.get('weight'))
        if bmi_raw is not None:
            bmi_rules = item_rule_map.get('bmi') or []
            selected_rule = _select_entry_rule(bmi_rules, student.gender)
            calc_result = _calc_entry_score(
                bmi_raw,
                selected_rule,
                conflict_policy,
                ctx["grade_name"],
                'bmi'
            )
            if existing_bmi_row:
                existing_bmi_row.raw_score = bmi_raw
                existing_bmi_row.score_value = calc_result.get('score_value')
                existing_bmi_row.is_pass = calc_result.get('is_pass')
                existing_bmi_row.is_excellent = calc_result.get('is_excellent')
                existing_bmi_row.is_full = calc_result.get('is_full')
            else:
                item_name = getattr(selected_rule, 'item_name', None) if selected_rule else 'BMI'
                auth.db.add(VadminSportScore(
                    biz_type=batch.biz_type,
                    batch_id=batch.id,
                    student_no=student.student_no,
                    student_name=student.name,
                    gender=student.gender,
                    mobile=student.phone,
                    school_name=ctx["school_name"],
                    grade_name=ctx["grade_name"],
                    class_name=ctx["class_name"],
                    item_code='bmi',
                    item_name=item_name,
                    raw_score=bmi_raw,
                    score_value=calc_result.get('score_value'),
                    is_pass=calc_result.get('is_pass'),
                    is_excellent=calc_result.get('is_excellent'),
                    is_full=calc_result.get('is_full')
                ))
            count += 1
    if count == 0:
        return ErrorResponse("请填写至少一项成绩")
    await auth.db.flush()
    return SuccessResponse({"upsert_count": count}, msg="成绩已提交，评分计算中")


@app.get("/student/list", summary="学生列表")
async def get_student_list(
    page: int = Query(1),
    limit: int = Query(10),
    name: str = Query(None),
    student_no: str = Query(None),
    school_id: int = Query(None),
    school_name: str = Query(None),
    grade_id: int = Query(None),
    grade_name: str = Query(None),
    class_id: int = Query(None),
    class_name: str = Query(None),
    auth: Auth = Depends(FullAdminAuth(permissions=[STUDENT_PERM]))
):
    if not _can_manage_student(auth):
        return ErrorResponse("无权限操作")
    sql = select(VadminPefStudent, VadminPefSchool.school_name, VadminPefGrade.grade_name, VadminPefClass.class_name)\
        .select_from(VadminPefStudent)\
        .join(VadminPefSchool, VadminPefStudent.school_id == VadminPefSchool.id)\
        .join(VadminPefGrade, VadminPefStudent.grade_id == VadminPefGrade.id)\
        .join(VadminPefClass, VadminPefStudent.class_id == VadminPefClass.id)\
        .where(VadminPefStudent.is_delete == false())
    
    if name:
        sql = sql.where(VadminPefStudent.name.like(f"%{name}%"))
    if student_no:
        sql = sql.where(VadminPefStudent.student_no.like(f"%{student_no}%"))
    if school_id:
        sql = sql.where(VadminPefStudent.school_id == school_id)
    if school_name:
        sql = sql.where(VadminPefSchool.school_name == school_name)
    if grade_id:
        sql = sql.where(VadminPefStudent.grade_id == grade_id)
    if grade_name:
        sql = sql.where(VadminPefGrade.grade_name == grade_name)
    if class_id:
        sql = sql.where(VadminPefStudent.class_id == class_id)
    if class_name:
        sql = sql.where(VadminPefClass.class_name == class_name)
    
    result = await auth.db.execute(sql)
    all_rows = [
        row for row in result.all()
        if _student_visible(auth, row[0].school_id, row[0].class_id)
    ]
    total = len(all_rows)
    paged = all_rows[(page-1)*limit : page*limit]
    
    data = []
    for obj, school_name, grade_name, class_name in paged:
        data.append(_serialize(obj, schemas.StudentOut, school_name=school_name, grade_name=grade_name, class_name=class_name))
    
    return SuccessResponse({"items": data, "total": total})


@app.get("/student/import/template", summary="下载学生批量导入模板")
async def download_student_import_template(
    direct: bool = Query(False),
    auth: Auth = Depends(FullAdminAuth(permissions=[STUDENT_PERM]))
):
    if not _can_manage_student(auth):
        return ErrorResponse("无权限操作")
    headers, scope_options = await _build_student_import_template_config(auth.db, auth)
    writer = WriteXlsx()
    writer.create_excel(sheet_name="学生导入模板", save_static=True)
    writer.generate_template(headers)
    _apply_student_import_template_validations(writer, scope_options)
    writer.close()
    if direct:
        return FileResponse(
            writer.file_path,
            filename="学生导入模板.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    return SuccessResponse({"url": writer.get_file_url(), "filename": "学生导入模板.xlsx"})


@app.post("/student/import", summary="批量导入学生")
async def import_students(
    file: UploadFile | None = File(None),
    auth: Auth = Depends(FullAdminAuth(permissions=[STUDENT_PERM]))
):
    if not _can_manage_student(auth):
        return ErrorResponse("无权限操作")
    if not file:
        return ErrorResponse("请选择要导入的 XLSX 文件")
    headers = await _build_student_import_headers(auth.db, auth)
    importer = ImportManage(file, headers)
    await importer.get_table_data()
    importer.check_table_data()

    seen_id_cards: set[str] = set()
    for item in list(importer.success):
        old_data_list = item.pop("old_data_list")
        try:
            id_card = vali_id_card(_clean_import_text(item.get("id_card")))
            if id_card in seen_id_cards:
                raise ValueError("同一导入文件中身份证重复")
            seen_id_cards.add(id_card)

            school_name = _clean_import_text(item.get("school_name"))
            grade_name = _clean_import_text(item.get("grade_name"))
            class_name = _clean_import_text(item.get("class_name"))
            school, grade, class_obj = await _resolve_student_import_scope(
                auth.db,
                auth,
                school_name,
                grade_name,
                class_name
            )

            data = schemas.StudentIn(
                name=_clean_import_text(item.get("name")),
                id_card=id_card,
                phone=_clean_import_text(item.get("phone")),
                gender=_clean_import_text(item.get("gender")),
                school_id=school.id,
                grade_id=grade.id,
                class_id=class_obj.id,
                birthday=_normalize_student_import_birthday(item.get("birthday")),
                is_active=_normalize_student_import_active(item.get("is_active")),
                remark=_clean_import_text(item.get("remark")) or None
            )

            obj = await auth.db.scalar(select(VadminPefStudent).where(
                VadminPefStudent.id_card == data.id_card,
                VadminPefStudent.is_delete == false()
            ))
            if obj and not _student_visible(auth, obj.school_id, obj.class_id):
                raise ValueError("无权限更新该学生数据")

            user, error = await _sync_student_login_user(auth.db, obj, data)
            if error:
                raise ValueError(error)

            payload = data.model_dump()
            payload["user_id"] = user.id
            if obj:
                await _sync_student_score_identity(auth.db, obj.student_no, data)
                for key, value in payload.items():
                    setattr(obj, key, value)
            else:
                auth.db.add(VadminPefStudent(**payload))
            await auth.db.flush()
        except ValidationError as exc:
            old_data_list.append(_format_student_import_validation_error(exc))
            importer.add_error_data(old_data_list)
        except ValueError as exc:
            old_data_list.append(str(exc))
            importer.add_error_data(old_data_list)

    return SuccessResponse({
        "success_number": importer.success_number,
        "error_number": importer.error_number,
        "error_url": importer.generate_error_url()
    })


@app.post("/student", summary="创建学生")
async def create_student(data: schemas.StudentIn, auth: Auth = Depends(FullAdminAuth(permissions=[STUDENT_PERM]))):
    if not _can_manage_student(auth):
        return ErrorResponse("无权限操作")
    school = await _load_school_or_none(auth.db, data.school_id)
    grade = await _load_grade_or_none(auth.db, data.grade_id)
    class_obj = await _load_class_or_none(auth.db, data.class_id)
    if not school or not grade or not class_obj:
        return ErrorResponse("学校/年级/班级不存在")
    if grade.school_id != school.id or class_obj.school_id != school.id or class_obj.grade_id != grade.id:
        return ErrorResponse("学生归属信息不匹配")
    if not _student_visible(auth, school.id, class_obj.id):
        return ErrorResponse("无权限操作该学生数据")
    user, error = await _sync_student_login_user(auth.db, None, data)
    if error:
        return ErrorResponse(error)
    payload = data.model_dump()
    payload['user_id'] = user.id
    obj = VadminPefStudent(**payload)
    auth.db.add(obj)
    await auth.db.flush()
    return SuccessResponse("创建成功")

@app.put("/student/{id}", summary="更新学生档案")
async def update_student(id: int, data: schemas.StudentUpdate, auth: Auth = Depends(FullAdminAuth(permissions=[STUDENT_PERM]))):
    if not _can_manage_student(auth):
        return ErrorResponse("无权限操作")
    obj = await auth.db.get(VadminPefStudent, id)
    if not obj:
        return ErrorResponse("学生不存在")
    old_school = await _load_school_or_none(auth.db, obj.school_id)
    school = await _load_school_or_none(auth.db, data.school_id)
    grade = await _load_grade_or_none(auth.db, data.grade_id)
    class_obj = await _load_class_or_none(auth.db, data.class_id)
    if not old_school or not school or not grade or not class_obj:
        return ErrorResponse("学校/年级/班级不存在")
    if grade.school_id != school.id or class_obj.school_id != school.id or class_obj.grade_id != grade.id:
        return ErrorResponse("学生归属信息不匹配")
    if (not _student_visible(auth, old_school.id, obj.class_id)) or (not _student_visible(auth, school.id, class_obj.id)):
        return ErrorResponse("无权限操作该学生数据")
    user, error = await _sync_student_login_user(auth.db, obj, data)
    if error:
        return ErrorResponse(error)
    await _sync_student_score_identity(auth.db, obj.student_no, data)
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    obj.user_id = user.id
    await auth.db.flush()
    return SuccessResponse("更新成功")
