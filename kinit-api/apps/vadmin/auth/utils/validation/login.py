#!/usr/bin/python
# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2022/11/9 10:15 
# @File           : login.py
# @IDE            : PyCharm
# @desc           : 登录验证装饰器

from fastapi import Request
from pydantic import BaseModel, field_validator
from sqlalchemy import select, func, false
from sqlalchemy.ext.asyncio import AsyncSession
from application.settings import DEFAULT_AUTH_ERROR_MAX_NUMBER, DEMO, REDIS_DB_ENABLE
from apps.vadmin.auth import crud, schemas
from apps.vadmin.sport.models import VadminPefStudent
from core.database import redis_getter
from core.validator import vali_id_card, vali_telephone
from utils.count import Count


class LoginForm(BaseModel):
    telephone: str
    password: str
    method: str = '0'  # 认证方式，0：密码登录，1：短信登录，2：微信一键登录
    platform: str = '0'  # 登录平台，0：PC端管理系统，1：移动端管理系统

    # 重用验证器：https://docs.pydantic.dev/dev-v2/usage/validators/#reuse-validators
    @field_validator('telephone')
    @classmethod
    def normalize_login_account(cls, value):
        text = str(value or '').strip()
        if not text:
            raise ValueError("请输入手机号或身份证号")
        return text


class WXLoginForm(BaseModel):
    telephone: str | None = None
    code: str
    method: str = '2'  # 认证方式，0：密码登录，1：短信登录，2：微信一键登录
    platform: str = '1'  # 登录平台，0：PC端管理系统，1：移动端管理系统


class LoginResult(BaseModel):
    status: bool | None = False
    user: schemas.UserPasswordOut | None = None
    msg: str | None = None

    class Config:
        arbitrary_types_allowed = True


async def has_login_permission(db: AsyncSession, user) -> bool:
    if user.is_staff:
        return True
    role_count = await db.scalar(
        select(func.count())
        .select_from(crud.models.vadmin_auth_user_roles)
        .join(crud.models.VadminRole, crud.models.VadminRole.id == crud.models.vadmin_auth_user_roles.c.role_id)
        .where(
            crud.models.vadmin_auth_user_roles.c.user_id == user.id,
            crud.models.VadminRole.disabled == false(),
            crud.models.VadminRole.is_delete == false()
        )
    )
    return bool(role_count)


async def resolve_login_user(db: AsyncSession, account: str):
    text = str(account or '').strip()
    if not text:
        return None

    user = await crud.UserDal(db).get_data(telephone=text, v_return_none=True)
    if user:
        return user

    try:
        id_card = vali_id_card(text)
    except ValueError:
        return None

    student = await db.scalar(select(VadminPefStudent).where(
        VadminPefStudent.id_card == id_card,
        VadminPefStudent.is_delete == false()
    ).order_by(VadminPefStudent.id.desc()))
    if not student or not student.user_id:
        return None
    return await crud.UserDal(db).get_data(id=student.user_id, v_return_none=True)


class LoginValidation:

    """
    验证用户登录时提交的数据是否有效
    """

    def __init__(self, func):
        self.func = func

    async def __call__(self, data: LoginForm, db: AsyncSession, request: Request) -> LoginResult:
        self.result = LoginResult()
        if data.platform not in ["0", "1"] or data.method not in ["0", "1"]:
            self.result.msg = "无效参数"
            return self.result
        if data.method == "1":
            try:
                data.telephone = vali_telephone(data.telephone)
            except ValueError:
                self.result.msg = "请输入正确手机号"
                return self.result
        user = await resolve_login_user(db, data.telephone)
        if not user:
            self.result.msg = "该账号不存在！"
            return self.result

        result = await self.func(self, data=data, user=user, request=request)

        if REDIS_DB_ENABLE:
            count_key = f"{data.telephone}_password_auth" if data.method == '0' else f"{data.telephone}_sms_auth"
            count = Count(redis_getter(request), count_key)
        else:
            count = None

        if not result.status:
            self.result.msg = result.msg
            if not DEMO and count:
                number = await count.add(ex=86400)
                if number >= DEFAULT_AUTH_ERROR_MAX_NUMBER:
                    await count.reset()
                    # 如果等于最大次数，那么就将用户 is_active=False
                    user.is_active = False
                    await db.flush()
        elif not user.is_active:
            self.result.msg = "此账号已被冻结！"
        elif data.platform in ["0", "1"] and not await has_login_permission(db, user):
            self.result.msg = "此账号无权限！"
        else:
            if not DEMO and count:
                await count.delete()
            self.result.msg = "OK"
            self.result.status = True
            self.result.user = schemas.UserPasswordOut.model_validate(user)
            await crud.UserDal(db).update_login_info(user, request.client.host)
        return self.result
