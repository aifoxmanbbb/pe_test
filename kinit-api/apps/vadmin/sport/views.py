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
from .models import VadminPefSchool, VadminPefGrade, VadminPefClass, VadminPefStudent, VadminSportStandardItem
from . import schemas
import traceback
import json

app = APIRouter()

STAGE_SET = {'primary', 'mid', 'high', 'university'}
STUDENT_ROLE_KEY = 'student_parent'
STUDENT_ROLE_NAME = '家长'
STUDENT_ROOT_PERM = 'sport.student'
STUDENT_SCORE_PERM = 'sport.student.scores'


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
            gender=data.gender,
            is_active=data.is_active,
            is_reset_password=False,
            is_staff=False
        )
        db.add(user)
        await db.flush()

    user.telephone = data.phone
    user.name = data.name
    user.gender = data.gender
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
async def get_school_list(auth: Auth = Depends(FullAdminAuth())):
    sql = select(VadminPefSchool).where(VadminPefSchool.is_delete == false()).order_by(VadminPefSchool.sort.asc())
    queryset = await auth.db.scalars(sql)
    return SuccessResponse([_serialize(i, schemas.SchoolOut) for i in queryset.all()])

@app.post("/school", summary="创建学校")
async def create_school(data: dict = Body(...), auth: Auth = Depends(FullAdminAuth())):
    data['stage_types'] = _normalize_stage_types(data.get('stage_types'))
    obj = VadminPefSchool(**data)
    auth.db.add(obj)
    await auth.db.flush()
    return SuccessResponse("创建成功")

@app.put("/school/{id}", summary="更新学校")
async def update_school(id: int, data: dict = Body(...), auth: Auth = Depends(FullAdminAuth())):
    obj = await auth.db.get(VadminPefSchool, id)
    if not obj: return ErrorResponse("学校不存在")
    if 'stage_types' in data:
        data['stage_types'] = _normalize_stage_types(data.get('stage_types'))
    for k, v in data.items(): setattr(obj, k, v)
    await auth.db.flush()
    return SuccessResponse("更新成功")

# ─── 年级管理 ─────────────────────────────────────────────

@app.get("/grade/list", summary="年级列表")
async def get_grade_list(auth: Auth = Depends(FullAdminAuth())):
    sql = select(VadminPefGrade, VadminPefSchool.school_name)\
        .select_from(VadminPefGrade)\
        .join(VadminPefSchool, VadminPefGrade.school_id == VadminPefSchool.id)\
        .where(VadminPefGrade.is_delete == false())
    result = await auth.db.execute(sql)
    data = []
    for grade, school_name in result.all():
        data.append(_serialize(grade, schemas.GradeOut, school_name=school_name))
    return SuccessResponse(data)

@app.post("/grade", summary="创建年级")
async def create_grade(data: dict = Body(...), auth: Auth = Depends(FullAdminAuth())):
    grade = VadminPefGrade(**data)
    auth.db.add(grade)
    await auth.db.flush()
    return SuccessResponse("创建成功")

@app.put("/grade/{id}", summary="更新年级")
async def update_grade(id: int, data: dict = Body(...), auth: Auth = Depends(FullAdminAuth())):
    grade = await auth.db.get(VadminPefGrade, id)
    if not grade: return ErrorResponse("数据不存在")
    for k, v in data.items(): setattr(grade, k, v)
    await auth.db.flush()
    return SuccessResponse("更新成功")

# ─── 班级管理 ─────────────────────────────────────────────

@app.get("/class/list", summary="班级列表")
async def get_class_list(auth: Auth = Depends(FullAdminAuth())):
    sql = select(VadminPefClass, VadminPefSchool.school_name, VadminPefGrade.grade_name)\
        .select_from(VadminPefClass)\
        .join(VadminPefSchool, VadminPefClass.school_id == VadminPefSchool.id)\
        .join(VadminPefGrade, VadminPefClass.grade_id == VadminPefGrade.id)\
        .where(VadminPefClass.is_delete == false())
    result = await auth.db.execute(sql)
    data = []
    for obj, school_name, grade_name in result.all():
        data.append(_serialize(obj, schemas.ClassOut, school_name=school_name, grade_name=grade_name))
    return SuccessResponse(data)

@app.post("/class", summary="创建班级")
async def create_class(data: dict = Body(...), auth: Auth = Depends(FullAdminAuth())):
    obj = VadminPefClass(**data)
    auth.db.add(obj)
    await auth.db.flush()
    return SuccessResponse("创建成功")

@app.put("/class/{id}", summary="更新班级")
async def update_class(id: int, data: dict = Body(...), auth: Auth = Depends(FullAdminAuth())):
    obj = await auth.db.get(VadminPefClass, id)
    if not obj: return ErrorResponse("数据不存在")
    for k, v in data.items(): setattr(obj, k, v)
    await auth.db.flush()
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
    auth: Auth = Depends(FullAdminAuth())
):
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
    all_rows = result.all()
    total = len(all_rows)
    paged = all_rows[(page-1)*limit : page*limit]
    
    data = []
    for obj, school_name, grade_name, class_name in paged:
        data.append(_serialize(obj, schemas.StudentOut, school_name=school_name, grade_name=grade_name, class_name=class_name))
    
    return SuccessResponse({"items": data, "total": total})

@app.post("/student", summary="创建学生")
async def create_student(data: schemas.StudentIn, auth: Auth = Depends(FullAdminAuth())):
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
async def update_student(id: int, data: schemas.StudentUpdate, auth: Auth = Depends(FullAdminAuth())):
    obj = await auth.db.get(VadminPefStudent, id)
    if not obj: return ErrorResponse("学生不存在")
    user, error = await _sync_student_login_user(auth.db, obj, data)
    if error:
        return ErrorResponse(error)
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    obj.user_id = user.id
    await auth.db.flush()
    return SuccessResponse("更新成功")
