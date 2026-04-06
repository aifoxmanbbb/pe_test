<script setup lang="tsx">
import { onMounted, reactive, ref } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import type { FormSchema } from '@/components/Form'
import {
  ElTag,
  ElDialog,
  ElDescriptions,
  ElDescriptionsItem,
  ElMessage
} from 'element-plus'
import { Table, TableColumn } from '@/components/Table'
import { BaseButton } from '@/components/Button'
import { getFitnessStandardListApi } from '@/api/vadmin/fitness'

defineOptions({
  name: 'FitnessStandard'
})

const searchSchema = reactive<FormSchema[]>([
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
    field: 'stage',
    label: '学段',
    component: 'Select',
    componentProps: {
      placeholder: '请选择学段',
      options: [
        { label: '初中', value: 'mid' },
        { label: '高中', value: 'high' }
      ]
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
        { label: '已发布', value: 'published' },
        { label: '已作废', value: 'void' }
      ]
    }
  },
  {
    field: 'keyword',
    label: '关键词',
    component: 'Input',
    componentProps: { placeholder: '标准名称/版本号' }
  }
])

const searchParams = ref<Record<string, any>>({})

const standardList = ref([
  {
    id: 1,
    name: '重庆市2026体测标准',
    region: '重庆市',
    year: 2026,
    stage: '初中',
    version: 'FT-2026.1',
    status: '已发布',
    source: 'PDF识别+人工确认',
    ref_count: 8
  },
  {
    id: 2,
    name: '重庆市2025体测标准',
    region: '重庆市',
    year: 2025,
    stage: '初中',
    version: 'FT-2025.2',
    status: '草稿',
    source: 'Excel导入',
    ref_count: 0
  }
])

// 详情弹窗
const detailVisible = ref(false)
const currentStandard = ref<any>(null)
const currentThresholds = ref<any[]>([])

// 内置阈值样例（正式从 thresholds 字段读取）
const thresholdSamples: Record<number, any[]> = {
  1: [
    { item: 'BMI', gender: '男/女', full: 'BMI 18.5~23.9', excellent: 'BMI 18.5~24.9', pass: 'BMI 15~27.9', mode: '阈值判定' },
    { item: '肺活量', gender: '男', full: '≥5000ml(100分)', excellent: '≥4200ml(80分)', pass: '≥3000ml(60分)', mode: '分段计分' },
    { item: '肺活量', gender: '女', full: '≥3500ml(100分)', excellent: '≥3000ml(80分)', pass: '≥2100ml(60分)', mode: '分段计分' },
    { item: '50米跑', gender: '男', full: '≤6.7秒(100分)', excellent: '≤7.2秒(80分)', pass: '≤8.0秒(60分)', mode: '分段计分' },
    { item: '50米跑', gender: '女', full: '≤7.5秒(100分)', excellent: '≤8.0秒(80分)', pass: '≤8.8秒(60分)', mode: '分段计分' },
    { item: '坐位体前屈', gender: '男', full: '≥23cm(100分)', excellent: '≥15cm(80分)', pass: '≥6cm(60分)', mode: '分段计分' },
    { item: '1分钟跳绳', gender: '男/女', full: '≥185次(100分)', excellent: '≥155次(80分)', pass: '≥110次(60分)', mode: '分段计分' },
    { item: '耐力跑', gender: '男(1000m)', full: '≤3\'50"(100分)', excellent: '≤4\'20"(80分)', pass: '≤5\'00"(60分)', mode: '分段计分' },
    { item: '耐力跑', gender: '女(800m)', full: '≤3\'30"(100分)', excellent: '≤4\'00"(80分)', pass: '≤4\'40"(60分)', mode: '分段计分' }
  ],
  2: [
    { item: '1分钟跳绳', gender: '男/女', full: '≥180次(100分)', excellent: '≥150次(80分)', pass: '≥105次(60分)', mode: '分段计分' }
  ]
}

const openDetail = (row: any) => {
  currentStandard.value = row
  currentThresholds.value = row.thresholds || thresholdSamples[row.id] || []
  detailVisible.value = true
}

const handlePublish = (row: any) => {
  ElMessage.success(`标准「${row.name}」已发布`)
  row.status = '已发布'
}

const handleConfirm = (row: any) => {
  ElMessage.success(`标准「${row.name}」人工确认通过，可发布`)
}

const handleClone = (row: any) => {
  ElMessage.info(`已复制「${row.name}」为新草稿版本，请修改版本号后发布`)
}

