<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import type { FormSchema } from '@/components/Form'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import type { SearchExpose } from '@/components/Search'
import { Echart } from '@/components/Echart'
import { ElCard, ElCol, ElEmpty, ElRow, ElStatistic, ElTable, ElTableColumn, ElTabs, ElTabPane } from 'element-plus'
import { getPeBatchOptionsApi, getPeGradeAnalysisApi } from '@/api/vadmin/pe'
import { getGradeOptionsApi, getSchoolOptionsApi } from '@/api/vadmin/sport'

defineOptions({ name: 'PEGradeAnalysis' })

const stageType = ref<'mid' | 'high'>('mid')
const lastParams = ref<Record<string, any>>({})
const searchRef = ref<SearchExpose>()

const batchOptions = ref<any[]>([])
const schoolOptions = ref<any[]>([])
const gradeOptions = ref<any[]>([])

const kpi = ref<any>(null)
const classList = ref<any[]>([])

const searchSchema = computed<FormSchema[]>(() => [
  { field: 'batch_id', label: '批次', component: 'Select', required: true, componentProps: { options: batchOptions.value, filterable: true } },
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
        await searchRef.value?.setValues({ grade_name: null })
        if (!val) return
        const res = await getGradeOptionsApi({ school_name: val }).catch(() => null)
        gradeOptions.value = (res?.data || []).map((i: any) => ({ label: i.label, value: i.grade_name || i.value }))
      }
    }
  },
  { field: 'grade_name', label: '年级', component: 'Select', required: true, componentProps: { options: gradeOptions.value } }
])

const titleText = computed(() => {
  const p = lastParams.value
  const batchText = batchOptions.value.find((b: any) => b.value === p.batch_id)?.label || '某批次'
  return `${batchText}-${p.school_name || '-'}-${p.grade_name || '-'} 体育项目情况分析`
})

