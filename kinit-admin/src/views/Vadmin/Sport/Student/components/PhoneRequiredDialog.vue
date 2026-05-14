<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElButton, ElDialog, ElForm, ElFormItem, ElInput, ElMessage } from 'element-plus'
import { updateStudentSelfPhoneApi } from '@/api/vadmin/sport'
import { useAuthStoreWithOut } from '@/store/modules/auth'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    initialPhone?: string
    closable?: boolean
  }>(),
  {
    initialPhone: '',
    closable: false
  }
)

const emit = defineEmits<{
  (event: 'update:modelValue', value: boolean): void
  (event: 'saved', phone: string): void
}>()

const authStore = useAuthStoreWithOut()
const formRef = ref<FormInstance>()
const saving = ref(false)
const form = reactive({ phone: '' })
const canClose = computed(() => props.closable)
const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value)
})

const phonePattern = /^1(3\d|4[4-9]|5[0-35-9]|6[67]|7[013-8]|8[0-9]|9[0-9])\d{8}$/
const rules: FormRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: phonePattern, message: '请输入11位有效手机号', trigger: ['blur', 'change'] }
  ]
}

const resetForm = () => {
  form.phone = String(props.initialPhone || '').replace(/\D/g, '').slice(0, 11)
}

const handlePhoneInput = (value: string) => {
  form.phone = String(value || '').replace(/\D/g, '').slice(0, 11)
}

const submit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  const res = await updateStudentSelfPhoneApi({ phone: form.phone }).catch(() => null)
  saving.value = false

  if (!res) return
  const phone = res.data?.phone || form.phone
  authStore.updateUser({ ...authStore.getUser, telephone: phone })
  ElMessage.success(res.message || '手机号已保存')
  emit('saved', phone)
  visible.value = false
}

watch(
  () => props.modelValue,
  (show) => {
    if (show) resetForm()
  }
)
</script>

<template>
  <ElDialog
    v-model="visible"
    title="完善手机号"
    width="420px"
    class="student-phone-dialog"
    :show-close="canClose"
    :close-on-click-modal="canClose"
    :close-on-press-escape="canClose"
    destroy-on-close
  >
    <div class="student-phone-dialog__intro">
      查看个人成绩前需要先完善本人手机号。
    </div>
    <ElForm ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent>
      <ElFormItem label="手机号" prop="phone">
        <ElInput
          v-model="form.phone"
          placeholder="请输入11位手机号"
          maxlength="11"
          inputmode="numeric"
          clearable
          @input="handlePhoneInput"
          @keyup.enter="submit"
        />
      </ElFormItem>
    </ElForm>
    <template #footer>
      <ElButton type="primary" :loading="saving" class="student-phone-dialog__submit" @click="submit">
        保存手机号
      </ElButton>
    </template>
  </ElDialog>
</template>

<style scoped>
.student-phone-dialog__intro {
  margin-bottom: 16px;
  color: #475569;
  font-size: 14px;
  line-height: 1.7;
}

.student-phone-dialog__submit {
  width: 100%;
}
</style>
