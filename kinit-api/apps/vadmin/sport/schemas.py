#!/usr/bin/python
# -*- coding: utf-8 -*-

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class SchoolOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    school_name: str
    school_code: Optional[str] = None
    region: Optional[str] = None
    stage_types: Optional[str] = None
    sort: int
    is_active: bool
    create_datetime: datetime

class GradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    school_id: int
    school_name: Optional[str] = None
    grade_name: str
    grade_code: Optional[str] = None
    sort: int
    is_active: bool
    create_datetime: datetime

class ClassOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    school_id: int
    school_name: Optional[str] = None
    grade_id: int
    grade_name: Optional[str] = None
    class_name: str
    class_code: Optional[str] = None
    sort: int
    is_active: bool
    create_datetime: datetime

class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    school_id: int
    school_name: Optional[str] = None
    grade_id: int
    grade_name: Optional[str] = None
    class_id: int
    class_name: Optional[str] = None
    student_no: str
    name: str
    gender: str
    phone: Optional[str] = None
    is_active: bool
    create_datetime: datetime

class BatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    biz_type: str
    batch_name: str
    standard_id: int
    school_name: str
    grade_name: str
    class_name: str
    stage_type: Optional[str] = None
    status: str
    create_datetime: datetime

class ScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    biz_type: str
    batch_id: int
    student_no: str
    student_name: str
    item_code: str
    item_name: str
    raw_score: Optional[float] = None
    score_value: Optional[float] = None
    create_datetime: datetime
