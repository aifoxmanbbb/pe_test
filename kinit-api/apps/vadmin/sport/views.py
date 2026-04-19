#!/usr/bin/python
# -*- coding: utf-8 -*-

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import select, false, true, func, or_
from apps.vadmin.auth import models as auth_models
from apps.vadmin.auth.models import VadminMenu, VadminRole, VadminUser
from apps.vadmin.auth.utils.current import FullAdminAuth
from apps.vadmin.auth.utils.validation.auth import Auth
from application import settings
from utils.response import SuccessResponse, ErrorResponse
from .models import (
    VadminPefSchool,
    VadminPefGrade,
    VadminPefClass,
    VadminPefStudent,
    VadminSportStandardItem,
    vadmin_pef_school_leaders,
    vadmin_pef_class_coaches
)
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
STUDENT_ROLE_NAME = '家长'
STUDENT_ROOT_PERM = 'sport.student'
STUDENT_SCORE_PERM = 'sport.student.scores'
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


def _default_user_password(telephone: str) -> str:
    return telephone[-8:] if settings.DEFAULT_PASSWORD == "0" else settings.DEFAULT_PASSWORD


def _normalize_auth_gender(value: str | int | None) -> str:
    text = str(value or '').strip().lower()
    if text in {'1', 'male', 'm', '男'}:
        return '1'
    if text in {'0', 'female', 'f', '女', '2'}:
        return '0'
    return '0'


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
            redirect='/sport/my-scores',
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
    root_menu.redirect = '/sport/my-scores'
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
        VadminMenu.perms == STUDENT_SCORE_PERM,
        VadminMenu.is_delete == false()
    ))
    if not score_menu:
        score_menu = VadminMenu(
            title='我的成绩',
            icon=None,
            redirect=None,
            component='views/Vadmin/Sport/Student/MyScores',
            path='my-scores',
            disabled=False,
            hidden=False,
            order=1,
            menu_type='1',
            parent_id=root_menu.id,
            perms=STUDENT_SCORE_PERM,
            noCache=False,
            breadcrumb=True,
            affix=False,
            noTagsView=False,
            canTo=False,
            alwaysShow=False
        )
        db.add(score_menu)
        await db.flush()
    score_menu.title = '我的成绩'
    score_menu.icon = None
    score_menu.redirect = None
    score_menu.component = 'views/Vadmin/Sport/Student/MyScores'
    score_menu.path = 'my-scores'
    score_menu.disabled = False
    score_menu.hidden = False
    score_menu.order = 1
    score_menu.menu_type = '1'
    score_menu.parent_id = root_menu.id
    score_menu.perms = STUDENT_SCORE_PERM
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
            desc='学生/家长自助账号，仅可查看我的成绩',
            is_admin=False
        )
        db.add(role)
        await db.flush()
    else:
        role.disabled = False

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
    duplicate_student = await db.scalar(select(VadminPefStudent).where(
        VadminPefStudent.phone == data.phone,
        VadminPefStudent.is_delete == false(),
        VadminPefStudent.id != (student.id if student else 0)
    ))
    if duplicate_student:
        return None, '该手机号已绑定其他学生'

    role = await _ensure_student_menu_role(db)

    current_user = None
    if student and student.user_id:
        current_user = await db.scalar(select(VadminUser).where(
            VadminUser.id == student.user_id,
            VadminUser.is_delete == false()
        ))

    user_by_phone = await db.scalar(select(VadminUser).where(
        VadminUser.telephone == data.phone,
        VadminUser.is_delete == false()
    ))

    if user_by_phone and current_user and user_by_phone.id != current_user.id:
        return None, '该手机号已被其他系统账号占用'

    if user_by_phone and user_by_phone.is_staff and (not current_user or user_by_phone.id != current_user.id):
        return None, '该手机号已被其他系统账号占用'

    user = current_user
    telephone_changed = bool(user and user.telephone != data.phone)

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
            telephone=data.phone,
            name=data.name,
            nickname=None,
            password=VadminUser.get_password_hash(_default_user_password(data.phone)),
            gender=_normalize_auth_gender(data.gender),
            is_active=data.is_active,
            is_reset_password=False,
            is_staff=False
        )
        db.add(user)
        await db.flush()

    user.telephone = data.phone
    user.name = data.name
    user.gender = _normalize_auth_gender(data.gender)
    user.is_active = data.is_active
    user.is_staff = False

    if telephone_changed:
        user.password = VadminUser.get_password_hash(_default_user_password(data.phone))
        user.is_reset_password = False

    await db.execute(auth_models.vadmin_auth_user_roles.delete().where(
        auth_models.vadmin_auth_user_roles.c.user_id == user.id
    ))
    await db.execute(auth_models.vadmin_auth_user_roles.insert().values(
        user_id=user.id,
        role_id=role.id
    ))
    return user, None

# ─── 基础选项接口 ──────────────────────────────────────────

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
        sql = sql.join(VadminPefSchool).where(VadminPefSchool.school_name == school_name)
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
        sql = sql.join(VadminPefGrade)
        sql = sql.where(VadminPefGrade.grade_name == grade_name)
    if school_name:
        if not joined_school:
            sql = sql.join(VadminPefSchool)
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
    sql = select(VadminSportStandardItem).where(
        VadminSportStandardItem.standard_id == standard_id,
        VadminSportStandardItem.is_delete == false()
    ).order_by(VadminSportStandardItem.sort.asc())
    items = (await auth.db.scalars(sql)).all()
    
    seen = set()
    result = []
    for i in items:
        if i.item_code not in seen:
            seen.add(i.item_code)
            result.append({"label": i.item_name, "value": i.item_code})
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

@app.get("/student/list", summary="学生列表")
async def get_student_list(
    page: int = Query(1),
    limit: int = Query(10),
    name: str = Query(None),
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
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    obj.user_id = user.id
    await auth.db.flush()
    return SuccessResponse("更新成功")
