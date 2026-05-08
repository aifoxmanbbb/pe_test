<script setup lang="tsx">
import { nextTick, reactive, ref, watch } from 'vue'
import { Form } from '@/components/Form'
import { useI18n } from '@/hooks/web/useI18n'
import { ElButton, ElCheckbox, ElDialog, ElMessage } from 'element-plus'
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

const { required, isTelephone } = useValidator()

const permissionStore = usePermissionStore()

const authStore = useAuthStore()

const { currentRoute, addRoute, push } = useRouter()

const { t } = useI18n()

const remember = ref(false)
const registerVisible = ref(false)
const registering = ref(false)
const publicSchoolOptions = ref<any[]>([])
const publicGradeOptions = ref<any[]>([])
const publicClassOptions = ref<any[]>([])

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
    label: t('login.telephone'),
    value: '',
    component: 'Input',
    colProps: {
      span: 24
    },
    componentProps: {
      style: {
        width: '100%'
      },
      placeholder: t('login.telephonePlaceholder'),
      maxlength: 11
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
                <ElButton link type="primary" onClick={openRegisterDialog}>
                  学生自主注册
                </ElButton>
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
  { field: 'student_no', label: '学号', component: 'Input', componentProps: { placeholder: '请输入学号' } },
  { field: 'name', label: '姓名', component: 'Input', componentProps: { placeholder: '请输入姓名' } },
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
    componentProps: { maxlength: 11, placeholder: '请输入登录手机号' }
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
  student_no: [required()],
  name: [required()],
  gender: [required()],
  phone: [required(), { validator: isTelephone, trigger: 'blur' }],
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
const openRegisterDialog = async () => {
  registerVisible.value = true
  publicSchoolOptions.value = []
  publicGradeOptions.value = []
  publicClassOptions.value = []
  const res = await getPublicSchoolOptionsApi().catch(() => null)
  publicSchoolOptions.value = res?.data || []
  await nextTick()
  registerFormMethods.setValues({
    student_no: '',
    name: '',
    gender: 'male',
    phone: '',
    school_id: null,
    grade_id: null,
    class_id: null
  })
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
    ElMessage.success(res.message || '注册成功，默认密码为手机号后8位')
    registerVisible.value = false
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
  <Form
    :schema="schema"
    :rules="rules"
    label-position="top"
    hide-required-asterisk
    size="large"
    class="dark:(border-1 border-[var(--el-border-color)] border-solid)"
    @register="formRegister"
  />

  <ElDialog
    v-model="registerVisible"
    title="学生自主注册"
    width="min(620px, calc(100vw - 32px))"
    destroy-on-close
  >
    <Form
      :schema="registerSchema"
      :rules="registerRules"
      label-position="top"
      hide-required-asterisk
      size="large"
      @register="registerFormRegister"
    />
    <template #footer>
      <ElButton @click="registerVisible = false">取消</ElButton>
      <ElButton type="primary" :loading="registering" @click="submitRegister">提交注册</ElButton>
    </template>
  </ElDialog>
</template>
