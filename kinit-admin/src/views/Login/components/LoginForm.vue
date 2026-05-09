<script setup lang="tsx">
import { nextTick, reactive, ref, watch } from 'vue'
import { Form } from '@/components/Form'
import { useI18n } from '@/hooks/web/useI18n'
import { ElButton, ElCheckbox, ElMessage } from 'element-plus'
import { useForm } from '@/hooks/web/useForm'
import { getRoleMenusApi } from '@/api/login'
import {
  getPublicClassOptionsApi,
  getPublicGradeOptionsApi,
  getPublicSchoolOptionsApi,
  registerStudentApi
} from '@/api/vadmin/sport'
import { useAuthStore } from '@/store/modules/auth'
import { usePermissionStore } from '@/store/modules/permission'
import { useRouter } from 'vue-router'
import type { RouteLocationNormalizedLoaded, RouteRecordRaw } from 'vue-router'
import { UserLoginType } from '@/api/login/types'
import { useValidator } from '@/hooks/web/useValidator'
import { FormSchema } from '@/components/Form'
import { BaseButton } from '@/components/Button'

const { required, isTelephone, isIdCard } = useValidator()

const permissionStore = usePermissionStore()

const authStore = useAuthStore()

const { currentRoute, addRoute, push } = useRouter()

const { t } = useI18n()

const remember = ref(false)
const activeMode = ref<'login' | 'register'>('login')
const registering = ref(false)
const publicSchoolOptions = ref<any[]>([])
const publicGradeOptions = ref<any[]>([])
const publicClassOptions = ref<any[]>([])

const optionalTelephone = (_rule: any, value: any, callback: (error?: Error) => void) => {
  const text = String(value ?? '').trim()
  if (!text) {
    callback()
    return
  }
  isTelephone(_rule, text, callback)
}

const rules = {
  telephone: [required()],
  method: [required()],
  password: [required()]
}

const schema = reactive<FormSchema[]>([
  {
    field: 'title',
    colProps: {
      span: 24
    },
    formItemProps: {
      slots: {
        default: () => {
          return <h2 class="text-2xl font-bold text-center w-[100%]">{t('login.login')}</h2>
        }
      }
    }
  },
  {
    field: 'telephone',
    label: '手机号/身份证号',
    value: '',
    component: 'Input',
    colProps: {
      span: 24
    },
    componentProps: {
      style: {
        width: '100%'
      },
      placeholder: '请输入手机号或身份证号',
      maxlength: 18
    }
  },
  {
    field: 'password',
    label: t('login.password'),
    value: '',
    component: 'InputPassword',
    colProps: {
      span: 24
    },
    componentProps: {
      style: {
        width: '100%'
      },
      placeholder: t('login.passwordPlaceholder')
    }
  },
  {
    field: 'method',
    label: '登录类型',
    value: '0',
    component: 'Input',
    hidden: true
  },
  {
    field: 'tool',
    colProps: {
      span: 24
    },
    formItemProps: {
      slots: {
        default: () => {
          return (
            <>
              <div class="flex justify-between items-center w-[100%]">
                <ElCheckbox v-model={remember.value} label={t('login.remember')} size="small" />
                <span
                  class="login-switch-text"
                  style={{ color: '#fff' }}
                  tabindex="0"
                  onClick={openRegisterPanel}
                  onKeydown={(event: KeyboardEvent) => {
                    if (event.key === 'Enter' || event.key === ' ') openRegisterPanel()
                  }}
                >
                  学生自主注册
                </span>
              </div>
            </>
          )
        }
      }
    }
  },
  {
    field: 'login',
    colProps: {
      span: 24
    },
    formItemProps: {
      slots: {
        default: () => {
          return (
            <>
              <div class="w-[100%]">
                <BaseButton
                  loading={loading.value}
                  type="primary"
                  class="w-[100%]"
                  onClick={signIn}
                >
                  {t('login.login')}
                </BaseButton>
              </div>
            </>
          )
        }
      }
    }
  }
])

const { formRegister, formMethods } = useForm()
const { formRegister: registerFormRegister, formMethods: registerFormMethods } = useForm()
const { getFormData, getElFormExpose } = formMethods
const loading = ref(false)
const redirect = ref<string>('')

