#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any, Iterable

from sqlalchemy import false, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.vadmin.auth.models.dept import VadminDept
from apps.vadmin.sport.models import VadminSportBatch, VadminSportScore, VadminSportStandardItem


from utils.excel.write_xlsx import WriteXlsx


def to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def round2(value: float) -> float:
    return round(float(value), 2)


def avg(values: Iterable[float]) -> float:
    nums = [float(v) for v in values if v is not None]
    if not nums:
        return 0.0
    return round2(sum(nums) / len(nums))


def pct(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round2((numerator * 100.0) / denominator)


async def resolve_dept_filter_names(
        db: AsyncSession,
        school_id: int | None = None,
        grade_id: int | None = None,
        class_id: int | None = None,
        school_name: str | None = None,
        grade_name: str | None = None,
        class_name: str | None = None
) -> tuple[str | None, str | None, str | None]:
    async def _name_by_id(dept_id: int | None) -> str | None:
        if not dept_id:
            return None
        row = await db.get(VadminDept, int(dept_id))
        if not row or bool(row.is_delete):
            return None
        return row.name

    if not school_name:
        school_name = await _name_by_id(school_id)
    if not grade_name:
        grade_name = await _name_by_id(grade_id)
    if not class_name:
        class_name = await _name_by_id(class_id)
    return school_name, grade_name, class_name


async def list_batches(
        db: AsyncSession,
        biz_type: str,
        stage_type: str | None = None,
        batch_id: int | None = None,
        school_name: str | None = None,
        grade_name: str | None = None,
        class_name: str | None = None,
        limit: int | None = None
) -> list[VadminSportBatch]:
    sql = select(VadminSportBatch).where(
        VadminSportBatch.is_delete == false(),
        VadminSportBatch.biz_type == biz_type
    )
    if batch_id:
        sql = sql.where(VadminSportBatch.id == batch_id)
    if stage_type:
        sql = sql.where(VadminSportBatch.stage_type == stage_type)
    if school_name:
        sql = sql.where(VadminSportBatch.school_name == school_name)
    if grade_name:
        sql = sql.where(VadminSportBatch.grade_name == grade_name)
    if class_name:
        sql = sql.where(VadminSportBatch.class_name == class_name)

    sql = sql.order_by(VadminSportBatch.id.desc())
    if limit and limit > 0:
        sql = sql.limit(limit)
    return (await db.scalars(sql)).all()


async def list_scores(
        db: AsyncSession,
        biz_type: str,
        batch_ids: list[int],
        school_name: str | None = None,
        grade_name: str | None = None,
        class_name: str | None = None,
        student_no: str | None = None,
        student_keyword: str | None = None
) -> list[VadminSportScore]:
    if not batch_ids:
        return []

    sql = select(VadminSportScore).where(
        VadminSportScore.is_delete == false(),
        VadminSportScore.biz_type == biz_type,
        VadminSportScore.batch_id.in_(batch_ids)
    )
    if school_name:
        sql = sql.where(VadminSportScore.school_name == school_name)
    if grade_name:
        sql = sql.where(VadminSportScore.grade_name == grade_name)
    if class_name:
        sql = sql.where(VadminSportScore.class_name == class_name)
    if student_no:
        sql = sql.where(VadminSportScore.student_no == student_no)

    rows = (await db.scalars(sql.order_by(VadminSportScore.batch_id.asc(), VadminSportScore.id.asc()))).all()
    if student_keyword:
        kw = str(student_keyword).strip()
        if kw:
            rows = [
                r for r in rows
                if kw in (r.student_no or '')
                or kw in (r.student_name or '')
                or kw in (r.mobile or '')
            ]
    return rows


async def get_standard_item_thresholds(db: AsyncSession, standard_id: int | None) -> dict[str, dict[str, float]]:
    if not standard_id:
        return {}
    sql = select(VadminSportStandardItem).where(
        VadminSportStandardItem.is_delete == false(),
        VadminSportStandardItem.standard_id == standard_id
    ).order_by(VadminSportStandardItem.sort.asc(), VadminSportStandardItem.id.asc())
    rows = (await db.scalars(sql)).all()
    result: dict[str, dict[str, float]] = {}
    for row in rows:
        result[row.item_code] = {
            'pass': to_float(row.pass_threshold),
            'excellent': to_float(row.excellent_threshold),
            'full': to_float(row.full_threshold),
            'max': to_float(row.max_score)
        }
    return result


def group_scores_by_student(rows: list[VadminSportScore]) -> dict[str, list[VadminSportScore]]:
    result: dict[str, list[VadminSportScore]] = defaultdict(list)
    for row in rows:
        result[row.student_no].append(row)
    return result


def group_scores_by_batch(rows: list[VadminSportScore]) -> dict[int, list[VadminSportScore]]:
    result: dict[int, list[VadminSportScore]] = defaultdict(list)
    for row in rows:
        result[row.batch_id].append(row)
    return result


def group_scores_by_batch_student(rows: list[VadminSportScore]) -> dict[tuple[int, str], list[VadminSportScore]]:
    result: dict[tuple[int, str], list[VadminSportScore]] = defaultdict(list)
    for row in rows:
        result[(row.batch_id, row.student_no)].append(row)
    return result


def group_scores_by_class(rows: list[VadminSportScore]) -> dict[tuple[str, str], list[VadminSportScore]]:
    result: dict[tuple[str, str], list[VadminSportScore]] = defaultdict(list)
    for row in rows:
        result[(row.school_name, row.class_name)].append(row)
    return result


def group_scores_by_grade_class(rows: list[VadminSportScore]) -> dict[str, list[VadminSportScore]]:
    result: dict[str, list[VadminSportScore]] = defaultdict(list)
    for row in rows:
        result[row.class_name].append(row)
    return result


def student_total_score(rows: list[VadminSportScore]) -> float:
    return round2(sum(to_float(r.score_value) for r in rows))


def classify_total(total_score: float, pass_line: float, excellent_line: float, full_line: float) -> dict[str, bool]:
    return {
        'is_pass': total_score >= pass_line,
        'is_excellent': total_score >= excellent_line,
        'is_full': total_score >= full_line
    }


def first_or_none(rows: list[Any]) -> Any | None:
    return rows[0] if rows else None


def pick_items_by_keywords(
        rows: list[VadminSportScore],
        slot_keywords: dict[str, list[str]],
        fallback_size: int
) -> dict[str, str]:
    item_order: list[str] = []
    item_name_map: dict[str, str] = {}
    count_map: dict[str, int] = defaultdict(int)

    for row in rows:
        if row.item_code not in item_name_map:
            item_name_map[row.item_code] = row.item_name
            item_order.append(row.item_code)
        count_map[row.item_code] += 1

    sorted_codes = sorted(item_name_map.keys(), key=lambda c: (-count_map[c], item_order.index(c)))

    result: dict[str, str] = {}
    used: set[str] = set()

    for slot, keywords in slot_keywords.items():
        target = None
        for code in sorted_codes:
            if code in used:
                continue
            name = item_name_map.get(code, '')
            text = f"{code} {name}".lower()
            if any(k.lower() in text for k in keywords):
                target = code
                break
        if target:
            result[slot] = target
            used.add(target)

    for code in sorted_codes:
        if len(result) >= fallback_size:
            break
        if code in used:
            continue
        slot = f'item_{len(result) + 1}'
        result[slot] = code
        used.add(code)

    return result


def format_score(value: float | int | str | None, suffix: str = '') -> str:
    if value is None or value == '':
        return '-'
    if isinstance(value, str):
        return value
    num = to_float(value)
    if abs(num - int(num)) < 1e-6:
        return f"{int(num)}{suffix}"
    return f"{round2(num)}{suffix}"


def build_rate_text(pass_rate: float, excellent_rate: float, full_rate: float) -> str:
    return f"及格{round2(pass_rate)}% / 优秀{round2(excellent_rate)}% / 满分{round2(full_rate)}%"


def export_scores_to_excel(rows: list[VadminSportScore], filename: str) -> str:
    if not rows:
        return ""

    # 获取所有项目
    item_map: dict[str, str] = {}
    for r in rows:
        item_map.setdefault(r.item_code, r.item_name)
    
    item_codes = sorted(item_map.keys())
    
    headers = ["学生姓名", "学号", "性别", "学校", "年级", "班级"]
    for code in item_codes:
        name = item_map[code]
        headers.append(f"{name}(成绩)")
        headers.append(f"{name}(分值)")
    headers.append("总分")

    # 按学生分组
    student_groups = group_scores_by_student(rows)
    
    excel_rows = []
    for student_no, s_rows in student_groups.items():
        first = s_rows[0]
        row_data = [
            first.student_name,
            first.student_no,
            first.gender,
            first.school_name,
            first.grade_name,
            first.class_name
        ]
        
        s_item_map = {r.item_code: r for r in s_rows}
        total_score = 0.0
        for code in item_codes:
            ir = s_item_map.get(code)
            if ir:
                row_data.append(format_score(ir.raw_score))
                row_data.append(to_float(ir.score_value))
                total_score += to_float(ir.score_value)
            else:
                row_data.append("-")
                row_data.append(0.0)
        
        row_data.append(round2(total_score))
        excel_rows.append(row_data)

    writer = WriteXlsx()
    writer.create_excel(file_path=filename, save_static=True)
    
    # 转换为 dict 结构的 headers
    header_dicts = [{"label": h} for h in headers]
    writer.generate_template(header_dicts)
    writer.write_list(excel_rows)
    writer.close()
    
    return writer.get_file_url()
