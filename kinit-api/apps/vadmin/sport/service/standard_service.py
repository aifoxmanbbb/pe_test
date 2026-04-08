#!/usr/bin/python
# -*- coding: utf-8 -*-

from sqlalchemy import select, false
from sqlalchemy.ext.asyncio import AsyncSession
from apps.vadmin.sport.models import VadminSportStandard, VadminSportStandardItem


async def list_standard_with_items(
        db: AsyncSession,
        biz_type: str,
        region: str | None = None,
        year: int | None = None,
        stage_type: str | None = None
) -> list[dict]:
    sql = select(VadminSportStandard).where(
        VadminSportStandard.is_delete == false(),
        VadminSportStandard.biz_type == biz_type
    )
    if region:
        sql = sql.where(VadminSportStandard.region == region)
    if year:
        sql = sql.where(VadminSportStandard.year == year)
    if stage_type:
        sql = sql.where(VadminSportStandard.stage_type == stage_type)

    sql = sql.order_by(VadminSportStandard.year.desc(), VadminSportStandard.id.desc())
    standards = (await db.scalars(sql)).all()
    if not standards:
        return []

    ids = [s.id for s in standards]
    item_sql = select(VadminSportStandardItem).where(
        VadminSportStandardItem.is_delete == false(),
        VadminSportStandardItem.standard_id.in_(ids)
    ).order_by(VadminSportStandardItem.sort.asc(), VadminSportStandardItem.id.asc())
    items = (await db.scalars(item_sql)).all()

    item_map: dict[int, list[dict]] = {}
    for it in items:
        item_map.setdefault(it.standard_id, []).append({
            'item': it.item_name,
            'gender': it.gender,
            'full': str(it.full_threshold) if it.full_threshold is not None else '-',
            'excellent': str(it.excellent_threshold) if it.excellent_threshold is not None else '-',
            'pass': str(it.pass_threshold) if it.pass_threshold is not None else '-',
            'mode': it.calc_mode
        })

    result = []
    for s in standards:
        stage_map = {
            'primary': '小学',
            'mid': '初中',
            'high': '高中',
            'university': '大学'
        }
        stage_text = stage_map.get(s.stage_type, s.stage_type)
        source_text = {
            'pdf': 'PDF识别+人工确认',
            'excel': 'Excel导入',
            'manual': '手工录入',
            'copy': '复制历史标准'
        }.get(s.source_type, s.source_type)
        result.append({
            'id': s.id,
            'name': s.name,
            'region': s.region,
            'year': s.year,
            'stage': stage_text,
            'exam_type': stage_text,
            'version': s.version,
            'status': '已发布' if s.status == 'published' else ('草稿' if s.status == 'draft' else '已作废'),
            'source': source_text,
            'ref_count': 0,
            'thresholds': item_map.get(s.id, [])
        })
    return result