const registerSchema = reactive<FormSchema[]>([
  { field: 'name', label: '姓名', component: 'Input', componentProps: { placeholder: '请输入姓名' } },
  {
    field: 'id_card',
    label: '身份证',
    component: 'Input',
    componentProps: { maxlength: 18, placeholder: '请输入学生身份证号' }
  },
  {
    field: 'gender',
    label: '性别',
    component: 'Select',
    value: 'male',
    componentProps: {
      options: [
        { label: '男', value: 'male' },
        { label: '女', value: 'female' }
      ]
    }
  },
  {
    field: 'phone',
    label: '手机号',
    component: 'Input',
    componentProps: { maxlength: 11, placeholder: '选填，后续可用手机号登录' }
  },
  {
    field: 'school_id',
    label: '学校',
    component: 'Select',
    componentProps: {
      options: publicSchoolOptions,
      filterable: true,
      onChange: async (val: number) => {
        publicGradeOptions.value = []
        publicClassOptions.value = []
        registerFormMethods.setValues({ grade_id: null, class_id: null })
        const res = await getPublicGradeOptionsApi({ school_id: val }).catch(() => null)
        publicGradeOptions.value = res?.data || []
      }
    }
  },
  {
    field: 'grade_id',
    label: '年级',
    component: 'Select',
    componentProps: {
      options: publicGradeOptions,
      filterable: true,
      onChange: async (val: number) => {
        publicClassOptions.value = []
        registerFormMethods.setValues({ class_id: null })
        const data = await registerFormMethods.getFormData()
        const res = await getPublicClassOptionsApi({
          school_id: data.school_id,
          grade_id: val
        }).catch(() => null)
        publicClassOptions.value = res?.data || []
      }
    }
  },
  {
    field: 'class_id',
    label: '班级',
    component: 'Select',
    componentProps: { options: publicClassOptions, filterable: true }
  }
])

const registerRules = reactive({
  name: [required()],
  id_card: [required(), { validator: isIdCard, trigger: 'blur' }],
  gender: [required()],
  phone: [{ validator: optionalTelephone, trigger: 'blur' }],
  school_id: [required()],
  grade_id: [required()],
  class_id: [required()]
})

watch(
  () => currentRoute.value,
  (route: RouteLocationNormalizedLoaded) => {
    redirect.value = route?.query?.redirect as string
  },
  {
    immediate: true
  }
)

// 登录
const openRegisterPanel = async () => {
  activeMode.value = 'register'
  publicSchoolOptions.value = []
  publicGradeOptions.value = []
  publicClassOptions.value = []
  const res = await getPublicSchoolOptionsApi().catch(() => null)
  publicSchoolOptions.value = res?.data || []
  await nextTick()
  registerFormMethods.setValues({
    name: '',
    id_card: '',
    gender: 'male',
    phone: '',
    school_id: null,
    grade_id: null,
    class_id: null
  })
}

const backToLogin = () => {
  activeMode.value = 'login'
}

const submitRegister = async () => {
  const elForm = await registerFormMethods.getElFormExpose()
  const valid = await elForm?.validate()
  if (!valid) return
  registering.value = true
  const data = await registerFormMethods.getFormData()
  const res = await registerStudentApi(data).catch(() => null)
  registering.value = false
  if (res) {
    ElMessage.success(res.message || '注册成功，默认密码为身份证后8位')
    formMethods.setValues({ telephone: data.id_card, password: '' })
    activeMode.value = 'login'
  }
}

const signIn = async () => {
  const elForm = await getElFormExpose()
  const valid = await elForm?.validate()
  if (valid) {
    loading.value = true
    const formData: UserLoginType = await getFormData()
    try {
      const res = await authStore.login(formData)
      if (res) {
        if (!res.data.is_reset_password) {
          // 重置密码
          push({ path: '/reset/password' })
        } else {
          // 获取动态路由
          getMenu()
        }
      } else {
        loading.value = false
      }
    } catch (e: any) {
      loading.value = false
    }
  }
}

// 获取用户菜单信息
const getMenu = async () => {
  const res = await getRoleMenusApi()
  if (res) {
    const routers = res.data || []
    await permissionStore.generateRoutes(routers).catch(() => {})
    permissionStore.getAddRouters.forEach((route) => {
      addRoute(route as RouteRecordRaw) // 动态添加可访问路由表
    })
    permissionStore.setIsAddRouters(true)
    push({ path: redirect.value || '/home' })
  }
}

</script>

