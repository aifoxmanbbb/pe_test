<script setup lang="tsx">
import { onMounted, reactive, ref, nextTick } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { FormSchema, Form } from '@/components/Form'
import { Search } from '@/components/Search'
import { ElDialog, ElMessage, ElTag } from 'element-plus'
import { Table, TableColumn } from '@/components/Table'
import { BaseButton } from '@/components/Button'
import { useForm } from '@/hooks/web/useForm'
import { getStudentListApi, createStudentApi, updateStudentApi, getGradeOptionsApi, getClassOptionsApi, getSchoolOptionsApi } from '@/api/vadmin/sport'

defineOptions({ name: 'PEFStudent' })

const loading = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const limit = ref(10)

const schoolOptions = ref([])
const gradeOptions = ref([])
const classOptions = ref([])

const searchSchema = reactive<FormSchema[]>([
  { field: 'name', label: '学生姓名', component: 'Input' }
])

const tableColumns = reactive<TableColumn[]>([
  { field: 'student_no', label: '学号', width: '120px' },
  { field: 'name', label: '姓名', width: '100px' },
  { field: 'school_name', label: '所属学校', minWidth: '150px' },
  { field: 'grade_name', label: '年级', width: '100px' },
  { field: 'class_name', label: '班级', width: '100px' },
  {
    field: 'gender',
    label: '性别',
    width: '80px',
    slots: {
      default: (data: any) => <span>{data.row.gender === 'male' ? '男' : '女'}</span>
    }
  },
  {
    field: 'action',
    label: '操作',
    width: '120px',
    fixed: 'right',
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
  const res = await getStudentListApi({ page: page.value, limit: limit.value }).catch(() => null)
  if (res && res.data) {
    list.value = res.data.items
    total.value = res.data.total
  }
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
  { field: 'student_no', label: '学号', component: 'Input', required: true },
  { field: 'name', label: '姓名', component: 'Input', required: true },
  { 
    field: 'gender', 
    label: '性别', 
    component: 'Select', 
    required: true,
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
    required: true,
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
    required: true,
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
    required: true,
    componentProps: { options: classOptions }
  }
])

const handleAdd = () => {
  currentId.value = null
  dialogVisible.value = true
  nextTick(() => formMethods.setValues({ student_no: '', name: '', gender: 'male', school_id: null, grade_id: null, class_id: null }))
}

const handleEdit = async (row: any) => {
  currentId.value = row.id
  dialogVisible.value = true
  // 同步加载级联数据
  const [gRes, cRes] = await Promise.all([
    getGradeOptionsApi({ school_id: row.school_id }),
    getClassOptionsApi({ grade_id: row.grade_id })
  ])
  if (gRes) gradeOptions.value = gRes.data
  if (cRes) classOptions.value = cRes.data
  nextTick(() => formMethods.setValues(row))
}

const submit = async () => {
  const data = await formMethods.getFormData()
  if (!data) return
  const res = currentId.value 
    ? await updateStudentApi(currentId.value, data)
    : await createStudentApi(data)
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
    <div class="mb-10px text-18px font-bold">学生档案管理</div>
    <Search :schema="searchSchema" @search="loadList" @reset="loadList" class="mb-10px" />
    <div class="mb-10px">
      <BaseButton type="primary" @click="handleAdd">新增学生</BaseButton>
    </div>
    <Table
      :columns="tableColumns"
      :data="list"
      :loading="loading"
      :pagination="{ total }"
      v-model:pageSize="limit"
      v-model:currentPage="page"
      @register="loadList"
    />
    <ElDialog v-model="dialogVisible" :title="currentId ? '编辑学生' : '新增学生'" width="600px" destroy-on-close>
      <Form :schema="formSchema" @register="formRegister" />
      <template #footer>
        <BaseButton type="primary" @click="submit">确定</BaseButton>
        <BaseButton @click="dialogVisible = false">取消</BaseButton>
      </template>
    </ElDialog>
  </ContentWrap>
</template>
