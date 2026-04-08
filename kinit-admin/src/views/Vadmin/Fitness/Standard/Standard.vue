<script setup lang="tsx">
import { onMounted, reactive, ref , computed} from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import { ElTag, ElDialog, ElMessage, ElUpload, ElInput, ElCard, ElSelect, ElOption } from 'element-plus'
import { Table, TableColumn } from '@/components/Table'
import { BaseButton } from '@/components/Button'
import {
  getFitnessStandardListApi,
  createFitnessStandardApi,
  importFitnessStandardApi,
  confirmFitnessStandardApi
} from '@/api/vadmin/fitness'

defineOptions({
  name: 'FitnessStandard'
})

// ─── 导入逻辑 ─────────────────────────────────────────────
const importDialogVisible = ref(false)
const importLoading = ref(false)
const importedItems = ref<any[]>([])
const importForm = reactive({
  name: '',
  region: '重庆市',
  year: 2026,
  version: '',
  stage_type: 'mid'
})
const stageOptions = [
  { label: '小学', value: 'primary' },
  { label: '初中', value: 'mid' },
  { label: '高中', value: 'high' },
  { label: '大学', value: 'university' }
]

const handleExcelImport = async (options: any) => {
  const formData = new FormData()
  formData.append('file', options.file)
  importLoading.value = true
  try {
    const res = await importFitnessStandardApi(formData)
    if (res && res.data) {
      importedItems.value = res.data
      importDialogVisible.value = true
      ElMessage.success('解析成功，请确认标准详情')
    }
  } catch {
    ElMessage.error('解析失败')
  } finally {
    importLoading.value = false
  }
}

const handleConfirmImport = async () => {
  if (!importForm.name || !importForm.version) {
    ElMessage.warning('请完整填写标准基本信息')
    return
  }
  const payload = {
    ...importForm,
    items: importedItems.value
  }
  const res = await confirmFitnessStandardApi(payload).catch(() => null)
  if (res) {
    ElMessage.success('导入成功')
    importDialogVisible.value = false
    loadList()
  }
}

// ─── 列表显示逻辑 ──────────────────────────────────────────
const searchSchema = computed<FormSchema[]>(() => [
  {
    field: 'region',
    label: '地区',
    component: 'Select',
    componentProps: {
      placeholder: '请选择地区',
      options: [
        { label: '重庆市', value: 'CQ' },
        { label: '四川省', value: 'SC' }
      ]
    }
  },
  {
    field: 'year',
    label: '年份',
    component: 'Select',
    componentProps: {
      placeholder: '请选择年份',
      options: [
        { label: '2026', value: 2026 },
        { label: '2025', value: 2025 }
      ]
    }
  },
  {
    field: 'keyword',
    label: '关键词',
    component: 'Input',
    componentProps: {
      placeholder: '标准名称/版本号'
    }
  }
])

const searchParams = ref<Record<string, any>>({})
const setSearchParams = (data: Record<string, any>) => {
  searchParams.value = data
  loadList()
}

const standardList = ref([])
const loading = ref(false)

const tableColumns = reactive<TableColumn[]>([
  { field: 'id', label: 'ID', width: '60px' },
  { field: 'name', label: '标准名称', minWidth: '220px' },
  { field: 'region', label: '地区', width: '90px' },
  { field: 'year', label: '年份', width: '80px' },
  { field: 'version', label: '版本号', width: '100px' },
  {
    field: 'status',
    label: '状态',
    width: '90px',
    slots: {
      default: (data: any) => {
        const val = data.row.status
        let type: 'success' | 'warning' | 'danger' = 'warning'
        if (val === '已发布') type = 'success'
        if (val === '已作废') type = 'danger'
        return <ElTag type={type}>{val || '草稿'}</ElTag>
      }
    }
  },
  {
    field: 'action',
    label: '操作',
    width: '150px',
    slots: {
      default: (data: any) => {
        return (
          <>
            <BaseButton type="primary" link size="small">
              详情
            </BaseButton>
            <BaseButton type="success" link size="small">
              发布
            </BaseButton>
          </>
        )
      }
    }
  }
])

const loadList = async () => {
  loading.value = true
  const res = await getFitnessStandardListApi(searchParams.value).catch(() => null)
  if (res) {
    standardList.value = res.data
  }
  loading.value = false
}

onMounted(() => {
  loadList()
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

    <div class="mb-10px flex gap-10px">
      <ElUpload
        :show-file-list="false"
        :http-request="handleExcelImport"
        accept=".xlsx, .xls"
      >
        <BaseButton type="success" :loading="importLoading">导入 Excel 标准</BaseButton>
      </ElUpload>
      <BaseButton type="warning">手工录入</BaseButton>
    </div>

    <ElCard shadow="never" title="体测标准列表">
      <Table :columns="tableColumns" :data="standardList" :loading="loading" :pagination="false" />
    </ElCard>

    <ElDialog v-model="importDialogVisible" title="标准导入确认" width="1000px">
      <div class="mb-20px">
        <div class="mb-10px font-bold">1. 完善基本信息</div>
        <div class="grid grid-cols-3 gap-10px">
          <div class="flex items-center">
            <span class="w-80px">标准名称：</span>
            <ElInput v-model="importForm.name" placeholder="请输入标准名称" class="flex-1" />
          </div>
          <div class="flex items-center">
            <span class="w-80px">地区：</span>
            <ElInput v-model="importForm.region" placeholder="请输入地区" class="flex-1" />
          </div>
          <div class="flex items-center">
            <span class="w-80px">版本号：</span>
            <ElInput v-model="importForm.version" placeholder="请输入版本号" class="flex-1" />
          </div>
          <div class="flex items-center">
            <span class="w-80px">学段：</span>
            <ElSelect v-model="importForm.stage_type" class="flex-1">
              <ElOption v-for="s in stageOptions" :key="s.value" :label="s.label" :value="s.value" />
            </ElSelect>
          </div>
        </div>
      </div>
      <div class="mb-10px font-bold">2. 预览项目解析结果</div>
      <Table
        :columns="[
          { field: 'item_name', label: '项目名称' },
          { field: 'gender', label: '性别' },
          { field: 'calc_mode', label: '模式' },
          { field: 'full_threshold', label: '满分阈值' },
          { field: 'excellent_threshold', label: '优秀阈值' },
          { field: 'pass_threshold', label: '及格阈值' },
          { field: 'max_score', label: '满分分值' }
        ]"
        :data="importedItems"
        :pagination="false"
      />
      <template #footer>
        <BaseButton type="primary" @click="handleConfirmImport">确认导入</BaseButton>
        <BaseButton @click="importDialogVisible = false">取消</BaseButton>
      </template>
    </ElDialog>
  </ContentWrap>
</template>
