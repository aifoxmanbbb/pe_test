#!/usr/bin/python
# -*- coding: utf-8 -*-

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from datetime import datetime
from typing import Optional
from core.data_types import IdCard
from core.validator import vali_telephone


def normalize_student_gender_value(value) -> str:
    text = str(value or '').strip().lower()
    if text in {'male', 'm', '1', '\u7537'}:
        return 'male'
    if text in {'female', 'f', '0', '2', '\u5973'}:
        return 'female'
    raise ValueError('\u6027\u522b\u5fc5\u987b\u4e3a\u7537\u6216\u5973')


def normalize_optional_phone(value) -> str | None:
    text = str(value or '').strip()
    if not text:
        return None
    return vali_telephone(text)


class SchoolOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    school_name: str
    school_code: Optional[str] = None
    region: Optional[str] = None
    stage_types: Optional[str] = None
    sort: int
    is_active: bool
    leader_user_ids: list[int] = Field(default_factory=list)
    leader_names: list[str] = Field(default_factory=list)
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
    coach_user_ids: list[int] = Field(default_factory=list)
    coach_names: list[str] = Field(default_factory=list)
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
    id_card: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    create_datetime: datetime


class StudentBase(BaseModel):
    student_no: Optional[str] = None
    name: str
    gender: str
    id_card: IdCard
    school_id: int
    grade_id: int
    class_id: int
    phone: Optional[str] = None
    birthday: Optional[str] = None
    is_active: bool = True
    remark: Optional[str] = None

    @field_validator('gender')
    @classmethod
    def validate_gender(cls, value):
        return normalize_student_gender_value(value)

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, value):
        return normalize_optional_phone(value)

    @model_validator(mode='after')
    def fill_student_no(self):
        self.student_no = self.id_card
        return self


class StudentIn(StudentBase):
    pass


class StudentUpdate(StudentBase):
    pass


class StudentRegisterIn(BaseModel):
    name: str
    gender: str
    id_card: IdCard
    school_id: int
    grade_id: int
    class_id: int
    phone: Optional[str] = None

    @field_validator('gender')
    @classmethod
    def validate_gender(cls, value):
        return normalize_student_gender_value(value)

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, value):
        return normalize_optional_phone(value)


class StudentSelfPhoneIn(BaseModel):
    phone: str

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, value):
        text = str(value or '').strip()
        if not text:
            raise ValueError('请输入手机号')
        return vali_telephone(text)


class SchoolBase(BaseModel):
    school_name: str
    school_code: Optional[str] = None
    region: Optional[str] = None
    stage_types: Optional[str | list[str]] = None
    sort: int = 0
    is_active: bool = True
    leader_user_ids: list[int] = Field(default_factory=list)


class SchoolIn(SchoolBase):
    pass


class SchoolUpdate(SchoolBase):
    pass


class GradeBase(BaseModel):
    school_id: int
    grade_name: str
    grade_code: Optional[str] = None
    sort: int = 0
    is_active: bool = True
    remark: Optional[str] = None


class GradeIn(GradeBase):
    pass


class GradeUpdate(GradeBase):
    pass


class ClassBase(BaseModel):
    school_id: int
    grade_id: int
    class_name: str
    class_code: Optional[str] = None
    sort: int = 0
    is_active: bool = True
    remark: Optional[str] = None
    coach_user_ids: list[int] = Field(default_factory=list)


class ClassIn(ClassBase):
    pass


class ClassUpdate(ClassBase):
    pass

class BatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    biz_type: str
    batch_name: str
    standard_id: int
    standard_name: Optional[str] = None
    standard_version: Optional[str] = None
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
