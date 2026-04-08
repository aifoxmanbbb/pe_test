<script setup lang="tsx">
import { onMounted, reactive, ref , computed} from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import {
  ElCard,
  ElTag,
  ElCheckboxGroup,
  ElCheckbox,
  ElAlert
} from 'element-plus'
import { Table, TableColumn } from '@/components/Table'
import { BaseButton } from '@/components/Button'
import {
  getFitnessReportConfigApi,
  getFitnessBatchOptionsApi,
  exportFitnessReportApi
} from '@/api/vadmin/fitness'

defineOptions({
  name: 'FitnessReport'
})

const batchOptions = ref([])

const searchSchema = computed<FormSchema[]>(() => [
  {
    field: 'report_type',
    label: '报表类型',
    component: 'Select',
    componentProps: {
      placeholder: '请选择类型',
      options: [
        { label: '学生体测报表', value: 'student' },
        { label: '班级汇总报表', value: 'class' },
        { label: '年级分析报表', value: 'grade' }
      ]
    }
  },
  {
    field: 'batch_id',
    label: '批次',
    component: 'Select',
    componentProps: {
      placeholder: '请选择批次',
      options: batchOptions.value,
      filterable: true
    }
  },
  {
    field: 'school_name',
    label: '学校',
    component: 'Input',
    componentProps: { placeholder: '请输入学校名称' }
  },
  {
    field: 'grade_name',
    label: '年级',
    component: 'Input',
    componentProps: { placeholder: '请输入年级' }
  },
  {
    field: 'class_name',
    label: '班级',
    component: 'Input',
    componentProps: { placeholder: '请输入班级' }
  }
])

const searchParams = ref<Record<string, any>>({})
const setSearchParams = (data: Record<string, any>) => {
  searchParams.value = data
}

// 导出字段：体测口径不含总分/总体状态
const exportFields = ref([
  'student_base',
  'raw_value',
  'score',
  'item_status',
  'version'
])

const exportStatus = ref({
  show: false,
  success: true,
  fileName: '',
  url: '',
  errorMsg: ''
})

const handleExport = async () => {
  if (!searchParams.value.batch_id) {
    ElMessage.warning('请先选择批次')
    return
  }
  
  exportStatus.value.show = true
  exportStatus.value.success = true
  exportStatus.value.fileName = '正在生成中...'
  
  try {
    const res = await exportFitnessReportApi(searchParams.value)
    if (res && res.data && res.data.url) {
      exportStatus.value.success = true
      exportStatus.value.url = res.data.url
      exportStatus.value.fileName = res.data.url.split('/').pop() || '报表.xlsx'
      ElMessage.success('报表生成成功')
    } else {
      throw new Error('生成失败')
    }
  } catch (e: any) {
    exportStatus.value.success = false
    exportStatus.value.errorMsg = e.message || '生成报表时发生错误'
    ElMessage.error('报表生成失败')
  }
}

const handleDownload = () => {
  if (exportStatus.value.url) {
    window.open(exportStatus.value.url)
  }
}

const loadBatchOptions = async () => {
  const res = await getFitnessBatchOptionsApi().catch(() => null)
  if (res && Array.isArray(res.data)) {
    batchOptions.value = res.data
  }
}

const historyData = ref([
  { id: 1, time: '2026-03-21 10:30', type: '学生报表', status: '成功', version: 'FT-2026.1' },
  { id: 2, time: '2026-03-20 16:00', type: '班级报表', status: '失败', version: 'FT-2026.1' }
])

const tableColumns = reactive<TableColumn[]>([
  { field: 'id', label: '序号', width: '70px' },
  { field: 'time', label: '导出时间', width: '180px' },
  { field: 'type', label: '报表类型', width: '120px' },
  {
    field: 'status',
    label: '状态',
    width: '90px',
    slots: {
      default: (data: any) => {
        const val = data.row.status
        return <ElTag type={val === '成功' ? 'success' : 'danger'}>{val}</ElTag>
      }
    }
  },
  { field: 'version', label: '标准版本号', width: '130px' },
  {
    field: 'action',
    label: '操作',
    minWidth: '140px',
    slots: {
      default: (data: any) => (
        <>
          <BaseButton type="primary" link size="small">下载</BaseButton>
          {data.row.status === '失败' && (
            <BaseButton type="danger" link size="small">重试</BaseButton>
          )}
        </>
      )
    }
  }
])

const loadConfig = async () => {
  const res = await getFitnessReportConfigApi().catch(() => null)
  if (!res) return
  const data = res.data || {}
  if (Array.isArray(data.history)) {
    historyData.value = data.history
  }
}
onMounted(() => {
  loadConfig()
  loadBatchOptions()
})
</script>

<template>
  <ContentWrap>
    <div class="flex justify-between items-start mb-20px">
      <Search
        :schema="searchSchema"
        @search="setSearchParams"
        @reset="setSearchParams"
        class="flex-grow"
      />
      <div class="ml-10px mt-2px">
        <BaseButton type="primary" @click="handleExport">生成报表</BaseButton>
      </div>
    </div>

    <!-- 导出字段选择 -->
    <ElCard shadow="never" class="mb-16px" header="导出字段选择">
      <div class="text-12px text-orange-400 mb-10px">
        ⚠ 体测报表不导出综合分、总分、总平均分和总体及格/优秀/满分状态，仅导出单项口径字段。
      </div>
      <ElCheckboxGroup v-model="exportFields">
        <ElCheckbox label="student_base">学生基础信息</ElCheckbox>
        <ElCheckbox label="raw_value">项目成绩</ElCheckbox>
        <ElCheckbox label="score">项目评分成绩</ElCheckbox>
        <ElCheckbox label="item_status">单项及格/优秀/满分状态</ElCheckbox>
        <ElCheckbox label="version">标准版本号</ElCheckbox>
      </ElCheckboxGroup>
    </ElCard>

    <!-- 导出结果 -->
    <div v-if="exportStatus.show" class="mb-16px">
      <ElAlert
        v-if="exportStatus.success"
        title="本次导出成功"
        type="success"
        show-icon
        :closable="false"
      >
        <p>文件名：{{ exportStatus.fileName }}</p>
        <BaseButton type="primary" link>立即下载</BaseButton>
      </ElAlert>
      <ElAlert v-else title="本次导出失败" type="error" show-icon :closable="false">
        <p>错误原因：{{ exportStatus.errorMsg }}</p>
        <BaseButton type="danger" link @click="handleExport">重新生成</BaseButton>
      </ElAlert>
    </div>

    <!-- 历史记录 -->
    <ElCard shadow="never" header="最近导出记录">
      <Table :columns="tableColumns" :data="historyData" :pagination="false" />
    </ElCard>
  </ContentWrap>
</template>
