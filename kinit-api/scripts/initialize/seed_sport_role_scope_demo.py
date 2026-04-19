#!/usr/bin/python
# -*- coding: utf-8 -*-

import asyncio
import json
import sys
from pathlib import Path
from sqlalchemy import select, text

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from application import settings
from core.database import session_factory
from apps.vadmin.auth.models import VadminRole, VadminMenu, VadminUser
from apps.vadmin.auth import models as auth_models
from apps.vadmin.sport.models import (
    VadminPefSchool,
    VadminPefClass,
    vadmin_pef_school_leaders,
    vadmin_pef_class_coaches
)


ROLE_SPECS = [
    {
        "name": "学校领导",
        "role_key": "school_leader",
        "order": 110,
        "desc": "学校领导角色，仅可查看编辑本校体育数据",
        "menu_perms": [
            "pe",
            "pe.analysis.overview",
            "pe.score.entry",
            "pe.analysis",
            "pe.analysis.student",
            "pe.analysis.class",
            "pe.analysis.grade",
            "pe.batch",
            "fitness",
            "fitness.analysis.overview",
            "fitness.score.entry",
            "fitness.analysis",
            "fitness.analysis.student",
            "fitness.analysis.class",
            "fitness.analysis.grade",
            "fitness.batch",
            "sport.student",
            "sport.student.scores",
            "sport.foundation",
            "sport.foundation.grade",
            "sport.foundation.class",
            "sport.foundation.student"
        ]
    },
    {
        "name": "老师教练",
        "role_key": "teacher_coach",
        "order": 120,
        "desc": "老师教练角色，仅可查看编辑关联班级体育数据",
        "menu_perms": [
            "pe",
            "pe.analysis.overview",
            "pe.score.entry",
            "pe.analysis",
            "pe.analysis.student",
            "pe.analysis.class",
            "pe.analysis.grade",
            "pe.batch",
            "fitness",
            "fitness.analysis.overview",
            "fitness.score.entry",
            "fitness.analysis",
            "fitness.analysis.student",
            "fitness.analysis.class",
            "fitness.analysis.grade",
            "fitness.batch",
            "sport.student",
            "sport.student.scores",
            "sport.foundation",
            "sport.foundation.student"
        ]
    }
]


DEMO_USERS = [
    {"telephone": "15802370001", "name": "巴蜀学校领导A", "gender": "1", "role_key": "school_leader"},
    {"telephone": "15802370003", "name": "综合学校领导B", "gender": "0", "role_key": "school_leader"},
    {"telephone": "15802370002", "name": "巴蜀老师教练A", "gender": "1", "role_key": "teacher_coach"},
    {"telephone": "15802370004", "name": "综合老师教练B", "gender": "0", "role_key": "teacher_coach"}
]


async def ensure_tables(db):
    await db.execute(text("""
        CREATE TABLE IF NOT EXISTS vadmin_pef_school_leaders (
            school_id INT NOT NULL,
            user_id INT NOT NULL,
            PRIMARY KEY (school_id, user_id),
            KEY idx_pef_school_leaders_user (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学校与校领导关联'
    """))
    await db.execute(text("""
        CREATE TABLE IF NOT EXISTS vadmin_pef_class_coaches (
            class_id INT NOT NULL,
            user_id INT NOT NULL,
            PRIMARY KEY (class_id, user_id),
            KEY idx_pef_class_coaches_user (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='班级与老师教练关联'
    """))


async def ensure_role(db, spec):
    role = await db.scalar(select(VadminRole).where(
        VadminRole.role_key == spec["role_key"],
        VadminRole.is_delete == 0
    ))
    if not role:
        role = VadminRole(
            name=spec["name"],
            role_key=spec["role_key"],
            data_range=0,
            disabled=False,
            order=spec["order"],
            desc=spec["desc"],
            is_admin=False
        )
        db.add(role)
        await db.flush()
    else:
        role.name = spec["name"]
        role.data_range = 0
        role.disabled = False
        role.order = spec["order"]
        role.desc = spec["desc"]
        role.is_admin = False

    menus = (await db.scalars(select(VadminMenu).where(
        VadminMenu.perms.in_(spec["menu_perms"]),
        VadminMenu.is_delete == 0
    ))).all()
    desired_menu_ids = sorted({menu.id for menu in menus})
    existing_menu_ids = set((await db.scalars(select(auth_models.vadmin_auth_role_menus.c.menu_id).where(
        auth_models.vadmin_auth_role_menus.c.role_id == role.id
    ))).all())
    for menu_id in desired_menu_ids:
        if menu_id not in existing_menu_ids:
            await db.execute(auth_models.vadmin_auth_role_menus.insert().values(role_id=role.id, menu_id=menu_id))
    return role