<template>
  <div class="auth-switch-card" :class="{ 'is-register': activeMode === 'register' }">
    <Transition name="auth-slide" mode="out-in">
      <div v-if="activeMode === 'login'" key="login" class="auth-pane">
        <Form
          :schema="schema"
          :rules="rules"
          label-position="top"
          hide-required-asterisk
          size="large"
          class="dark:(border-1 border-[var(--el-border-color)] border-solid)"
          @register="formRegister"
        />
      </div>

      <div v-else key="register" class="auth-pane auth-register">
        <div class="auth-register__head">
          <div>
            <div class="auth-register__eyebrow">STUDENT ACCESS</div>
            <h3>学生自主注册</h3>
            <p>完成身份与班级信息登记后，使用身份证号和默认密码登录录入成绩。</p>
          </div>
          <ElButton link class="auth-register__back" @click="backToLogin">返回登录</ElButton>
        </div>

        <Form
          :schema="registerSchema"
          :rules="registerRules"
          label-position="top"
          hide-required-asterisk
          size="large"
          class="auth-register__form"
          @register="registerFormRegister"
        />

        <div class="auth-register__actions">
          <ElButton class="auth-register__ghost" @click="backToLogin">已有账号，去登录</ElButton>
          <ElButton type="primary" class="auth-register__submit" :loading="registering" @click="submitRegister">
            提交注册
          </ElButton>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.auth-switch-card {
  position: relative;
}

.auth-pane {
  width: 100%;
}

.login-switch-text {
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  text-shadow: 0 1px 12px rgba(125, 211, 252, 0.28);
  user-select: none;
}

.login-switch-text:hover,
.login-switch-text:focus-visible {
  color: #e0f2fe;
  outline: none;
  text-decoration: underline;
  text-underline-offset: 4px;
}

.auth-slide-enter-active,
.auth-slide-leave-active {
  transition:
    opacity 0.22s ease,
    transform 0.22s ease;
}

.auth-slide-enter-from {
  opacity: 0;
  transform: translateX(18px);
}

.auth-slide-leave-to {
  opacity: 0;
  transform: translateX(-18px);
}

.auth-register {
  padding-top: 2px;
}

.auth-register__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 18px;
  padding: 16px 16px 14px;
  border: 1px solid rgba(125, 211, 252, 0.16);
  border-radius: 22px;
  background:
    radial-gradient(circle at 12% 12%, rgba(56, 189, 248, 0.2), transparent 38%),
    linear-gradient(135deg, rgba(15, 23, 42, 0.92), rgba(8, 47, 73, 0.52));
}

.auth-register__eyebrow {
  font-size: 11px;
  letter-spacing: 0.18em;
  color: rgba(125, 211, 252, 0.78);
}

.auth-register__head h3 {
  margin: 7px 0 6px;
  font-size: 24px;
  line-height: 1.15;
  font-weight: 900;
  color: #f8fbff;
}

.auth-register__head p {
  margin: 0;
  max-width: 310px;
  font-size: 13px;
  line-height: 1.7;
  color: rgba(226, 232, 240, 0.72);
}

.auth-register__back {
  flex: 0 0 auto;
  margin-top: -2px;
  color: #7dd3fc;
}

.auth-register__form :deep(.el-form-item) {
  margin-bottom: 14px;
}

.auth-register__actions {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  gap: 12px;
  margin-top: 4px;
}

.auth-register__actions .el-button {
  width: 100%;
  height: 48px;
  margin-left: 0;
  border-radius: 999px;
}

.auth-register__submit {
  border: 0;
  background: linear-gradient(135deg, #38bdf8, #2563eb);
  box-shadow: 0 16px 32px rgba(37, 99, 235, 0.34);
}

.auth-register__ghost {
  border-color: rgba(148, 163, 184, 0.22);
  background: rgba(15, 23, 42, 0.46);
  color: #e2e8f0;
}

@media (max-width: 520px) {
  .auth-switch-card.is-register {
    max-height: calc(100dvh - 178px);
    overflow-y: auto;
    overscroll-behavior: contain;
    -webkit-overflow-scrolling: touch;
    padding-right: 2px;
    padding-bottom: calc(8px + env(safe-area-inset-bottom));
  }

  .auth-register__head {
    flex-direction: column;
    gap: 8px;
    padding: 14px;
  }

  .auth-register__actions {
    grid-template-columns: 1fr;
  }
}
</style>
