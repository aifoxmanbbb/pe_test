<script setup lang="ts">
import { computed } from 'vue'
import { ElScrollbar } from 'element-plus'
import { ThemeSwitch } from '@/components/ThemeSwitch'
import { useAppStore } from '@/store/modules/app'
import { useDesign } from '@/hooks/web/useDesign'
import { underlineToHump } from '@/utils'
import { LoginForm } from './components'
import bgLogin from '@/assets/imgs/bg-login.webp'

const { getPrefixCls } = useDesign()
const prefixCls = getPrefixCls('login')

const appStore = useAppStore()
const logo = computed(() => appStore.getLogoImage)
const title = computed(() => underlineToHump(appStore.getTitle))
</script>

<template>
  <div :class="prefixCls" class="login-stage" :style="{ '--login-image': `url(${bgLogin})` }">
    <ElScrollbar class="h-full">
      <div class="login-stage__shell">
        <div class="login-stage__topbar">
          <div class="login-stage__brand">
            <img :src="logo" alt="" class="login-stage__brand-logo" />
            <div>
              <div class="login-stage__brand-title">{{ title }}</div>
              <div class="login-stage__brand-sub">国家级体育考试与体质健康管理中枢</div>
            </div>
          </div>
<!--          <ThemeSwitch />-->
        </div>

        <div class="login-stage__content">
          <section class="login-stage__hero">
            <div class="login-stage__eyebrow">NATIONAL PHYSICAL HEALTH PLATFORM</div>
            <h1 class="login-stage__title">
              国家体质健康
              <span>达标检测中心</span>
              管理平台
            </h1>
            <p class="login-stage__desc">
              面向学校体育教学、过程管理、成绩分析与家校查询的一体化服务平台，集中支撑体考、体测、学生档案与结果应用。
            </p>
            <div class="login-stage__signals">
              <div class="login-stage__signal">
                <span>统一业务入口</span>
                <strong>覆盖体考、体测、档案与分析</strong>
              </div>
              <div class="login-stage__signal">
                <span>多角色协同使用</span>
                <strong>支持管理、教学与个人查询场景</strong>
              </div>
            </div>
          </section>

          <section class="login-stage__panel">
            <div class="login-stage__panel-head">
              <div>
                <div class="login-stage__panel-eyebrow">SECURE ACCESS</div>
                <div class="login-stage__panel-title">进入系统</div>
              </div>
<!--              <div class="login-stage__panel-note">手机号 + 密码认证</div>-->
            </div>

            <div class="login-stage__form-wrap">
              <LoginForm class="login-stage__form" />
            </div>
          </section>
        </div>
      </div>
    </ElScrollbar>
  </div>
</template>

<style lang="less" scoped>
@prefix-cls: ~'@{namespace}-login';

.login-stage {
  min-height: 100%;
  background:
    linear-gradient(90deg, rgba(5, 10, 22, 0.9), rgba(5, 10, 22, 0.38)),
    linear-gradient(180deg, rgba(56, 189, 248, 0.08), transparent 32%),
    var(--login-image) center/cover no-repeat;
  overflow: auto;
}

.login-stage__shell {
  min-height: 100vh;
  padding: 24px 28px 28px;
  backdrop-filter: blur(2px);
}

.login-stage__topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.login-stage__brand {
  display: flex;
  align-items: center;
  gap: 14px;
}

.login-stage__brand-logo {
  width: 54px;
  height: 54px;
}

.login-stage__brand-title {
  font-size: 20px;
  font-weight: 800;
  color: #f8fbff;
}

.login-stage__brand-sub {
  margin-top: 4px;
  font-size: 12px;
  letter-spacing: 0.12em;
  color: rgba(226, 232, 240, 0.72);
}

.login-stage__content {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) 460px;
  gap: 32px;
  align-items: center;
  min-height: calc(100vh - 106px);
}

.login-stage__hero {
  max-width: 760px;
  padding: 48px 0;
}