async def ensure_user(db, role_map, user_spec):
    user = await db.scalar(select(VadminUser).where(
        VadminUser.telephone == user_spec["telephone"],
        VadminUser.is_delete == 0
    ))
    if not user:
        user = VadminUser(
            avatar=settings.DEFAULT_AVATAR,
            telephone=user_spec["telephone"],
            name=user_spec["name"],
            nickname=None,
            password=VadminUser.get_password_hash("kinit2022"),
            gender=user_spec["gender"],
            is_active=True,
            is_reset_password=False,
            is_staff=True
        )
        db.add(user)
        await db.flush()
    else:
        user.name = user_spec["name"]
        user.gender = user_spec["gender"]
        user.is_active = True
        user.is_staff = True
        user.is_reset_password = False
        user.password = VadminUser.get_password_hash("kinit2022")

    role = role_map[user_spec["role_key"]]
    exists = await db.scalar(select(auth_models.vadmin_auth_user_roles.c.user_id).where(
        auth_models.vadmin_auth_user_roles.c.user_id == user.id,
        auth_models.vadmin_auth_user_roles.c.role_id == role.id
    ))
    if not exists:
        await db.execute(auth_models.vadmin_auth_user_roles.insert().values(user_id=user.id, role_id=role.id))
    return user


async def pick_schools(db):
    schools = (await db.scalars(select(VadminPefSchool).where(
        VadminPefSchool.is_delete == 0
    ).order_by(VadminPefSchool.id.asc()))).all()
    if len(schools) < 2:
        raise RuntimeError("学校数据不足，至少需要 2 所学校用于角色权限验证")

    by_name = {school.school_name: school for school in schools}
    first = by_name.get("巴蜀中学") or schools[0]
    second = by_name.get("清华中学") or next((item for item in schools if item.id != first.id), schools[1])
    return first, second


async def pick_classes(db, school_id):
    rows = (await db.scalars(select(VadminPefClass).where(
        VadminPefClass.school_id == school_id,
        VadminPefClass.is_delete == 0
    ).order_by(VadminPefClass.id.asc()))).all()
    if not rows:
        raise RuntimeError(f"学校 {school_id} 下没有班级，无法验证老师教练权限")
    return rows


async def reset_school_leaders(db, school_id, user_ids):
    await db.execute(vadmin_pef_school_leaders.delete().where(vadmin_pef_school_leaders.c.school_id == school_id))
    if user_ids:
        await db.execute(vadmin_pef_school_leaders.insert(), [
            {"school_id": school_id, "user_id": user_id} for user_id in user_ids
        ])


async def reset_class_coaches(db, class_id, user_ids):
    await db.execute(vadmin_pef_class_coaches.delete().where(vadmin_pef_class_coaches.c.class_id == class_id))
    if user_ids:
        await db.execute(vadmin_pef_class_coaches.insert(), [
            {"class_id": class_id, "user_id": user_id} for user_id in user_ids
        ])


async def main():
    async with session_factory() as db:
        async with db.begin():
            await ensure_tables(db)

            role_map = {}
            for spec in ROLE_SPECS:
                role_map[spec["role_key"]] = await ensure_role(db, spec)

            user_map = {}
            for user_spec in DEMO_USERS:
                user_map[user_spec["telephone"]] = await ensure_user(db, role_map, user_spec)

            school_a, school_b = await pick_schools(db)
            school_a_classes = await pick_classes(db, school_a.id)
            school_b_classes = await pick_classes(db, school_b.id)

            leader_a = user_map["15802370001"]
            leader_b = user_map["15802370003"]
            coach_a = user_map["15802370002"]
            coach_b = user_map["15802370004"]

            await reset_school_leaders(db, school_a.id, [leader_a.id, leader_b.id])
            await reset_school_leaders(db, school_b.id, [leader_b.id])

            target_class_a = school_a_classes[0]
            target_class_b = school_a_classes[1] if len(school_a_classes) > 1 else school_a_classes[0]
            target_class_c = school_b_classes[0]

            await reset_class_coaches(db, target_class_a.id, [coach_a.id, coach_b.id])
            await reset_class_coaches(db, target_class_b.id, [coach_a.id])
            await reset_class_coaches(db, target_class_c.id, [coach_b.id])

            target_class_a.coach_user_id = coach_a.id
            target_class_b.coach_user_id = coach_a.id
            target_class_c.coach_user_id = coach_b.id

            payload = {
                "accounts": [
                    {"role": "学校领导", "telephone": "15802370001", "password": "kinit2022", "name": leader_a.name},
                    {"role": "学校领导", "telephone": "15802370003", "password": "kinit2022", "name": leader_b.name},
                    {"role": "老师教练", "telephone": "15802370002", "password": "kinit2022", "name": coach_a.name},
                    {"role": "老师教练", "telephone": "15802370004", "password": "kinit2022", "name": coach_b.name}
                ],
                "schools": [
                    {"school_id": school_a.id, "school_name": school_a.school_name, "leader_user_ids": [leader_a.id, leader_b.id]},
                    {"school_id": school_b.id, "school_name": school_b.school_name, "leader_user_ids": [leader_b.id]}
                ],
                "classes": [
                    {"class_id": target_class_a.id, "class_name": target_class_a.class_name, "coach_user_ids": [coach_a.id, coach_b.id]},
                    {"class_id": target_class_b.id, "class_name": target_class_b.class_name, "coach_user_ids": [coach_a.id]},
                    {"class_id": target_class_c.id, "class_name": target_class_c.class_name, "coach_user_ids": [coach_b.id]}
                ]
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
