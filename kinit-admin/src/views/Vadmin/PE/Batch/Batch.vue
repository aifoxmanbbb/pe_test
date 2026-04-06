<script setup lang="tsx">
import { onMounted, reactive, ref } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import { FormSchema, Form } from '@/components/Form'
import { ElTag, ElDialog, ElMessageBox, ElMessage } from 'element-plus'
import { Table, TableColumn } from '@/components/Table'
import { BaseButton } from '@/components/Button'
import { useForm } from '@/hooks/web/useForm'
import {
  getPeBatchListApi,
  createPeBatchApi,
  updatePeBatchApi,
  deletePeBatchApi,
  getPeStandardListApi
} from '@/api/vadmin/pe'

defineOptions({
  name: 'PEBatch'
})

const searchSchema = reactive<FormSchema[]>([
  {
    field: 'batch_name',
    label: '批次名称',
    component: 'Input',
    componentProps: {
      placeholder: '请输入批次名称'
    }
  },
  {
    field: 'status',
    label: '状态',
    component: 'Select',
    componentProps: {
      placeholder: '请选择状态',
      options: [
        { label: '草稿', value: 'draft' },
        { label: '进行中', value: 'ongoing' },
        { label: '已结束', value: 'finished' }
      ]
    }
  }
])

const searchParams = ref<Record<string, any>>({})
const setSearchParams = (data: Record<string, any>) => {
  searchParams.value = data
  loadList()
}

const batchList = ref([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const limit = ref(10)

const tableColumns = reactive<TableColumn[]>([
  { field: 'id', label: 'ID', width: '60px' },
  { field: 'batch_name', label: '批次名称', minWidth: '180px' },
  { field: 'school_name', label: '学校', minWidth: '150px' },
  { field: 'grade_name', label: '年级', width: '100px' },
  { field: 'class_name', label: '班级', width: '100px' },
  {
    field: 'stage_type',
    label: '学段',
    width: '80px',
    slots: {
      default: (data: any) => {
        return data.row.stage_type === 'mid' ? '初中' : '高中'
      }
    }
  },
  {
    field: 'status',
    label: '状态',
    width: '90px',
    slots: {
      default: (data: any) => {
        const val = data.row.status
        const statusMap = {
          draft: { label: '草稿', type: 'info' },
          ongoing: { label: '进行中', type: 'primary' },
          finished: { label: '已结束', type: 'success' }
        }
        const config = statusMap[val] || { label: val, type: 'info' }
        return <ElTag type={config.type as any}>{config.label}</ElTag>
      }
    }
  },
  { field: 'create_datetime', label: '创建时间', width: '170px' },
  {
    field: 'action',
    label: '操作',
    width: '180px',
    fixed: 'right',
    slots: {
      default: (data: any) => {
        return (
          <>
            <BaseButton type="primary" link size="small" onClick={() => handleEdit(data.row)}>
              编辑
            </BaseButton>
            <BaseButton type="danger" link size="small" onClick={() => handleDelete(data.row)}>
              删除
            </BaseButton>
            {data.row.status === 'draft' && (
              <BaseButton type="success" link size="small" onClick={() => handleStatus(data.row, 'ongoing')}>
                开始
              </BaseButton>
            )}
            {data.row.status === 'ongoing' && (
              <BaseButton type="warning" link size="small" onClick={() => handleStatus(data.row, 'finished')}>
                结束
              </BaseButton>
            )}
          </>
        )
      }
    }
  }
])

const standardOptions = ref<{ label: string; value: number }[]>([])

const loadStandards = async () => {
  const res = await getPeStandardListApi().catch(() => null)
  if (res) {
    standardOptions.value = res.data.map((i: any) => ({ label: i.name, value: i.id }))
  }
}

const loadList = async () => {
  loading.value = true
  const res = await getPeBatchListApi({
    page: page.value,
    limit: limit.value,
    ...searchParams.value
  }).catch(() => null)
  if (res) {
    batchList.value = res.data.items
    total.value = res.data.total
  }
  loading.value = false
}

const dialogVisible = ref(false)
const dialogTitle = ref('新增批次')
const currentId = ref<number | null>(null)

const { formRegister, formMethods } = useForm()
const { setValues, getFormData, setSchema } = formMethods

const formSchema = reactive<FormSchema[]>([
  {
    field: 'batch_name',
    label: '批次名称',
    component: 'Input',
    required: true
  },
  {
    field: 'standard_id',
    label: '评分标准',
    component: 'Select',
    required: true,
    componentProps: {
      options: standardOptions
    }
  },
  {
    field: 'school_name',
    label: '学校名称',
    component: 'Input',
    required: true
  },
  {
    field: 'grade_name',
    label: '年级名称',
    component: 'Input',
    required: true
  },
  {
    field: 'class_name',
    label: '班级名称',
    component: 'Input',
    required: true
  },
  {
    field: 'stage_type',
    label: '学段',
    component: 'Select',
    required: true,
    value: 'mid',
    componentProps: {
      options: [
        { label: '初中', value: 'mid' },
        { label: '高中', value: 'high' }
      ]
    }
  },
  {
    field: 'remark',
    label: '备注',
    component: 'Input',
    componentProps: {
      type: 'textarea'
    }
  }
])

const handleAdd = () => {
  dialogTitle.value = '新增批次'
  currentId.value = null
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  dialogTitle.value = '编辑批次'
  currentId.value = row.id
  dialogVisible.value = true
  setValues(row)
}

const handleDelete = (row: any) => {
  ElMessageBox.confirm('确认删除该批次吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    const res = await deletePeBatchApi(row.id).catch(() => null)
    if (res) {
      ElMessage.success('删除成功')
      loadList()
    }
  })
}

const handleStatus = async (row: any, status: string) => {
  const res = await updatePeBatchApi(row.id, { status }).catch(() => null)
  if (res) {
    ElMessage.success('操作成功')
    loadList()
  }
}

const submit = async () => {
  const data = await getFormData()
  if (currentId.value) {
    const res = await updatePeBatchApi(currentId.value, data).catch(() => null)
    if (res) {
      ElMessage.success('更新成功')
      dialogVisible.value = false
      loadList()
    }
  } else {
    const res = await createPeBatchApi(data).catch(() => null)
    if (res) {
      ElMessage.success('创建成功')
      dialogVisible.value = false
      loadList()
    }
  }
}

onMounted(() => {
  loadList()
  loadStandards()
})
</script>

<template>
  <ContentWrap>
    <Search
      :schema="searchSchema"
      @search="setSearchParams"
      @reset="setSearchParams"
      class="mb-20px"
    />

    <div class="mb-10px">
      <BaseButton type="primary" @click="handleAdd">新增批次</BaseButton>
    </div>

    <Table
      :columns="tableColumns"
      :data="batchList"
      :loading="loading"
      :pagination="{
        total: total
      }"
      v-model:pageSize="limit"
      v-model:currentPage="page"
      @register="loadList"
    />

    <ElDialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <Form :schema="formSchema" @register="formRegister" />
      <template #footer>
        <BaseButton type="primary" @click="submit">确定</BaseButton>
        <BaseButton @click="dialogVisible = false">取消</BaseButton>
      </template>
    </ElDialog>
  </ContentWrap>
</template>
