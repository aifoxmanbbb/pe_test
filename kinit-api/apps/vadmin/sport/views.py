#!/usr/bin/python
# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, Body, Query
from sqlalchemy import select, false, true, func, or_
from apps.vadmin.auth.utils.current import FullAdminAuth
from apps.vadmin.auth.utils.validation.auth import Auth
from utils.response import SuccessResponse, ErrorResponse
from .models import VadminPefSchool, VadminPefGrade, VadminPefClass, VadminPefStudent, VadminSportStandardItem
from . import schemas
import traceback
import json

app = APIRouter()

STAGE_SET = {'primary', 'mid', 'high', 'university'}


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
async def get_class_options(grade_id: int = Query(None), grade_name: str = Query(None), auth: Auth = Depends(FullAdminAuth())):
    sql = select(VadminPefClass).where(VadminPefClass.is_delete == false(), VadminPefClass.is_active == true())
    if grade_id:
        sql = sql.where(VadminPefClass.grade_id == grade_id)
    if grade_name:
        sql = sql.join(VadminPefGrade).where(VadminPefGrade.grade_name == grade_name)
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
async def create_student(data: dict = Body(...), auth: Auth = Depends(FullAdminAuth())):
    obj = VadminPefStudent(**data)
    auth.db.add(obj)
    await auth.db.flush()
    return SuccessResponse("创建成功")

@app.put("/student/{id}", summary="更新学生档案")
async def update_student(id: int, data: dict = Body(...), auth: Auth = Depends(FullAdminAuth())):
    obj = await auth.db.get(VadminPefStudent, id)
    if not obj: return ErrorResponse("学生不存在")
    for k, v in data.items(): setattr(obj, k, v)
    await auth.db.flush()
    return SuccessResponse("更新成功")