const classAvgOptions = reactive<any>({
  title: { text: '各班平均分', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
  tooltip: { trigger: 'axis' },
  grid: { left: 25, right: 20, top: 45, bottom: 30, containLabel: true },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', name: '总分' },
  series: [
    {
      name: '平均分',
      type: 'bar',
      data: [],
      itemStyle: { color: '#409EFF' },
      label: { show: true, position: 'top' },
      markLine: { symbol: ['none', 'none'], data: [] }
    }
  ]
})

const classItemOptions = reactive<any>({
  title: { text: '各班项目均值', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0 },
  grid: { left: 25, right: 20, top: 45, bottom: 50, containLabel: true },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', name: '平均分值' },
  series: []
})

const classHistoryOptions = reactive<any>({
  title: { text: '各班历史趋势', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0 },
  grid: { left: 25, right: 20, top: 45, bottom: 50, containLabel: true },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', name: '总分' },
  series: []
})

const applyCharts = (data: any) => {
  const avgCompare = data?.class_avg_compare || {}
  classAvgOptions.xAxis.data = avgCompare.classes || []
  classAvgOptions.series[0].data = avgCompare.avg_score || []
  const t = avgCompare.threshold || {}
  classAvgOptions.series[0].markLine.data = [
    { yAxis: t.pass || 30, name: '及格阈值', lineStyle: { color: '#E6A23C', type: 'dashed' } },
    { yAxis: t.excellent || 40, name: '优秀阈值', lineStyle: { color: '#67C23A', type: 'dashed' } },
    { yAxis: t.full || 50, name: '满分阈值', lineStyle: { color: '#000000', type: 'dashed' } }
  ]

  const item = data?.class_item_compare || {}
  classItemOptions.xAxis.data = item.classes || []
  classItemOptions.series = [
    { name: '门槛项', type: 'bar', data: item.gate_point_avg || [], itemStyle: { color: '#409EFF' }, label: { show: true, position: 'top' } },
    { name: '跳绳', type: 'bar', data: item.rope_point_avg || [], itemStyle: { color: '#67C23A' }, label: { show: true, position: 'top' } },
    { name: '跳远', type: 'bar', data: item.jump_point_avg || [], itemStyle: { color: '#E6A23C' }, label: { show: true, position: 'top' } },
    { name: '实心球', type: 'bar', data: item.ball_point_avg || [], itemStyle: { color: '#F56C6C' }, label: { show: true, position: 'top' } }
  ]

  const history = data?.class_history_trend || {}
  classHistoryOptions.xAxis.data = history.batches || []
  classHistoryOptions.series = (history.series || []).map((s: any, idx: number) => ({
    name: s.name,
    type: 'line',
    smooth: true,
    data: s.values || [],
    label: { show: true, position: 'top' },
    itemStyle: { color: ['#409EFF', '#67C23A', '#E6A23C', '#000000'][idx % 4] }
  }))
}

const loadData = async (params: Record<string, any> = lastParams.value) => {
  const query = { ...params, stage_type: stageType.value }
  lastParams.value = { ...params }
  const res = await getPeGradeAnalysisApi(query).catch(() => null)
  if (!res?.data?.kpi) {
    kpi.value = null
    classList.value = []
    return
  }
  kpi.value = res.data.kpi
  classList.value = res.data.class_list || []
  applyCharts(res.data)
}

const loadBatchOptions = async () => {
  const batchRes = await getPeBatchOptionsApi({ stage_type: stageType.value }).catch(() => null)
  batchOptions.value = batchRes?.data || []
}

const loadSchoolOptions = async () => {
  const schoolRes = await getSchoolOptionsApi({ stage_type: stageType.value }).catch(() => null)
  schoolOptions.value = (schoolRes?.data || []).map((i: any) => ({ label: i.label, value: i.school_name || i.value }))
}

const buildDefaultParams = async () => {
  const params: Record<string, any> = { batch_id: null, school_name: null, grade_name: null }
  if (batchOptions.value.length) params.batch_id = batchOptions.value[0].value
  if (schoolOptions.value.length) {
    params.school_name = schoolOptions.value[0].value
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
  gradeOptions.value = []
  kpi.value = null
  classList.value = []
  await syncSearchValues({ batch_id: null, school_name: null, grade_name: null })
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
      <ElTabPane label="初中" name="mid" />
      <ElTabPane label="高中" name="high" />
    </ElTabs>

    <Search ref="searchRef" :schema="searchSchema" class="mb-12px" @search="loadData" @reset="loadData" />

    <ElCard shadow="never" class="analysis-card">
      <div class="card-title">{{ titleText }}</div>

      <div v-if="!kpi" class="py-30px"><ElEmpty description="请选择年级并查询" /></div>

      <template v-else>
        <ElRow :gutter="12" class="mb-14px">
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover"><ElStatistic title="年级平均分" :value="kpi.avg_score || 0" :precision="2" /></ElCard></ElCol>
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover" class="kpi-pass"><ElStatistic title="及格率" :value="kpi.pass_rate || 0" suffix="%" :precision="2" /></ElCard></ElCol>
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover" class="kpi-excellent"><ElStatistic title="优秀率" :value="kpi.excellent_rate || 0" suffix="%" :precision="2" /></ElCard></ElCol>
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover" class="kpi-full"><ElStatistic title="满分率" :value="kpi.full_rate || 0" suffix="%" :precision="2" /></ElCard></ElCol>
        </ElRow>

        <ElRow :gutter="14" class="mb-14px">
          <ElCol :xs="24" :sm="24" :md="12" :lg="12" :xl="12"><Echart :options="classAvgOptions" height="300px" /></ElCol>
          <ElCol :xs="24" :sm="24" :md="12" :lg="12" :xl="12"><Echart :options="classItemOptions" height="300px" /></ElCol>
        </ElRow>

        <Echart :options="classHistoryOptions" height="300px" class="mb-14px" />

        <ElTable :data="classList" stripe>
          <ElTableColumn prop="class_name" label="班级" min-width="120" />
          <ElTableColumn label="门槛项" min-width="130" align="center">
            <template #default="{ row }"><div>{{ row.gate_score }}</div><div class="sub-cell">{{ row.gate_point }}分</div></template>
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
          <ElTableColumn prop="avg_score" label="班级平均分" min-width="110" align="center" />
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

