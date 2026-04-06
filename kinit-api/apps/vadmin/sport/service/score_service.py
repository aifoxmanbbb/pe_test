#!/usr/bin/python
# -*- coding: utf-8 -*-

from sqlalchemy import select, false
from sqlalchemy.ext.asyncio import AsyncSession
from apps.vadmin.sport.models import VadminSportBatch, VadminSportScore


async def get_latest_batch(db: AsyncSession, biz_type: str, stage_type: str | None = None) -> VadminSportBatch | None:
    sql = select(VadminSportBatch).where(
        VadminSportBatch.is_delete == false(),
        VadminSportBatch.biz_type == biz_type
    )
    if stage_type:
        sql = sql.where(VadminSportBatch.stage_type == stage_type)
    sql = sql.order_by(VadminSportBatch.id.desc()).limit(1)
    return (await db.scalars(sql)).first()


async def get_batch_scores(db: AsyncSession, batch_id: int, biz_type: str) -> list[VadminSportScore]:
    sql = select(VadminSportScore).where(
        VadminSportScore.is_delete == false(),
        VadminSportScore.batch_id == batch_id,
        VadminSportScore.biz_type == biz_type
    ).order_by(VadminSportScore.id.asc())
    return (await db.scalars(sql)).all()

