<script setup lang="tsx">
import { onMounted, reactive, ref, nextTick } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { FormSchema, Form } from '@/components/Form'
import { ElDialog, ElMessage, ElSwitch } from 'element-plus'
import { Table, TableColumn } from '@/components/Table'
import { BaseButton } from '@/components/Button'
import { useForm } from '@/hooks/web/useForm'
import { getGradeListApi, createGradeApi, updateGradeApi, getSchoolOptionsApi } from '@/api/vadmin/sport'

defineOptions({ name: 'PEFGrade' })

const loading = ref(false)
const list = ref([])
const schoolOptions = ref([])

const tableColumns = reactive<TableColumn[]>([
  { field: 'id', label: 'ID', width: '80px' },
  { field: 'school_name', label: '所属学校', minWidth: '150px' },
  { field: 'grade_name', label: '年级名称' },
  { field: 'grade_code', label: '年级编码' },
  { field: 'sort', label: '排序', width: '100px' },
  {
    field: 'is_active',
    label: '状态',
    slots: {
      default: (data: any) => <ElSwitch v-model={data.row.is_active} disabled />
    }
  },
  {
    field: 'action',
    label: '操作',
    width: '120px',
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
  const res = await getGradeListApi().catch(() => null)
  if (res) list.value = res.data
  loading.value = false
}

const loadSchools = async () => {
  const res = await getSchoolOptionsApi().catch(() => null)
  if (res) schoolOptions.value = res.data
}

const { formRegister, formMethods } = useForm()
const dialogVisible = ref(false)
const currentId = ref<number | null>(null)

const formSchema = reactive<FormSchema[]>([
  { 
    field: 'school_id', 
    label: '所属学校', 
    component: 'Select', 
    required: true,
    componentProps: { options: schoolOptions }
  },
  { field: 'grade_name', label: '年级名称', component: 'Input', required: true },
  { field: 'grade_code', label: '年级编码', component: 'Input' },
  { field: 'sort', label: '排序', component: 'InputNumber', value: 0 },
  { field: 'is_active', label: '启用', component: 'Switch', value: true }
])

const handleAdd = () => {
  currentId.value = null
  dialogVisible.value = true
  nextTick(() => formMethods.setValues({ grade_name: '', grade_code: '', sort: 0, is_active: true, school_id: null }))
}

const handleEdit = (row: any) => {
  currentId.value = row.id
  dialogVisible.value = true
  nextTick(() => formMethods.setValues(row))
}

const submit = async () => {
  const data = await formMethods.getFormData()
  if (!data) return
  const res = currentId.value 
    ? await updateGradeApi(currentId.value, data)
    : await createGradeApi(data)
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
</script>

<template>
  <ContentWrap>
    <div class="mb-10px text-18px font-bold">年级管理</div>
    <div class="mb-10px">
      <BaseButton type="primary" @click="handleAdd">新增年级</BaseButton>
    </div>
    <Table :columns="tableColumns" :data="list" :loading="loading" :pagination="false" />
    <ElDialog v-model="dialogVisible" :title="currentId ? '编辑年级' : '新增年级'" width="500px" destroy-on-close>
      <Form :schema="formSchema" @register="formRegister" />
      <template #footer>
        <BaseButton type="primary" @click="submit">确定</BaseButton>
        <BaseButton @click="dialogVisible = false">取消</BaseButton>
      </template>
    </ElDialog>
  </ContentWrap>
</template>