const thresholdColumns = reactive<TableColumn[]>([
  { field: 'item', label: '项目', minWidth: '130px' },
  { field: 'gender', label: '性别', width: '110px' },
  { field: 'full', label: '满分阈值', minWidth: '160px' },
  { field: 'excellent', label: '优秀阈值', minWidth: '160px' },
  { field: 'pass', label: '及格阈值', minWidth: '160px' },
  { field: 'mode', label: '计分模式', width: '110px' }
])

const tableColumns = reactive<TableColumn[]>([
  { field: 'id', label: 'ID', width: '60px' },
  { field: 'name', label: '标准名称', minWidth: '220px' },
  { field: 'region', label: '地区', width: '90px' },
  { field: 'year', label: '年份', width: '80px' },
  { field: 'stage', label: '学段', width: '80px' },
  { field: 'version', label: '版本号', width: '110px' },
  {
    field: 'status',
    label: '状态',
    width: '90px',
    slots: {
      default: (data: any) => {
        const val = data.row.status
        const type = val === '已发布' ? 'success' : val === '已作废' ? 'danger' : 'warning'
        return <ElTag type={type}>{val}</ElTag>
      }
    }
  },
  { field: 'source', label: '来源', minWidth: '140px' },
  { field: 'ref_count', label: '批次引用数', width: '100px' },
  {
    field: 'action',
    label: '操作',
    minWidth: '260px',
    slots: {
      default: (data: any) => (
        <>
          <BaseButton type="primary" link size="small" onClick={() => openDetail(data.row)}>
            详情
          </BaseButton>
          <BaseButton type="primary" link size="small">
            修改
          </BaseButton>
          {data.row.status === '草稿' && (
            <BaseButton type="warning" link size="small" onClick={() => handleConfirm(data.row)}>
              人工确认
            </BaseButton>
          )}
          <BaseButton type="info" link size="small" onClick={() => handleClone(data.row)}>
            复制新版
          </BaseButton>
          {data.row.status !== '已发布' && (
            <BaseButton type="success" link size="small" onClick={() => handlePublish(data.row)}>
              发布
            </BaseButton>
          )}
        </>
      )
    }
  }
])

const setSearchParams = (params: Record<string, any>) => {
  searchParams.value = params
  loadList()
}

const loadList = async () => {
  const res = await getFitnessStandardListApi(searchParams.value).catch(() => null)
  if (!res) return
  const rows = Array.isArray(res.data) ? res.data : []
  if (rows.length > 0) {
    standardList.value = rows
  }
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
      class="mb-16px"
    />

    <!-- 操作按钮 -->
    <div class="mb-12px flex gap-10px">
      <BaseButton type="primary">导入 PDF</BaseButton>
      <BaseButton type="success">导入表格</BaseButton>
      <BaseButton type="warning">手工录入</BaseButton>
    </div>

    <!-- 标准列表 -->
    <ElCard shadow="never" header="体测标准版本列表">
      <Table :columns="tableColumns" :data="standardList" :pagination="false" />
    </ElCard>

    <!-- 详情弹窗 -->
    <ElDialog v-model="detailVisible" title="体测标准详情" width="1020px" destroy-on-close>
      <ElDescriptions v-if="currentStandard" :column="3" border class="mb-20px">
        <ElDescriptionsItem label="标准名称">{{ currentStandard.name }}</ElDescriptionsItem>
        <ElDescriptionsItem label="地区/年份">
          {{ currentStandard.region }} / {{ currentStandard.year }}
        </ElDescriptionsItem>
        <ElDescriptionsItem label="学段">{{ currentStandard.stage }}</ElDescriptionsItem>
        <ElDescriptionsItem label="版本号">{{ currentStandard.version }}</ElDescriptionsItem>
        <ElDescriptionsItem label="状态">{{ currentStandard.status }}</ElDescriptionsItem>
        <ElDescriptionsItem label="来源">{{ currentStandard.source }}</ElDescriptionsItem>
      </ElDescriptions>

      <div class="text-12px text-orange-400 mb-10px">
        ⚠ 体测标准仅展示单项成绩/分值/及格/优秀/满分阈值，不含综合分口径。
      </div>

      <ElCard shadow="never" header="项目阈值配置（按性别区分）">
        <Table :columns="thresholdColumns" :data="currentThresholds" :pagination="false" />
      </ElCard>
    </ElDialog>
  </ContentWrap>
</template>
