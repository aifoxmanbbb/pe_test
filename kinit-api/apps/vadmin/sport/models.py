#!/usr/bin/python
# -*- coding: utf-8 -*-

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, BigInteger, Date, DateTime, DECIMAL, Boolean, ForeignKey, JSON
from db.db_base import BaseModel

class VadminSportStandard(BaseModel):
    __tablename__ = "vadmin_pef_standard"
    __table_args__ = ({'comment': '体考/体测标准主表'})

    biz_type: Mapped[str] = mapped_column(String(16), index=True, nullable=False, comment="业务类型：pe=体考,fitness=体测")
    name: Mapped[str] = mapped_column(String(120), nullable=False, comment="标准名称")
    region: Mapped[str] = mapped_column(String(64), nullable=False, comment="地区")
    year: Mapped[int] = mapped_column(Integer, nullable=False, comment="年份")
    stage_type: Mapped[str] = mapped_column(String(16), nullable=False, comment="学段：primary,mid,high,university")
    version: Mapped[str] = mapped_column(String(32), nullable=False, comment="标准版本号")
    status: Mapped[str] = mapped_column(String(16), default="draft", comment="状态：draft,published,void")
    source_type: Mapped[str] = mapped_column(String(16), default="manual", comment="来源")
    conflict_policy: Mapped[str] = mapped_column(String(32), default="lower_priority", comment="规则冲突策略")
    remark: Mapped[str | None] = mapped_column(String(255), comment="备注")


class VadminSportStandardItem(BaseModel):
    __tablename__ = "vadmin_pef_standard_item"
    __table_args__ = ({'comment': '体考/体测标准项目明细'})

    standard_id: Mapped[int] = mapped_column(Integer, ForeignKey("vadmin_pef_standard.id", ondelete='CASCADE'), nullable=False)
    item_code: Mapped[str] = mapped_column(String(64), nullable=False, comment="项目编码")
    item_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="项目名称")
    gender: Mapped[str] = mapped_column(String(8), default="all", comment="性别：male,female,all")
    calc_mode: Mapped[str] = mapped_column(String(16), default="segment", comment="计分模式")
    pass_threshold: Mapped[float | None] = mapped_column(DECIMAL(10, 3))
    excellent_threshold: Mapped[float | None] = mapped_column(DECIMAL(10, 3))
    full_threshold: Mapped[float | None] = mapped_column(DECIMAL(10, 3))
    segment_json: Mapped[dict | None] = mapped_column(JSON, comment="分值段JSON")
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    is_gate_item: Mapped[bool] = mapped_column(Boolean, default=False)
    max_score: Mapped[float] = mapped_column(DECIMAL(10, 3), default=0.0)
    sort: Mapped[int] = mapped_column(Integer, default=0)


class VadminSportBatch(BaseModel):
    __tablename__ = "vadmin_pef_batch"
    __table_args__ = ({'comment': '体考/体测批次表'})

    biz_type: Mapped[str] = mapped_column(String(16), index=True, nullable=False, comment="业务类型 pe/fitness")
    batch_name: Mapped[str] = mapped_column(String(120), nullable=False, comment="批次名称")
    standard_id: Mapped[int] = mapped_column(Integer, ForeignKey("vadmin_pef_standard.id"), nullable=False)
    school_name: Mapped[str] = mapped_column(String(120), nullable=False, comment="学校")
    grade_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="年级")
    class_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="班级")
    stage_type: Mapped[str] = mapped_column(String(16), comment="学段")
    start_date: Mapped[str | None] = mapped_column(Date, comment="开始日期")
    end_date: Mapped[str | None] = mapped_column(Date, comment="结束日期")
    status: Mapped[str] = mapped_column(String(16), default="draft", comment="状态：draft,ongoing,finished")
    remark: Mapped[str | None] = mapped_column(String(255), comment="备注")


