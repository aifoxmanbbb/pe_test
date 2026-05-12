<script setup lang="tsx">
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { FormSchema, Form } from '@/components/Form'
import { Search } from '@/components/Search'
import { ElDialog, ElMessage } from 'element-plus'
import { Table, TableColumn } from '@/components/Table'
import { BaseButton } from '@/components/Button'
import { useForm } from '@/hooks/web/useForm'
import { useValidator } from '@/hooks/web/useValidator'
import {
  getStudentListApi,
  createStudentApi,
  updateStudentApi,
  getGradeOptionsApi,
  getClassOptionsApi,
  getSchoolOptionsApi
} from '@/api/vadmin/sport'
import StudentImport from './components/Import.vue'

defineOptions({ name: 'PEFStudent' })

const loading = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const limit = ref(10)
const searchParams = ref<Recordable>({})

const schoolOptions = ref([])
const gradeOptions = ref([])
const classOptions = ref([])
const searchRef = ref<any>()
const searchGradeOptions = ref([])
const searchClassOptions = ref([])
const { required, isTelephone, isIdCard } = useValidator()

const normalizeGender = (value: unknown) => {
  const text = String(value ?? '').trim().toLowerCase()
  if (['male', 'm', '1', '\u7537'].includes(text)) return 'male'
  if (['female', 'f', '0', '2', '\u5973'].includes(text)) return 'female'
  return ''
}

const displayGender = (value: unknown) => {
  const gender = normalizeGender(value)
  if (gender === 'male') return '\u7537'
  if (gender === 'female') return '\u5973'
  return '-'
}

const optionalTelephone = (_rule: any, value: any, callback: (error?: Error) => void) => {
  const text = String(value ?? '').trim()
  if (!text) {
    callback()
    return
  }
  isTelephone(_rule, text, callback)
}

const searchSchema = computed<FormSchema[]>(() => [
  { field: 'name', label: '学生姓名', component: 'Input' },
  { field: 'id_card', label: '身份证', component: 'Input' },
  {
    field: 'school_id',
    label: '学校',
    component: 'Select',
    componentProps: {
      options: schoolOptions.value,
      clearable: true,
      filterable: true,
      onChange: async (val: number) => {
        searchGradeOptions.value = []
        searchClassOptions.value = []
        await searchRef.value?.setValues({ grade_id: null, class_id: null })
        if (!val) return
        const res = await getGradeOptionsApi({ school_id: val }).catch(() => null)
        searchGradeOptions.value = res?.data || []
      }
    }
  },
  {
    field: 'grade_id',
    label: '年级',
    component: 'Select',
    componentProps: {
      options: searchGradeOptions.value,
      clearable: true,
      filterable: true,
      onChange: async (val: number) => {
        searchClassOptions.value = []
        await searchRef.value?.setValues({ class_id: null })
        if (!val) return
        const res = await getClassOptionsApi({ grade_id: val }).catch(() => null)
        searchClassOptions.value = res?.data || []
      }
    }
  },
  {
    field: 'class_id',
    label: '班级',
    component: 'Select',
    componentProps: { options: searchClassOptions.value, clearable: true, filterable: true }
  }
])

const tableColumns = reactive<TableColumn[]>([
  { field: 'name', label: '姓名', width: '100px', show: true },
  { field: 'id_card', label: '身份证', width: '180px', show: true },
  { field: 'phone', label: '手机号', width: '130px', show: true },
  { field: 'school_name', label: '所属学校', minWidth: '150px', show: true },
  { field: 'grade_name', label: '年级', width: '100px', show: true },
  { field: 'class_name', label: '班级', width: '100px', show: true },
  {
    field: 'gender',
    label: '性别',
    width: '80px',
    show: true,
    slots: {
      default: (data: any) => <span>{displayGender(data.row.gender)}</span>
    }
  },
  {
    field: 'action',
    label: '操作',
    width: '120px',
    fixed: 'right',
    show: true,
    slots: {
      default: (data: any) => (
        <BaseButton type="primary" link size="small" onClick={() => handleEdit(data.row)}>
          编辑
        </BaseButton>
      )
    }
  }
])

const loadList = async () => {
  loading.value = true
  const res = await getStudentListApi({
    ...searchParams.value,
    page: page.value,
    limit: limit.value
  }).catch(() => null)
  if (res && res.data) {
    list.value = res.data.items
    total.value = res.data.total
  }
  loading.value = false
}

const handleSearch = (params: Recordable = {}) => {
  searchParams.value = { ...params }
  if (page.value === 1) {
    loadList()
    return
  }
  page.value = 1
}

const handleReset = (params: Recordable = {}) => {
  searchParams.value = { ...params }
  searchGradeOptions.value = []
  searchClassOptions.value = []
  if (page.value === 1) {
    loadList()
    return
  }
  page.value = 1
}

