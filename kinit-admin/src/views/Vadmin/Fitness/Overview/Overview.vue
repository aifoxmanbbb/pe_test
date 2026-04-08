<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import type { FormSchema } from '@/components/Form'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import type { SearchExpose } from '@/components/Search'
import { Echart } from '@/components/Echart'
import { ElCard, ElCol, ElEmpty, ElRow, ElStatistic, ElTable, ElTableColumn, ElTabs, ElTabPane } from 'element-plus'
import { getFitnessBatchOptionsApi, getFitnessOverviewApi } from '@/api/vadmin/fitness'
import { getClassOptionsApi, getGradeOptionsApi, getSchoolOptionsApi } from '@/api/vadmin/sport'

defineOptions({ name: 'FitnessOverview' })

const stageType = ref<'primary' | 'mid' | 'high' | 'university'>('primary')
const lastParams = ref<Record<string, any>>({})
const searchRef = ref<SearchExpose>()

const batchOptions = ref<any[]>([])
const schoolOptions = ref<any[]>([])
const gradeOptions = ref<any[]>([])
const classOptions = ref<any[]>([])
const currentSchoolName = ref<string>('')

const result = ref<any>(null)
const classList = ref<any[]>([])

const searchSchema = computed<FormSchema[]>(() => [
  { field: 'batch_id', label: '批次', component: 'Select', componentProps: { options: batchOptions.value, filterable: true } },
  {
    field: 'school_name',
    label: '学校',
    component: 'Select',
    componentProps: {
      options: schoolOptions.value,
      clearable: true,
      filterable: true,
      onChange: async (val: string) => {
        currentSchoolName.value = val || ''
        gradeOptions.value = []
        classOptions.value = []
        await searchRef.value?.setValues({ grade_name: null, class_name: null })
        if (!val) return
        const res = await getGradeOptionsApi({ school_name: val }).catch(() => null)
        gradeOptions.value = (res?.data || []).map((i: any) => ({ label: i.label, value: i.grade_name || i.value }))
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
        await searchRef.value?.setValues({ class_name: null })
        const schoolName = currentSchoolName.value || searchRef.value?.formModel?.school_name
        if (!val || !schoolName) return
        const res = await getClassOptionsApi({
          school_name: schoolName,
          grade_name: val
        }).catch(() => null)
        classOptions.value = (res?.data || []).map((i: any) => ({ label: i.label, value: i.class_name || i.value }))
      }
    }
  },
  { field: 'class_name', label: '班级', component: 'Select', componentProps: { options: classOptions.value, clearable: true } }
])

const titleText = computed(() => {
  const p = lastParams.value
  const batchText = batchOptions.value.find((b: any) => b.value === p.batch_id)?.label || '某批次'
  return `${batchText}-${p.school_name || '所有学校'} 体质测试情况分析`
})

