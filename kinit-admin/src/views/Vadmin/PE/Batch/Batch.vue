<script setup lang="tsx">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import { Form, FormSchema } from '@/components/Form'
import { ElDialog, ElMessage, ElMessageBox, ElTag } from 'element-plus'
import { Table, TableColumn } from '@/components/Table'
import { BaseButton } from '@/components/Button'
import { useForm } from '@/hooks/web/useForm'
import { useValidator } from '@/hooks/web/useValidator'
import {
  createPeBatchApi,
  deletePeBatchApi,
  getPeBatchListApi,
  getPeStandardListApi,
  updatePeBatchApi
} from '@/api/vadmin/pe'
import { getClassOptionsApi, getGradeOptionsApi, getSchoolOptionsApi } from '@/api/vadmin/sport'

defineOptions({ name: 'PEBatch' })

const { required } = useValidator()

const batchList = ref<any[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const limit = ref(10)

const standardOptions = ref<any[]>([])
const schoolOptions = ref<any[]>([])
const gradeOptions = ref<any[]>([])
const classOptions = ref<any[]>([])

const SCOPE_ALL_VALUE = '__scope_all__'
const SCOPE_ALL_OPTION = { label: '不区分', value: SCOPE_ALL_VALUE }

const replaceOptions = (target: any[], rows: any[]) => {
  target.splice(0, target.length, ...(rows || []))
}

const toApiScopeValue = (value: any) => (value === SCOPE_ALL_VALUE ? '' : value)
const fromApiScopeValue = (value: any) => value || SCOPE_ALL_VALUE
const mapSchoolOptions = (rows: any[] = []) => [
  SCOPE_ALL_OPTION,
  ...rows.map((item: any) => ({ label: item.label, value: item.school_name }))
]
const mapGradeOptions = (rows: any[] = []) => [
  SCOPE_ALL_OPTION,
  ...rows.map((item: any) => ({ label: item.label, value: item.grade_name || item.value }))
]
const mapClassOptions = (rows: any[] = []) => [
  SCOPE_ALL_OPTION,
  ...rows.map((item: any) => ({ label: item.label, value: item.class_name || item.value }))
]
const normalizeBatchForm = (row: any) => ({
  ...row,
  school_name: fromApiScopeValue(row?.school_name),
  grade_name: fromApiScopeValue(row?.grade_name),
  class_name: fromApiScopeValue(row?.class_name)
})
const normalizeBatchPayload = (data: any) => ({
  ...data,
  school_name: toApiScopeValue(data?.school_name),
  grade_name: toApiScopeValue(data?.grade_name),
  class_name: toApiScopeValue(data?.class_name)
})

const searchSchema = computed<FormSchema[]>(() => [{ field: 'batch_name', label: '批次名称', component: 'Input' }])

const tableColumns = reactive<TableColumn[]>([
  { field: 'id', label: 'ID', width: '60px', show: true },
  { field: 'batch_name', label: '批次名称', minWidth: '180px', show: true },
  { field: 'standard_name', label: '评分标准', minWidth: '260px', show: true },
  { field: 'school_name', label: '学校', minWidth: '120px', show: true },
  { field: 'grade_name', label: '年级', width: '100px', show: true },
  { field: 'class_name', label: '班级', width: '100px', show: true },
  {
    field: 'status',
    label: '状态',
    show: true,
    slots: {
      default: (data: any) => {
        const statusMap: Record<string, 'info' | 'primary' | 'success'> = {
          draft: 'info',
          ongoing: 'primary',
          finished: 'success'
        }
        return <ElTag type={statusMap[data.row.status]}>{data.row.status}</ElTag>
      }
    }
  },
  {
    field: 'action',
    label: '操作',
    width: '150px',
    fixed: 'right',
    show: true,
    slots: {
      default: (data: any) => (
        <>
          <BaseButton type="primary" link onClick={() => handleEdit(data.row)}>
            编辑
          </BaseButton>
          <BaseButton type="danger" link onClick={() => handleDelete(data.row)}>
            删除
          </BaseButton>
        </>
      )
    }
  }
])

const loadList = async () => {
  loading.value = true
  const res = await getPeBatchListApi({ page: page.value, limit: limit.value }).catch(() => null)
  if (res?.data) {
    batchList.value = res.data.items || []
    total.value = res.data.total || 0
  }
  loading.value = false
}

const loadFormOptions = async () => {
  const [standardRes, schoolRes] = await Promise.all([getPeStandardListApi(), getSchoolOptionsApi()])
  if (standardRes?.data) {
    replaceOptions(
      standardOptions.value,
      standardRes.data.map((item: any) => ({
        label: `${item.name} [${item.version}]`,
        value: item.id
      }))
    )
  }
  if (schoolRes?.data) {
    replaceOptions(schoolOptions.value, mapSchoolOptions(schoolRes.data))
  }
}

const { formRegister, formMethods } = useForm()
const dialogVisible = ref(false)
const currentId = ref<number | null>(null)

const formSchema = reactive<FormSchema[]>([
  {
    field: 'batch_name',
    label: '批次名称',
    component: 'Input',
    formItemProps: { rules: [required('请输入批次名称')] }
  },
  {
    field: 'standard_id',
    label: '评分标准',
    component: 'Select',
    componentProps: { options: standardOptions.value },
    formItemProps: { rules: [required('请选择评分标准')] }
  },
  {
    field: 'stage_type',
    label: '针对学段',
    component: 'Select',
    componentProps: {
      options: [
        { label: '初中', value: 'mid' },
        { label: '高中', value: 'high' }
      ]
    },
    formItemProps: { rules: [required('请选择针对学段')] }
  },
  {
    field: 'school_name',
    label: '学校名称',
    component: 'Select',
    componentProps: {
      options: schoolOptions.value,
      onChange: async (val: string) => {
        if (val === SCOPE_ALL_VALUE) {
          replaceOptions(gradeOptions.value, [SCOPE_ALL_OPTION])
          replaceOptions(classOptions.value, [SCOPE_ALL_OPTION])
          formMethods.setValues({ grade_name: SCOPE_ALL_VALUE, class_name: SCOPE_ALL_VALUE })
          return
        }
        const res = await getGradeOptionsApi({ school_name: val }).catch(() => null)
        replaceOptions(gradeOptions.value, mapGradeOptions(res?.data || []))
        replaceOptions(classOptions.value, [])
        formMethods.setValues({ grade_name: null, class_name: null })
      }
    },
    formItemProps: { rules: [required('请选择学校名称')] }
  },
  {
    field: 'grade_name',
    label: '年级',
    component: 'Select',
    componentProps: {
      options: gradeOptions.value,
      onChange: async (val: string) => {
        if (val === SCOPE_ALL_VALUE) {
          replaceOptions(classOptions.value, [SCOPE_ALL_OPTION])
          formMethods.setValues({ class_name: SCOPE_ALL_VALUE })
          return
        }
        const formData = await formMethods.getFormData()
        const res = await getClassOptionsApi({ school_name: formData?.school_name, grade_name: val }).catch(() => null)
        replaceOptions(classOptions.value, mapClassOptions(res?.data || []))
        formMethods.setValues({ class_name: null })
      }
    },
    formItemProps: { rules: [required('请选择年级')] }
  },
  {
    field: 'class_name',
    label: '班级',
    component: 'Select',
    componentProps: { options: classOptions.value },
    formItemProps: { rules: [required('请选择班级')] }
  },
  {
    field: 'status',
    label: '状态',
    component: 'Select',
    value: 'draft',
    componentProps: {
      options: [
        { label: '草稿', value: 'draft' },
        { label: '进行中', value: 'ongoing' },
        { label: '已结束', value: 'finished' }
      ]
    },
    formItemProps: { rules: [required('请选择状态')] }
  }
])

const handleAdd = () => {
  currentId.value = null
  dialogVisible.value = true
  replaceOptions(gradeOptions.value, [])
  replaceOptions(classOptions.value, [])
  nextTick(() => formMethods.setValues({ status: 'draft', stage_type: 'mid' }))
}

const handleEdit = async (row: any) => {
  currentId.value = row.id
  dialogVisible.value = true
  if (row.school_name) {
    const gradeRes = await getGradeOptionsApi({ school_name: row.school_name }).catch(() => null)
    replaceOptions(gradeOptions.value, mapGradeOptions(gradeRes?.data || []))
  } else {
    replaceOptions(gradeOptions.value, [SCOPE_ALL_OPTION])
  }
  if (row.grade_name) {
    const classRes = await getClassOptionsApi({ school_name: row.school_name, grade_name: row.grade_name }).catch(() => null)
    replaceOptions(classOptions.value, mapClassOptions(classRes?.data || []))
  } else {
    replaceOptions(classOptions.value, [SCOPE_ALL_OPTION])
  }
  nextTick(() => formMethods.setValues(normalizeBatchForm(row)))
}

const handleDelete = (row: any) => {
  ElMessageBox.confirm('确定删除吗？').then(async () => {
    await deletePeBatchApi(row.id)
    loadList()
  })
}

const submit = async () => {
  const elForm = await formMethods.getElFormExpose()
  const valid = await elForm?.validate().catch(() => false)
  if (!valid) return
  const data = await formMethods.getFormData()
  if (!data) return
  const payload = normalizeBatchPayload(data)
  const res = currentId.value ? await updatePeBatchApi(currentId.value, payload) : await createPeBatchApi(payload)
  if (res) {
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadList()
  }
}

onMounted(() => {
  loadList()
  loadFormOptions()
})
</script>

<template>
  <ContentWrap>
    <Search :schema="searchSchema" class="mb-20px" @search="loadList" @reset="loadList" />
    <div class="mb-10px">
      <BaseButton type="primary" @click="handleAdd">新增体考批次</BaseButton>
    </div>
    <Table
      v-model:currentPage="page"
      v-model:pageSize="limit"
      :columns="tableColumns"
      :data="batchList"
      :loading="loading"
      :pagination="{ total }"
      @register="loadList"
    />
    <ElDialog v-model="dialogVisible" :title="currentId ? '编辑批次' : '新增批次'" width="600px" destroy-on-close>
      <Form :schema="formSchema" @register="formRegister" />
      <template #footer>
        <BaseButton type="primary" @click="submit">确定</BaseButton>
        <BaseButton @click="dialogVisible = false">取消</BaseButton>
      </template>
    </ElDialog>
  </ContentWrap>
</template>