const setSearchRegister = (expose: any) => {
  searchRef.value = expose
}

const loadSchools = async () => {
  const res = await getSchoolOptionsApi().catch(() => null)
  if (res) schoolOptions.value = res.data
}

const { formRegister, formMethods } = useForm()
const dialogVisible = ref(false)
const importDialogVisible = ref(false)
const currentId = ref<number | null>(null)

const formSchema = reactive<FormSchema[]>([
  { field: 'name', label: '姓名', component: 'Input' },
  {
    field: 'id_card',
    label: '身份证',
    component: 'Input',
    componentProps: {
      maxlength: 18,
      placeholder: '请输入学生身份证号'
    }
  },
  {
    field: 'phone',
    label: '手机号',
    component: 'Input',
    componentProps: {
      maxlength: 11,
      placeholder: '请输入学生/家长登录手机号'
    }
  },
  {
    field: 'gender',
    label: '性别',
    component: 'Select',
    componentProps: {
      options: [
        { label: '男', value: 'male' },
        { label: '女', value: 'female' }
      ]
    }
  },
  {
    field: 'school_id',
    label: '所属学校',
    component: 'Select',
    componentProps: {
      options: schoolOptions,
      onChange: async (val: number) => {
        const res = await getGradeOptionsApi({ school_id: val })
        gradeOptions.value = res.data
        formMethods.setValues({ grade_id: null, class_id: null })
      }
    }
  },
  {
    field: 'grade_id',
    label: '所属年级',
    component: 'Select',
    componentProps: {
      options: gradeOptions,
      onChange: async (val: number) => {
        const res = await getClassOptionsApi({ grade_id: val })
        classOptions.value = res.data
        formMethods.setValues({ class_id: null })
      }
    }
  },
  {
    field: 'class_id',
    label: '所属班级',
    component: 'Select',
    componentProps: { options: classOptions }
  }
])

const rules = reactive({
  name: [required()],
  id_card: [required(), { validator: isIdCard, trigger: 'blur' }],
  phone: [{ validator: optionalTelephone, trigger: 'blur' }],
  gender: [required()],
  school_id: [required()],
  grade_id: [required()],
  class_id: [required()]
})

const handleAdd = () => {
  currentId.value = null
  dialogVisible.value = true
  nextTick(() =>
    formMethods.setValues({
      name: '',
      id_card: '',
      phone: '',
      gender: '',
      school_id: null,
      grade_id: null,
      class_id: null
    })
  )
}

const handleImport = () => {
  importDialogVisible.value = true
}

const handleEdit = async (row: any) => {
  currentId.value = row.id
  dialogVisible.value = true
  const [gRes, cRes] = await Promise.all([
    getGradeOptionsApi({ school_id: row.school_id }),
    getClassOptionsApi({ grade_id: row.grade_id })
  ])
  if (gRes) gradeOptions.value = gRes.data
  if (cRes) classOptions.value = cRes.data
  nextTick(() => formMethods.setValues({ ...row, gender: normalizeGender(row.gender) }))
}

const submit = async () => {
  const elForm = await formMethods.getElFormExpose()
  const valid = await elForm?.validate()
  if (!valid) return
  const data = await formMethods.getFormData()
  if (!data) return
  const payload = { ...data, phone: String(data.phone || '').trim() || null, gender: normalizeGender(data.gender) }
  const res = currentId.value
    ? await updateStudentApi(currentId.value, payload)
    : await createStudentApi(payload)
  if (res) {
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadList()
  }
}

onMounted(() => {
  loadList()
  loadSchools()
})

watch([page, limit], () => {
  loadList()
})
</script>

<template>
  <ContentWrap>
    <div class="mb-10px text-18px font-bold">学生档案管理</div>
    <Search :schema="searchSchema" @register="setSearchRegister" @search="handleSearch" @reset="handleReset" class="mb-10px" />
    <div class="mb-10px">
      <BaseButton type="primary" @click="handleAdd">新增学生</BaseButton>
      <BaseButton type="success" class="ml-10px" @click="handleImport">批量导入学生</BaseButton>
    </div>
    <Table
      :columns="tableColumns"
      :data="list"
      :loading="loading"
      :pagination="{ total }"
      v-model:pageSize="limit"
      v-model:currentPage="page"
    />
    <ElDialog v-model="dialogVisible" :title="currentId ? '编辑学生' : '新增学生'" width="600px" destroy-on-close>
      <Form :schema="formSchema" :rules="rules" @register="formRegister" />
      <template #footer>
        <BaseButton type="primary" @click="submit">确定</BaseButton>
        <BaseButton @click="dialogVisible = false">取消</BaseButton>
      </template>
    </ElDialog>
    <ElDialog v-model="importDialogVisible" title="批量导入学生" width="820px" destroy-on-close>
      <StudentImport @get-list="loadList" />
    </ElDialog>
  </ContentWrap>
</template>
