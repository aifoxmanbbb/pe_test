<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import type { FormSchema } from '@/components/Form'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import type { SearchExpose } from '@/components/Search'
import { Echart } from '@/components/Echart'
import { ElCard, ElCol, ElEmpty, ElRow, ElStatistic, ElTable, ElTableColumn, ElTabs, ElTabPane } from 'element-plus'
import { getPeBatchOptionsApi, getPeOverviewApi } from '@/api/vadmin/pe'
import { getClassOptionsApi, getGradeOptionsApi, getSchoolOptionsApi } from '@/api/vadmin/sport'

defineOptions({ name: 'PEOverview' })

const stageType = ref<'mid' | 'high'>('mid')
const lastParams = ref<Record<string, any>>({})
const searchRef = ref<SearchExpose>()

const batchOptions = ref<any[]>([])
const schoolOptions = ref<any[]>([])
const gradeOptions = ref<any[]>([])
const classOptions = ref<any[]>([])

const result = ref<any>(null)
const classList = ref<any[]>([])

const searchSchema = computed<FormSchema[]>(() => [
  {
    field: 'batch_id',
    label: '批次',
    component: 'Select',
    componentProps: { options: batchOptions.value, filterable: true, clearable: true }
  },
  {
    field: 'school_name',
    label: '学校',
    component: 'Select',
    componentProps: {
      options: schoolOptions.value,
      filterable: true,
      clearable: true,
      onChange: async (val: string) => {
        gradeOptions.value = []
        classOptions.value = []
        if (!val) return
        const res = await getGradeOptionsApi({ school_name: val }).catch(() => null)
        if (!res) return
        gradeOptions.value = (res.data || []).map((i: any) => ({ label: i.label, value: i.grade_name || i.value }))
      }
    }
  },
  {
    field: 'grade_name',
    label: '年级',
    component: 'Select',
    componentProps: {
      options: gradeOptions.value,
      clearable: true,
      onChange: async (val: string) => {
        classOptions.value = []
        if (!val) return
        const res = await getClassOptionsApi({ grade_name: val }).catch(() => null)
        if (!res) return
        classOptions.value = (res.data || []).map((i: any) => ({ label: i.label, value: i.class_name || i.value }))
      }
    }
  },
  {
    field: 'class_name',
    label: '班级',
    component: 'Select',
    componentProps: { options: classOptions.value, clearable: true }
  }
])

const mainTitle = computed(() => {
  const p = lastParams.value
  const batchText = batchOptions.value.find((b: any) => b.value === p.batch_id)?.label || '某批次'
  const schoolText = p.school_name || '所有学校'
  return `${batchText}-${schoolText} 体育项目情况分析`
})

const kpi = computed(() => {
  const data = result.value?.kpi || {}
  return {
    totalStudents: data.total_students || 0,
    avgScore: data.avg_score || 0,
    passRate: data.pass_rate || 0,
    excellentRate: data.excellent_rate || 0,
    fullRate: data.full_rate || 0
  }
})

