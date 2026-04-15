<script setup lang="tsx">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import { Form, FormSchema } from '@/components/Form'
import { ElDialog, ElMessage, ElMessageBox, ElTag } from 'element-plus'
import { Table, TableColumn } from '@/components/Table'
import { BaseButton } from '@/components/Button'
import { useForm } from '@/hooks/web/useForm'
import {
  createFitnessBatchApi,
  deleteFitnessBatchApi,
  getFitnessBatchListApi,
  getFitnessStandardListApi,
  updateFitnessBatchApi
} from '@/api/vadmin/fitness'
import { getClassOptionsApi, getGradeOptionsApi, getSchoolOptionsApi } from '@/api/vadmin/sport'

defineOptions({ name: 'FitnessBatch' })

const batchList = ref<any[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const limit = ref(10)

const standardOptions = ref<any[]>([])
const schoolOptions = ref<any[]>([])
const gradeOptions = ref<any[]>([])
const classOptions = ref<any[]>([])

const replaceOptions = (target: any[], rows: any[]) => {
  target.splice(0, target.length, ...(rows || []))
}

const searchSchema = computed<FormSchema[]>(() => [{ field: 'batch_name', label: '批次名称', component: 'Input' }])

const tableColumns = reactive<TableColumn[]>([
  { field: 'id', label: 'ID', width: '60px' },
  { field: 'batch_name', label: '批次名称', minWidth: '180px' },
  { field: 'standard_name', label: '评分标准', minWidth: '260px' },
  { field: 'school_name', label: '学校', minWidth: '120px' },
  { field: 'grade_name', label: '年级', width: '100px' },
  { field: 'class_name', label: '班级', width: '100px' },
  {
    field: 'status',
    label: '状态',
    slots: {
      default: (data: any) => <ElTag>{data.row.status}</ElTag>
    }
  },
  {
    field: 'action',
    label: '操作',
    width: '150px',
    fixed: 'right',
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
  const res = await getFitnessBatchListApi({ page: page.value, limit: limit.value }).catch(() => null)
  if (res?.data) {
    batchList.value = res.data.items || []
    total.value = res.data.total || 0
  }
  loading.value = false
}

const loadFormOptions = async () => {
  const [standardRes, schoolRes] = await Promise.all([getFitnessStandardListApi(), getSchoolOptionsApi()])
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
    replaceOptions(
      schoolOptions.value,
      schoolRes.data.map((item: any) => ({ label: item.label, value: item.school_name }))
    )
  }
}

const { formRegister, formMethods } = useForm()
const dialogVisible = ref(false)
const currentId = ref<number | null>(null)

const formSchema = reactive<FormSchema[]>([
  { field: 'batch_name', label: '批次名称', component: 'Input', required: true },
  {
    field: 'standard_id',
    label: '评分标准',
    component: 'Select',
    required: true,
    componentProps: { options: standardOptions.value }
  },
  {
    field: 'stage_type',
    label: '针对学段',
    component: 'Select',
    componentProps: {
      onChange: async (val: string) => {
        const schoolRes = await getSchoolOptionsApi(val ? { stage_type: val } : undefined).catch(() => null)
        replaceOptions(
          schoolOptions.value,
          schoolRes?.data ? schoolRes.data.map((item: any) => ({ label: item.label, value: item.school_name })) : []
        )
        formMethods.setValues({ school_name: null, grade_name: null, class_name: null })
        replaceOptions(gradeOptions.value, [])
        replaceOptions(classOptions.value, [])
      },
      options: [
        { label: '小学', value: 'primary' },
        { label: '初中', value: 'mid' },
        { label: '高中', value: 'high' },
        { label: '大学', value: 'university' }
      ]
    }
  },
  {
    field: 'school_name',
    label: '学校名称',
    component: 'Select',
    componentProps: {
      options: schoolOptions.value,
      onChange: async (val: string) => {
        const res = await getGradeOptionsApi({ school_name: val }).catch(() => null)
        replaceOptions(
          gradeOptions.value,
          res?.data ? res.data.map((item: any) => ({ label: item.label, value: item.grade_name })) : []
        )
        formMethods.setValues({ grade_name: null, class_name: null })
      }
    }
  },
  {
    field: 'grade_name',
    label: '年级',
    component: 'Select',
    componentProps: {
      options: gradeOptions.value,
      onChange: async (val: string) => {
        const formData = await formMethods.getFormData()
        const res = await getClassOptionsApi({ school_name: formData?.school_name, grade_name: val }).catch(() => null)
        replaceOptions(
          classOptions.value,
          res?.data ? res.data.map((item: any) => ({ label: item.label, value: item.class_name })) : []
        )
        formMethods.setValues({ class_name: null })
      }
    }
  },
  {
    field: 'class_name',
    label: '班级',
    component: 'Select',
    componentProps: { options: classOptions.value }
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
    }
  }
])

const handleAdd = () => {
  currentId.value = null
  dialogVisible.value = true
  nextTick(() => formMethods.setValues({ status: 'draft', stage_type: 'mid' }))
}

const handleEdit = async (row: any) => {
  currentId.value = row.id
  dialogVisible.value = true
  const schoolRes = await getSchoolOptionsApi(row.stage_type ? { stage_type: row.stage_type } : undefined).catch(() => null)
  if (schoolRes?.data) {
    replaceOptions(
      schoolOptions.value,
      schoolRes.data.map((item: any) => ({ label: item.label, value: item.school_name }))
    )
  }
  if (row.school_name) {
    const gradeRes = await getGradeOptionsApi({ school_name: row.school_name }).catch(() => null)
    replaceOptions(
      gradeOptions.value,
      gradeRes?.data ? gradeRes.data.map((item: any) => ({ label: item.label, value: item.grade_name || item.value })) : []
    )
  }
  if (row.grade_name) {
    const classRes = await getClassOptionsApi({ school_name: row.school_name, grade_name: row.grade_name }).catch(() => null)
    replaceOptions(
      classOptions.value,
      classRes?.data ? classRes.data.map((item: any) => ({ label: item.label, value: item.class_name || item.value })) : []
    )
  }
  nextTick(() => formMethods.setValues(row))
}

const handleDelete = (row: any) => {
  ElMessageBox.confirm('确定删除吗？').then(async () => {
    await deleteFitnessBatchApi(row.id)
    loadList()
  })
}

const submit = async () => {
  const data = await formMethods.getFormData()
  if (!data) return
  const res = currentId.value
    ? await updateFitnessBatchApi(currentId.value, data)
    : await createFitnessBatchApi(data)
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
      <BaseButton type="primary" @click="handleAdd">新增体测批次</BaseButton>
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