.login-stage__eyebrow,
.login-stage__panel-eyebrow {
  font-size: 12px;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  color: rgba(191, 219, 254, 0.84);
}

.login-stage__title {
  margin: 18px 0 18px;
  font-size: clamp(40px, 5vw, 78px);
  line-height: 0.98;
  font-weight: 900;
  color: #f8fbff;
  text-wrap: balance;
}

.login-stage__title span {
  display: block;
  color: #7dd3fc;
}

.login-stage__desc {
  margin: 0;
  max-width: 640px;
  font-size: 17px;
  line-height: 1.95;
  color: rgba(226, 232, 240, 0.88);
}

.login-stage__signals {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  max-width: 720px;
  margin-top: 28px;
}

.login-stage__signal {
  padding: 18px 18px 20px;
  border: 1px solid rgba(226, 232, 240, 0.12);
  background: rgba(7, 15, 30, 0.34);
  backdrop-filter: blur(16px);
}

.login-stage__signal span {
  display: block;
  color: rgba(191, 219, 254, 0.74);
  font-size: 12px;
}

.login-stage__signal strong {
  display: block;
  margin-top: 10px;
  color: #fff;
  font-size: 18px;
  line-height: 1.6;
}

.login-stage__panel {
  position: relative;
  padding: 24px 24px 20px;
  border: 1px solid rgba(226, 232, 240, 0.12);
  background:
    linear-gradient(180deg, rgba(6, 12, 24, 0.84), rgba(6, 12, 24, 0.72)),
    radial-gradient(circle at top right, rgba(56, 189, 248, 0.12), transparent 36%);
  box-shadow: 0 32px 72px rgba(15, 23, 42, 0.42);
  backdrop-filter: blur(20px);
}

.login-stage__panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.login-stage__panel-title {
  margin-top: 8px;
  font-size: 28px;
  font-weight: 800;
  color: #fff;
}

.login-stage__panel-note {
  padding: 8px 12px;
  font-size: 12px;
  letter-spacing: 0.08em;
  color: rgba(191, 219, 254, 0.84);
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(15, 23, 42, 0.46);
}

.login-stage__form-wrap {
  margin-top: 22px;
}

.login-stage__form {
  padding: 0;
}

.login-stage__form :deep(.el-form-item) {
  margin-bottom: 18px;
}

.login-stage__form :deep(.el-form-item__label) {
  color: rgba(226, 232, 240, 0.82);
  font-size: 13px;
}

.login-stage__form :deep(h2) {
  display: none;
}

.login-stage__form :deep(.el-input__wrapper) {
  min-height: 50px;
  background: rgba(15, 23, 42, 0.72);
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.18);
}

.login-stage__form :deep(.el-input__inner) {
  color: #f8fbff;
}

.login-stage__form :deep(.el-input__inner::placeholder) {
  color: rgba(191, 219, 254, 0.4);
}

.login-stage__form :deep(.el-checkbox) {
  color: rgba(226, 232, 240, 0.82);
}

.login-stage__form :deep(.el-link) {
  color: #7dd3fc;
}

.login-stage__form :deep(.el-button--primary),
.login-stage__form :deep(.base-button--primary) {
  height: 50px;
  border: 0;
  background: linear-gradient(135deg, #38bdf8, #2563eb);
  box-shadow: 0 16px 32px rgba(37, 99, 235, 0.34);
}

.login-stage__form :deep(.el-button:not(.el-button--primary)) {
  border-color: rgba(148, 163, 184, 0.22);
  background: rgba(15, 23, 42, 0.46);
  color: #e2e8f0;
}

@media (max-width: 1100px) {
  .login-stage__content {
    grid-template-columns: 1fr;
    gap: 24px;
  }

  .login-stage__hero {
    padding: 24px 0 0;
  }
}

@media (max-width: 768px) {
  .login-stage__shell {
    padding: 16px;
  }

  .login-stage__signals {
    grid-template-columns: 1fr;
  }

  .login-stage__panel-head {
    flex-direction: column;
  }
}
</style>
