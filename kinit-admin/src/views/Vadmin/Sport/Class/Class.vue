<script setup lang="tsx">
import { onMounted, reactive, ref, nextTick } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { FormSchema, Form } from '@/components/Form'
import { ElDialog, ElMessage, ElSwitch } from 'element-plus'
import { Table, TableColumn } from '@/components/Table'
import { BaseButton } from '@/components/Button'
import { useForm } from '@/hooks/web/useForm'
import { getClassListApi, createClassApi, updateClassApi, getGradeOptionsApi, getSchoolOptionsApi } from '@/api/vadmin/sport'

defineOptions({ name: 'PEFClass' })

const loading = ref(false)
const list = ref([])
const schoolOptions = ref([])
const gradeOptions = ref([])

const tableColumns = reactive<TableColumn[]>([
  { field: 'id', label: 'ID', width: '80px' },
  { field: 'school_name', label: '所属学校', minWidth: '150px' },
  { field: 'grade_name', label: '所属年级', width: '120px' },
  { field: 'class_name', label: '班级名称' },
  { field: 'class_code', label: '班级编码' },
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
  const res = await getClassListApi().catch(() => null)
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
    componentProps: { 
      options: schoolOptions,
      onChange: async (val: number) => {
        const res = await getGradeOptionsApi({ school_id: val })
        gradeOptions.value = res.data
        formMethods.setValues({ grade_id: null })
      }
    }
  },
  { 
    field: 'grade_id', 
    label: '所属年级', 
    component: 'Select', 
    required: true,
    componentProps: { options: gradeOptions }
  },
  { field: 'class_name', label: '班级名称', component: 'Input', required: true },
  { field: 'class_code', label: '班级编码', component: 'Input' },
  { field: 'sort', label: '排序', component: 'InputNumber', value: 0 }
])

const handleAdd = () => {
  currentId.value = null
  dialogVisible.value = true
  nextTick(() => formMethods.setValues({ class_name: '', class_code: '', sort: 0, school_id: null, grade_id: null }))
}

const handleEdit = async (row: any) => {
  currentId.value = row.id
  dialogVisible.value = true
  // 必须先加载对应学校的年级列表
  const res = await getGradeOptionsApi({ school_id: row.school_id })
  gradeOptions.value = res.data
  nextTick(() => formMethods.setValues(row))
}

const submit = async () => {
  const data = await formMethods.getFormData()
  if (!data) return
  const res = currentId.value 
    ? await updateClassApi(currentId.value, data)
    : await createClassApi(data)
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
    <div class="mb-10px text-18px font-bold">班级管理</div>
    <div class="mb-10px">
      <BaseButton type="primary" @click="handleAdd">新增班级</BaseButton>
    </div>
    <Table :columns="tableColumns" :data="list" :loading="loading" :pagination="false" />
    <ElDialog v-model="dialogVisible" :title="currentId ? '编辑班级' : '新增班级'" width="500px" destroy-on-close>
      <Form :schema="formSchema" @register="formRegister" />
      <template #footer>
        <BaseButton type="primary" @click="submit">确定</BaseButton>
        <BaseButton @click="dialogVisible = false">取消</BaseButton>
      </template>
    </ElDialog>
  </ContentWrap>
</template>