const itemAvgOptions = reactive<any>({
  title: { text: '单项平均分对比', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
  tooltip: { trigger: 'axis' },
  grid: { left: 25, right: 20, top: 45, bottom: 40, containLabel: true },
  xAxis: { type: 'category', data: [], axisLabel: { interval: 0, rotate: 20 } },
  yAxis: { type: 'value', name: '分值' },
  series: [
    {
      name: '单项均分',
      type: 'bar',
      data: [],
      itemStyle: { color: '#409EFF' },
      label: { show: true, position: 'top' },
      markLine: { symbol: ['none', 'none'], data: [] }
    }
  ]
})

const itemRateOptions = reactive<any>({
  title: { text: '单项达成率对比', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
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

const itemTrendOptions = reactive<any>({
  title: { text: '重点单项趋势', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0 },
  grid: { left: 25, right: 20, top: 45, bottom: 50, containLabel: true },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', name: '分值' },
  series: []
})

const schoolSpanMethod = ({ rowIndex, columnIndex }: { rowIndex: number; columnIndex: number }) => {
  if (columnIndex !== 0) return [1, 1]
  const rows = classList.value
  const current = rows[rowIndex]
  const prev = rows[rowIndex - 1]
  if (prev && prev.school_name === current.school_name) return [0, 0]
  let count = 1
  for (let i = rowIndex + 1; i < rows.length; i += 1) {
    if (rows[i].school_name === current.school_name) count += 1
    else break
  }
  return [count, 1]
}

const applyCharts = (data: any) => {
  const avgData = data?.item_avg || {}
  itemAvgOptions.xAxis.data = avgData.items || []
  itemAvgOptions.series[0].data = avgData.values || []
  const t = avgData.threshold || { pass: 60, excellent: 80, full: 100 }
  itemAvgOptions.series[0].markLine.data = [
    { yAxis: t.pass, name: '及格阈值', lineStyle: { color: '#E6A23C', type: 'dashed' } },
    { yAxis: t.excellent, name: '优秀阈值', lineStyle: { color: '#67C23A', type: 'dashed' } },
    { yAxis: t.full, name: '满分阈值', lineStyle: { color: '#000000', type: 'dashed' } }
  ]

  const rate = data?.item_rate || {}
  itemRateOptions.xAxis.data = rate.items || []
  itemRateOptions.series[0].data = rate.pass_rate || []
  itemRateOptions.series[1].data = rate.excellent_rate || []
  itemRateOptions.series[2].data = rate.full_rate || []

  const trend = data?.item_trend || {}
  itemTrendOptions.xAxis.data = trend.batches || []
  itemTrendOptions.series = (trend.series || []).map((s: any, idx: number) => ({
    name: s.name,
    type: 'line',
    smooth: true,
    data: s.values || [],
    label: { show: true, position: 'top' },
    itemStyle: { color: ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C'][idx % 4] }
  }))
}

const loadData = async (params: Record<string, any> = lastParams.value) => {
  const query = { ...params, stage_type: stageType.value }
  lastParams.value = { ...params }
  const res = await getFitnessOverviewApi(query).catch(() => null)
  if (!res?.data) {
    result.value = null
    classList.value = []
    return
  }
  result.value = res.data
  classList.value = res.data.class_list || []
  applyCharts(res.data)
}

const loadBatchOptions = async () => {
  const batchRes = await getFitnessBatchOptionsApi({ stage_type: stageType.value }).catch(() => null)
  batchOptions.value = batchRes?.data || []
}

const loadSchoolOptions = async () => {
  const schoolRes = await getSchoolOptionsApi({ stage_type: stageType.value }).catch(() => null)
  schoolOptions.value = (schoolRes?.data || []).map((i: any) => ({ label: i.label, value: i.school_name || i.value }))
}

const buildDefaultParams = async () => {
  const params: Record<string, any> = { batch_id: null, school_name: null, grade_name: null, class_name: null }
  if (batchOptions.value.length) params.batch_id = batchOptions.value[0].value
  if (schoolOptions.value.length) {
    params.school_name = schoolOptions.value[0].value
    currentSchoolName.value = params.school_name
    const gradeRes = await getGradeOptionsApi({ school_name: params.school_name }).catch(() => null)
    gradeOptions.value = (gradeRes?.data || []).map((i: any) => ({ label: i.label, value: i.grade_name || i.value }))
  }
  return params
}

const syncSearchValues = async (params: Record<string, any>) => {
  await nextTick()
  await searchRef.value?.setValues(params)
}

const onTabChange = async () => {
  lastParams.value = {}
  currentSchoolName.value = ''
  gradeOptions.value = []
  classOptions.value = []
  result.value = null
  classList.value = []
  await syncSearchValues({ batch_id: null, school_name: null, grade_name: null, class_name: null })
  await Promise.all([loadBatchOptions(), loadSchoolOptions()])
  const params = await buildDefaultParams()
  await syncSearchValues(params)
  await loadData(params)
}

onMounted(async () => {
  await Promise.all([loadBatchOptions(), loadSchoolOptions()])
  const params = await buildDefaultParams()
  await syncSearchValues(params)
  await loadData(params)
})
</script>

<template>
  <ContentWrap>
    <ElTabs v-model="stageType" class="mb-10px" @tab-change="onTabChange">
      <ElTabPane label="小学" name="primary" />
      <ElTabPane label="初中" name="mid" />
      <ElTabPane label="高中" name="high" />
      <ElTabPane label="大学" name="university" />
    </ElTabs>

    <Search ref="searchRef" :schema="searchSchema" class="mb-12px" @search="loadData" @reset="loadData" />

    <ElCard shadow="never" class="analysis-card">
      <div class="card-title">{{ titleText }}</div>

      <div v-if="!result || !result.kpi" class="py-30px"><ElEmpty description="暂无体测数据" /></div>

      <template v-else>
        <ElRow :gutter="12" class="mb-14px">
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover"><ElStatistic title="参考人数" :value="result.kpi.total_students || 0" /></ElCard></ElCol>
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover"><ElStatistic title="项目数" :value="result.kpi.item_count || 0" /></ElCard></ElCol>
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover"><ElStatistic title="单项记录数" :value="result.kpi.item_records || 0" /></ElCard></ElCol>
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover" class="kpi-fail"><ElStatistic title="不及格单项记录" :value="result.kpi.fail_item_records || 0" /></ElCard></ElCol>
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover" class="kpi-full"><ElStatistic title="满分单项记录" :value="result.kpi.full_item_records || 0" /></ElCard></ElCol>
        </ElRow>

        <ElRow :gutter="14" class="mb-14px">
          <ElCol :xs="24" :sm="24" :md="12" :lg="12" :xl="12"><Echart :options="itemAvgOptions" height="320px" /></ElCol>
          <ElCol :xs="24" :sm="24" :md="12" :lg="12" :xl="12"><Echart :options="itemRateOptions" height="320px" /></ElCol>
        </ElRow>

        <Echart :options="itemTrendOptions" height="300px" class="mb-14px" />

        <ElTable :data="classList" :span-method="schoolSpanMethod" stripe>
          <ElTableColumn prop="school_name" label="学校" min-width="160" />
          <ElTableColumn prop="class_name" label="班级" min-width="120" />
          <ElTableColumn label="BMI" min-width="130" align="center">
            <template #default="{ row }"><div>{{ row.bmi_score }}</div><div class="sub-cell">{{ row.bmi_point }}分 / {{ row.bmi_rate }}</div></template>
          </ElTableColumn>
          <ElTableColumn label="肺活量" min-width="130" align="center">
            <template #default="{ row }"><div>{{ row.lung_score }}</div><div class="sub-cell">{{ row.lung_point }}分 / {{ row.lung_rate }}</div></template>
          </ElTableColumn>
          <ElTableColumn label="50米" min-width="130" align="center">
            <template #default="{ row }"><div>{{ row.sprint_score }}</div><div class="sub-cell">{{ row.sprint_point }}分 / {{ row.sprint_rate }}</div></template>
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

