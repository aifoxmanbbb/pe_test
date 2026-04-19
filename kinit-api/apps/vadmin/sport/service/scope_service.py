#!/usr/bin/python
# -*- coding: utf-8 -*-

from typing import Any
from sqlalchemy import select, false
from sqlalchemy.ext.asyncio import AsyncSession
from apps.vadmin.auth.models import VadminUser
from apps.vadmin.sport.models import (
    VadminPefSchool,
    VadminPefClass,
    vadmin_pef_school_leaders,
    vadmin_pef_class_coaches
)

ROLE_SCHOOL_LEADER = "school_leader"
ROLE_TEACHER_COACH = "teacher_coach"


async def get_user_sport_scope(db: AsyncSession, user: VadminUser) -> dict[str, Any]:
    role_keys = [str(getattr(role, "role_key", "") or "") for role in (user.roles or [])]
    if user.is_admin():
        return {
            "role_keys": role_keys,
            "school_ids": ["*"],
            "school_names": ["*"],
            "class_ids": ["*"],
            "class_names": ["*"]
        }

    school_rows = (await db.execute(
        select(VadminPefSchool.id, VadminPefSchool.school_name)
        .join(vadmin_pef_school_leaders, vadmin_pef_school_leaders.c.school_id == VadminPefSchool.id)
        .where(
            vadmin_pef_school_leaders.c.user_id == user.id,
            VadminPefSchool.is_delete == false()
        )
    )).all()

    class_rows = (await db.execute(
        select(VadminPefClass.id, VadminPefClass.class_name, VadminPefClass.school_id, VadminPefSchool.school_name)
        .select_from(VadminPefClass)
        .join(vadmin_pef_class_coaches, vadmin_pef_class_coaches.c.class_id == VadminPefClass.id)
        .join(VadminPefSchool, VadminPefSchool.id == VadminPefClass.school_id)
        .where(
            vadmin_pef_class_coaches.c.user_id == user.id,
            VadminPefClass.is_delete == false(),
            VadminPefSchool.is_delete == false()
        )
    )).all()

    school_ids = {int(row.id) for row in school_rows}
    school_names = {str(row.school_name) for row in school_rows if row.school_name}
    class_ids = set()
    class_names = set()
    for row in class_rows:
        class_ids.add(int(row.id))
        if row.class_name:
            class_names.add(str(row.class_name))
        if row.school_id:
            school_ids.add(int(row.school_id))
        if row.school_name:
            school_names.add(str(row.school_name))

    return {
        "role_keys": role_keys,
        "school_ids": list(school_ids),
        "school_names": list(school_names),
        "class_ids": list(class_ids),
        "class_names": list(class_names)
    }


def is_global_scope(auth) -> bool:
    return auth.data_range in (None, 4) or "*" in (auth.dept_ids or []) or "*" in (auth.school_ids or [])


def match_scope_by_name(auth, school_name: str | None, class_name: str | None) -> bool:
    if is_global_scope(auth):
        return True

    explicit_school_names = {str(item) for item in (auth.school_names or []) if item not in ("", None)}
    explicit_class_names = {str(item) for item in (auth.class_names or []) if item not in ("", None)}
    if explicit_school_names or explicit_class_names:
        school_ok = True
        class_ok = True
        if explicit_school_names and school_name is not None:
            school_ok = str(school_name) in explicit_school_names
        elif explicit_school_names and explicit_class_names:
            school_ok = False
        if explicit_class_names and class_name is not None:
            class_ok = str(class_name) in explicit_class_names
        elif explicit_class_names and explicit_school_names:
            class_ok = False
        return school_ok and class_ok

    tokens = []
    if auth.user and hasattr(auth.user, "depts"):
        for dept in auth.user.depts:
            name = getattr(dept, "name", None)
            key = getattr(dept, "dept_key", None)
            if name:
                tokens.append(str(name))
            if key:
                tokens.append(str(key))
    tokens = list(set(tokens))
    if not tokens:
        return True

    values = [str(school_name or ""), str(class_name or "")]
    return any((tk in val) or (val in tk) for tk in tokens for val in values if val)