class VadminSportScore(BaseModel):
    __tablename__ = "vadmin_pef_score"
    __table_args__ = ({'comment': '体考/体测成绩明细表'})

    biz_type: Mapped[str] = mapped_column(String(16), index=True, nullable=False, comment="业务类型 pe/fitness")
    batch_id: Mapped[int] = mapped_column(Integer, ForeignKey("vadmin_pef_batch.id", ondelete='CASCADE'), nullable=False)
    student_no: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="学号")
    student_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False, comment="学生姓名")
    gender: Mapped[str] = mapped_column(String(8), nullable=False, comment="性别")
    mobile: Mapped[str | None] = mapped_column(String(32), comment="联系方式")
    school_name: Mapped[str] = mapped_column(String(120), nullable=False, comment="学校")
    grade_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="年级")
    class_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="班级")
    item_code: Mapped[str] = mapped_column(String(64), nullable=False, comment="项目编码")
    item_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="项目名称")
    raw_score: Mapped[float | None] = mapped_column(DECIMAL(10, 3), comment="成绩")
    score_value: Mapped[float | None] = mapped_column(DECIMAL(10, 3), comment="分值")
    is_pass: Mapped[bool | None] = mapped_column(Boolean, comment="是否及格")
    is_excellent: Mapped[bool | None] = mapped_column(Boolean, comment="是否优秀")
    is_full: Mapped[bool | None] = mapped_column(Boolean, comment="是否满分")
    teacher_comment: Mapped[str | None] = mapped_column(String(255), comment="老师评语")
    test_date: Mapped[str | None] = mapped_column(Date, comment="测试日期")


class VadminPefSchool(BaseModel):
    __tablename__ = "vadmin_pef_school"
    __table_args__ = ({'comment': '体考体测-学校'})

    school_name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, comment="学校名称")
    school_code: Mapped[str | None] = mapped_column(String(50), comment="学校代码")
    region: Mapped[str | None] = mapped_column(String(100), comment="所属地区")
    stage_types: Mapped[str | None] = mapped_column(String(64), comment="学段集合：primary,mid,high,university")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")


class VadminPefGrade(BaseModel):
    __tablename__ = "vadmin_pef_grade"
    __table_args__ = ({'comment': '体考体测-年级'})

    school_id: Mapped[int] = mapped_column(Integer, ForeignKey("vadmin_pef_school.id"), nullable=False, comment="所属学校ID")
    grade_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="年级名称")
    grade_code: Mapped[str | None] = mapped_column(String(50), comment="年级编码")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    remark: Mapped[str | None] = mapped_column(String(255), comment="备注")


class VadminPefClass(BaseModel):
    __tablename__ = "vadmin_pef_class"
    __table_args__ = ({'comment': '体考体测-班级'})

    school_id: Mapped[int] = mapped_column(Integer, ForeignKey("vadmin_pef_school.id"), nullable=False, comment="所属学校ID")
    grade_id: Mapped[int] = mapped_column(Integer, ForeignKey("vadmin_pef_grade.id"), nullable=False, comment="年级ID")
    class_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="班级名称")
    class_code: Mapped[str | None] = mapped_column(String(50), unique=True, comment="班级编码")
    coach_user_id: Mapped[int | None] = mapped_column(Integer, comment="主教练用户ID")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    remark: Mapped[str | None] = mapped_column(String(255), comment="备注")


class VadminPefStudent(BaseModel):
    __tablename__ = "vadmin_pef_student"
    __table_args__ = ({'comment': '体考体测-学生花名册'})

    student_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, comment="学号")
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="姓名")
    gender: Mapped[str] = mapped_column(String(8), nullable=False, comment="性别")
    birthday: Mapped[str | None] = mapped_column(Date, comment="出生日期")
    school_id: Mapped[int] = mapped_column(Integer, ForeignKey("vadmin_pef_school.id"), nullable=False, comment="所属学校ID")
    grade_id: Mapped[int] = mapped_column(Integer, ForeignKey("vadmin_pef_grade.id"), nullable=False, comment="年级ID")
    class_id: Mapped[int] = mapped_column(Integer, ForeignKey("vadmin_pef_class.id"), nullable=False, comment="班级ID")
    user_id: Mapped[int | None] = mapped_column(Integer, comment="关联用户ID")
    phone: Mapped[str | None] = mapped_column(String(20), comment="联系电话")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    remark: Mapped[str | None] = mapped_column(String(255), comment="备注")
