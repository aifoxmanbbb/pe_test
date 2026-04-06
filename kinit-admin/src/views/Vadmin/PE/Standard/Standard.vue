<script setup lang="tsx">
import { onMounted, reactive, ref } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import { ElTag, ElDialog, ElDescriptions, ElDescriptionsItem } from 'element-plus'
import { Table, TableColumn } from '@/components/Table'
import { BaseButton } from '@/components/Button'
import { getPeStandardListApi } from '@/api/vadmin/pe'

defineOptions({
  name: 'PEStandard'
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
    field: 'exam_type',
    label: '考试类型',
    component: 'Select',
    componentProps: {
      placeholder: '请选择考试类型',
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

const standardList = ref([
  {
    id: 1,
    name: '重庆市2026年体育初中标准',
    region: '重庆市',
    year: 2026,
    exam_type: '初中',
    version: 'V2026.1',
    status: '已发布',
    source: 'PDF识别+人工确认',
    ref_count: 12
  },
  {
    id: 2,
    name: '重庆市2025年体育初中标准',
    region: '重庆市',
    year: 2025,
    exam_type: '初中',
    version: 'V2025.2',
    status: '草稿',
    source: 'Excel导入',
    ref_count: 0
  }
])

const thresholdMap = ref<Record<number, any[]>>({
  1: [
    {
      item: '1000米/800米(门槛项)',
      gender: '男/女',
      full: '-',
      excellent: '-',
      pass: '合格判定',
      mode: '门槛判定'
    },
    {
      item: '1分钟跳绳',
      gender: '男/女',
      full: '185次(20分)',
      excellent: '170次(18分)',
      pass: '140次(14分)',
      mode: '分段计分'
    },
    {
      item: '立定跳远',
      gender: '男',
      full: '2.40m(15分)',
      excellent: '2.26m(13分)',
      pass: '2.05m(10分)',
      mode: '分段计分'
    },
    {
      item: '立定跳远',
      gender: '女',
      full: '2.03m(15分)',
      excellent: '1.89m(13分)',
      pass: '1.76m(10分)',
      mode: '分段计分'
    }
  ],
  2: [
    {
      item: '1分钟跳绳',
      gender: '男/女',
      full: '180次(20分)',
      excellent: '165次(18分)',
      pass: '135次(14分)',
      mode: '分段计分'
    }
  ]
})

const tableColumns = reactive<TableColumn[]>([
  { field: 'id', label: 'ID', width: '60px' },
  { field: 'name', label: '标准名称', minWidth: '220px' },
  { field: 'region', label: '地区', width: '90px' },
  { field: 'year', label: '年份', width: '80px' },
  { field: 'exam_type', label: '考试类型', width: '90px' },
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
        return <ElTag type={type}>{val}</ElTag>
      }
    }
  },
  { field: 'source', label: '来源', minWidth: '140px' },
  { field: 'ref_count', label: '批次引用数', width: '100px' },
  {
    field: 'action',
    label: '操作',
    minWidth: '240px',
    slots: {
      default: (data: any) => {
        return (
          <>
            <BaseButton type="primary" link size="small" onClick={() => openDetail(data.row)}>
              详情
            </BaseButton>
            <BaseButton type="primary" link size="small">
              修改
            </BaseButton>
            {data.row.status === '草稿' && (
              <BaseButton type="success" link size="small">
                人工确认
              </BaseButton>
            )}
            <BaseButton type="warning" link size="small">
              复制新版
            </BaseButton>
            {data.row.status !== '已发布' && (
              <BaseButton type="primary" link size="small">
                发布
              </BaseButton>
            )}
          </>
        )
      }
    }
  }
])

const thresholdColumns = reactive<TableColumn[]>([
  { field: 'item', label: '项目', minWidth: '150px' },
  { field: 'gender', label: '性别', width: '80px' },
  { field: 'full', label: '满分阈值', minWidth: '120px' },
  { field: 'excellent', label: '优秀阈值', minWidth: '120px' },
  { field: 'pass', label: '及格阈值', minWidth: '120px' },
  { field: 'mode', label: '计分模式', minWidth: '100px' }
])

const detailVisible = ref(false)
const currentStandard = ref<any>(null)
const currentThresholds = ref<any[]>([])

const openDetail = (row: any) => {
  currentStandard.value = row
  currentThresholds.value = thresholdMap.value[row.id] || []
  detailVisible.value = true
}

const loadList = async () => {
  const res = await getPeStandardListApi(searchParams.value).catch(() => null)
  if (!res) return
  const rows = Array.isArray(res.data) ? res.data : []
  standardList.value = rows
  thresholdMap.value = rows.reduce((acc: Record<number, any[]>, item: any) => {
    acc[item.id] = Array.isArray(item.thresholds) ? item.thresholds : []
    return acc
  }, {})
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
      <BaseButton type="primary">导入 PDF</BaseButton>
      <BaseButton type="success">导入 Excel</BaseButton>
      <BaseButton type="warning">手工录入</BaseButton>
    </div>

    <ElCard shadow="never" title="标准版本列表">
      <Table :columns="tableColumns" :data="standardList" :pagination="false" />
    </ElCard>

    <ElDialog v-model="detailVisible" title="标准详情" width="980px" destroy-on-close>
      <ElDescriptions v-if="currentStandard" :column="3" border class="mb-20px">
        <ElDescriptionsItem label="标准名称">{{ currentStandard.name }}</ElDescriptionsItem>
        <ElDescriptionsItem label="地区/年份"
          >{{ currentStandard.region }} / {{ currentStandard.year }}</ElDescriptionsItem
        >
        <ElDescriptionsItem label="考试类型">{{ currentStandard.exam_type }}</ElDescriptionsItem>
        <ElDescriptionsItem label="版本号">{{ currentStandard.version }}</ElDescriptionsItem>
        <ElDescriptionsItem label="状态">{{ currentStandard.status }}</ElDescriptionsItem>
        <ElDescriptionsItem label="来源">{{ currentStandard.source }}</ElDescriptionsItem>
      </ElDescriptions>

      <ElCard shadow="never" title="项目阈值配置（按性别区分）">
        <Table :columns="thresholdColumns" :data="currentThresholds" :pagination="false" />
      </ElCard>
    </ElDialog>
  </ContentWrap>
</template>