const itemAvgOptions = reactive<any>({
  title: { text: '项目均分对比', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
  tooltip: { trigger: 'axis' },
  grid: { left: 30, right: 20, bottom: 40, top: 50, containLabel: true },
  xAxis: { type: 'category', data: [], axisLabel: { interval: 0, rotate: 22 } },
  yAxis: { type: 'value', name: '分值' },
  series: [
    {
      name: '项目均分',
      type: 'bar',
      data: [],
      itemStyle: { color: '#409EFF' },
      label: { show: true, position: 'top' },
      markLine: { symbol: ['none', 'none'], data: [] }
    }
  ]
})

const classRateOptions = reactive<any>({
  title: { text: '班级分层率', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0 },
  grid: { left: 25, right: 20, top: 45, bottom: 50, containLabel: true },
  xAxis: { type: 'category', data: [], axisLabel: { interval: 0, rotate: 20 } },
  yAxis: { type: 'value', max: 100, name: '%' },
  series: [
    { name: '及格率', type: 'bar', data: [], itemStyle: { color: '#E6A23C' } },
    { name: '优秀率', type: 'bar', data: [], itemStyle: { color: '#67C23A' } },
    { name: '满分率', type: 'bar', data: [], itemStyle: { color: '#000000' } }
  ]
})

const batchTrendOptions = reactive<any>({
  title: { text: '批次趋势', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0 },
  grid: { left: 25, right: 20, top: 45, bottom: 50, containLabel: true },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', name: '总均分' },
  series: [
    { name: '总均分', type: 'line', smooth: true, data: [], itemStyle: { color: '#409EFF' }, label: { show: true, position: 'top' } },
    { name: '及格线', type: 'line', smooth: true, data: [], lineStyle: { type: 'dashed', color: '#E6A23C' } },
    { name: '优秀线', type: 'line', smooth: true, data: [], lineStyle: { type: 'dashed', color: '#67C23A' } },
    { name: '满分线', type: 'line', smooth: true, data: [], lineStyle: { type: 'dashed', color: '#000000' } }
  ]
})

const buildCharts = (data: any) => {
  const itemAvg = data?.item_avg || {}
  const threshold = itemAvg.threshold || {}
  itemAvgOptions.xAxis.data = itemAvg.items || []
  itemAvgOptions.series[0].data = itemAvg.values || []
  itemAvgOptions.series[0].markLine.data = [
    { yAxis: threshold.pass || 10, name: '及格阈值', lineStyle: { color: '#E6A23C', type: 'dashed' } },
    { yAxis: threshold.excellent || 14, name: '优秀阈值', lineStyle: { color: '#67C23A', type: 'dashed' } },
    { yAxis: threshold.full || 20, name: '满分阈值', lineStyle: { color: '#000000', type: 'dashed' } }
  ]

  const classRate = data?.class_rate || {}
  classRateOptions.xAxis.data = classRate.classes || []
  classRateOptions.series[0].data = classRate.pass_rate || []
  classRateOptions.series[1].data = classRate.excellent_rate || []
  classRateOptions.series[2].data = classRate.full_rate || []

  const trend = data?.batch_trend || {}
  batchTrendOptions.xAxis.data = trend.batches || []
  batchTrendOptions.series[0].data = trend.avg_score || []
  batchTrendOptions.series[1].data = trend.pass_line || []
  batchTrendOptions.series[2].data = trend.excellent_line || []
  batchTrendOptions.series[3].data = trend.full_line || []
}

const loadData = async (params: Record<string, any> = lastParams.value) => {
  const query = { ...params, stage_type: stageType.value }
  lastParams.value = { ...params }
  const res = await getPeOverviewApi(query).catch(() => null)
  if (!res?.data) {
    result.value = null
    classList.value = []
    return
  }
  result.value = res.data
  classList.value = res.data.class_list || []
  buildCharts(res.data)
}

const loadBatchOptions = async () => {
  const batchRes = await getPeBatchOptionsApi({ stage_type: stageType.value }).catch(() => null)
  batchOptions.value = batchRes?.data || []
}

const loadSchoolOptions = async () => {
  const schoolRes = await getSchoolOptionsApi({ stage_type: stageType.value }).catch(() => null)
  schoolOptions.value = (schoolRes?.data || []).map((i: any) => ({ label: i.label, value: i.school_name || i.value }))
}

const buildDefaultParams = () => {
  const params: Record<string, any> = { grade_name: null, class_name: null }
  if (batchOptions.value.length) params.batch_id = batchOptions.value[0].value
  if (schoolOptions.value.length) params.school_name = schoolOptions.value[0].value
  return params
}

const syncSearchValues = async (params: Record<string, any>) => {
  await nextTick()
  await searchRef.value?.setValues(params)
}

const onTabChange = async () => {
  lastParams.value = {}
  gradeOptions.value = []
  classOptions.value = []
  await Promise.all([loadBatchOptions(), loadSchoolOptions()])
  const params = buildDefaultParams()
  await syncSearchValues(params)
  await loadData(params)
}

const schoolSpanMethod = ({ rowIndex, columnIndex }: { rowIndex: number; columnIndex: number }) => {
  if (columnIndex !== 0) return [1, 1]
  const rows = classList.value
  const current = rows[rowIndex]
  const prev = rows[rowIndex - 1]
  if (prev && prev.school_name === current.school_name) {
    return [0, 0]
  }
  let count = 1
  for (let i = rowIndex + 1; i < rows.length; i += 1) {
    if (rows[i].school_name === current.school_name) count += 1
    else break
  }
  return [count, 1]
}

onMounted(async () => {
  await Promise.all([loadBatchOptions(), loadSchoolOptions()])
  const params = buildDefaultParams()
  await syncSearchValues(params)
  await loadData(params)
})
</script>

<template>
  <ContentWrap>
    <ElTabs v-model="stageType" class="mb-10px" @tab-change="onTabChange">
      <ElTabPane label="初中" name="mid" />
      <ElTabPane label="高中" name="high" />
    </ElTabs>

    <Search ref="searchRef" :schema="searchSchema" class="mb-12px" @search="loadData" @reset="loadData" />

    <ElCard shadow="never" class="analysis-card">
      <div class="card-title">{{ mainTitle }}</div>

      <div v-if="!result || !kpi.totalStudents" class="py-30px">
        <ElEmpty description="暂无可展示数据" />
      </div>

      <template v-else>
        <ElRow :gutter="14" class="mb-14px">
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover"><ElStatistic title="参考人数" :value="kpi.totalStudents" /></ElCard></ElCol>
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover"><ElStatistic title="平均分" :value="kpi.avgScore" :precision="2" /></ElCard></ElCol>
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover" class="kpi-pass"><ElStatistic title="及格率" :value="kpi.passRate" suffix="%" :precision="2" /></ElCard></ElCol>
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover" class="kpi-excellent"><ElStatistic title="优秀率" :value="kpi.excellentRate" suffix="%" :precision="2" /></ElCard></ElCol>
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover" class="kpi-full"><ElStatistic title="满分率" :value="kpi.fullRate" suffix="%" :precision="2" /></ElCard></ElCol>
        </ElRow>

        <ElRow :gutter="14" class="mb-14px">
          <ElCol :span="14"><Echart :options="itemAvgOptions" height="320px" /></ElCol>
          <ElCol :span="10"><Echart :options="classRateOptions" height="320px" /></ElCol>
        </ElRow>

        <Echart :options="batchTrendOptions" height="300px" class="mb-14px" />

        <ElTable :data="classList" :span-method="schoolSpanMethod" stripe>
          <ElTableColumn prop="school_name" label="学校" min-width="160" />
          <ElTableColumn prop="class_name" label="班级" min-width="120" />
          <ElTableColumn label="门槛项" min-width="150" align="center">
            <template #default="{ row }">
              <div>{{ row.gate_score }}</div>
              <div class="sub-cell">{{ row.gate_point }}分</div>
            </template>
          </ElTableColumn>
          <ElTableColumn label="跳绳" min-width="130" align="center">
            <template #default="{ row }"><div>{{ row.rope_score }}</div><div class="sub-cell">{{ row.rope_point }}分</div></template>
          </ElTableColumn>
          <ElTableColumn label="跳远" min-width="130" align="center">
            <template #default="{ row }"><div>{{ row.jump_score }}</div><div class="sub-cell">{{ row.jump_point }}分</div></template>
          </ElTableColumn>
          <ElTableColumn label="实心球" min-width="130" align="center">
            <template #default="{ row }"><div>{{ row.ball_score }}</div><div class="sub-cell">{{ row.ball_point }}分</div></template>
          </ElTableColumn>
          <ElTableColumn prop="avg_total" label="总均分" min-width="100" align="center" />
          <ElTableColumn prop="pass_rate" label="及格率" min-width="90" align="center">
            <template #default="{ row }"><span class="kpi-pass-text">{{ row.pass_rate }}%</span></template>
          </ElTableColumn>
          <ElTableColumn prop="excellent_rate" label="优秀率" min-width="90" align="center">
            <template #default="{ row }"><span class="kpi-excellent-text">{{ row.excellent_rate }}%</span></template>
          </ElTableColumn>
          <ElTableColumn prop="full_rate" label="满分率" min-width="90" align="center">
            <template #default="{ row }"><span class="kpi-full-text">{{ row.full_rate }}%</span></template>
          </ElTableColumn>
        </ElTable>
      </template>
    </ElCard>
  </ContentWrap>
</template>

<style scoped>
.analysis-card { border-radius: 10px; }
.card-title { text-align: center; font-size: 22px; font-weight: 700; margin-bottom: 16px; }
.sub-cell { color: #909399; font-size: 12px; }
.analysis-card :deep(.el-statistic__head) { font-size: 14px; color: #606266; font-weight: 500; }
.kpi-pass :deep(.el-statistic__content-value), .kpi-pass :deep(.el-statistic__content), .kpi-pass-text { color: #E6A23C !important; }
.kpi-fail :deep(.el-statistic__content-value), .kpi-fail :deep(.el-statistic__content), .kpi-fail-text { color: #F56C6C !important; }
.kpi-excellent :deep(.el-statistic__content-value), .kpi-excellent :deep(.el-statistic__content), .kpi-excellent-text { color: #67C23A !important; }
.kpi-full :deep(.el-statistic__content-value), .kpi-full :deep(.el-statistic__content), .kpi-full-text { color: #000000 !important; }
</style>

