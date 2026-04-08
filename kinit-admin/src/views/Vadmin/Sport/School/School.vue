<script setup lang="tsx">
import { onMounted, reactive, ref, nextTick } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { FormSchema, Form } from '@/components/Form'
import { ElDialog, ElMessage, ElSwitch, ElInput, ElInputNumber } from 'element-plus'
import { Table, TableColumn } from '@/components/Table'
import { BaseButton } from '@/components/Button'
import { useForm } from '@/hooks/web/useForm'
import { getSchoolListApi, createSchoolApi, updateSchoolApi } from '@/api/vadmin/sport'

defineOptions({ name: 'PEFSchool' })

const loading = ref(false)
const list = ref([])
const stageOptions = [
  { label: '小学', value: 'primary' },
  { label: '初中', value: 'mid' },
  { label: '高中', value: 'high' },
  { label: '大学', value: 'university' }
]

const stageTextMap: Record<string, string> = {
  primary: '小学',
  mid: '初中',
  high: '高中',
  university: '大学'
}

const tableColumns = reactive<TableColumn[]>([
  { field: 'id', label: 'ID', width: '80px' },
  { field: 'school_name', label: '学校名称' },
  { field: 'school_code', label: '学校代码' },
  { field: 'region', label: '所属地区' },
  {
    field: 'stage_types',
    label: '学段',
    minWidth: '180px',
    slots: {
      default: (data: any) => {
        const values = String(data.row.stage_types || '')
          .split(',')
          .filter(Boolean)
          .map((v: string) => stageTextMap[v] || v)
        return values.join(' / ') || '-'
      }
    }
  },
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
  try {
    const res = await getSchoolListApi().catch(() => null)
    if (res && res.data) {
      list.value = res.data
    }
  } catch (e) {
    ElMessage.error('加载列表失败')
  } finally {
    loading.value = false
  }
}

const { formRegister, formMethods } = useForm()
const dialogVisible = ref(false)
const currentId = ref<number | null>(null)

const formSchema = reactive<FormSchema[]>([
  { field: 'school_name', label: '学校名称', component: 'Input', required: true },
  { field: 'school_code', label: '学校代码', component: 'Input' },
  { field: 'region', label: '地区', component: 'Input' },
  {
    field: 'stage_types',
    label: '学段',
    component: 'Select',
    required: true,
    componentProps: {
      options: stageOptions,
      multiple: true,
      collapseTags: true,
      collapseTagsTooltip: true,
      clearable: true
    }
  },
  { field: 'sort', label: '排序', component: 'InputNumber', value: 0 },
  { field: 'is_active', label: '启用', component: 'Switch', value: true }
])

const handleAdd = () => {
  currentId.value = null
  dialogVisible.value = true
  nextTick(() => {
    formMethods.setValues({ school_name: '', school_code: '', region: '', stage_types: ['mid'], sort: 0, is_active: true })
  })
}

const handleEdit = (row: any) => {
  currentId.value = row.id
  dialogVisible.value = true
  nextTick(() => {
    formMethods.setValues({
      ...row,
      stage_types: String(row.stage_types || '').split(',').filter(Boolean)
    })
  })
}

const submit = async () => {
  const data: any = await formMethods.getFormData()
  if (!data) return
  const payload = {
    ...data,
    stage_types: Array.isArray(data.stage_types) ? data.stage_types.join(',') : data.stage_types
  }
  
  loading.value = true
  try {
    const res = currentId.value 
      ? await updateSchoolApi(currentId.value, payload)
      : await createSchoolApi(payload)
    if (res) {
      ElMessage.success('保存成功')
      dialogVisible.value = false
      loadList()
    }
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadList)
</script>

<template>
  <ContentWrap>
    <div class="mb-10px text-18px font-bold">学校管理</div>
    <div class="mb-10px">
      <BaseButton type="primary" @click="handleAdd">新增学校</BaseButton>
    </div>
    <Table :columns="tableColumns" :data="list" :loading="loading" :pagination="false" />
    <ElDialog 
      v-model="dialogVisible" 
      :title="currentId ? '编辑学校' : '新增学校'" 
      width="500px" 
      destroy-on-close
    >
      <Form :schema="formSchema" @register="formRegister" />
      <template #footer>
        <BaseButton type="primary" @click="submit" :loading="loading">确定</BaseButton>
        <BaseButton @click="dialogVisible = false">取消</BaseButton>
      </template>
    </ElDialog>
  </ContentWrap>
</template>
