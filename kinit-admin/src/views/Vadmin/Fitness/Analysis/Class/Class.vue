<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import type { FormSchema } from '@/components/Form'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import type { SearchExpose } from '@/components/Search'
import { Echart } from '@/components/Echart'
import { ElCard, ElCol, ElEmpty, ElRow, ElStatistic, ElTable, ElTableColumn, ElTabs, ElTabPane } from 'element-plus'
import { getFitnessBatchOptionsApi, getFitnessClassAnalysisApi } from '@/api/vadmin/fitness'
import { getClassOptionsApi, getGradeOptionsApi, getSchoolOptionsApi } from '@/api/vadmin/sport'

defineOptions({ name: 'FitnessClassAnalysis' })

const stageType = ref<'primary' | 'mid' | 'high' | 'university'>('primary')
const lastParams = ref<Record<string, any>>({})
const searchRef = ref<SearchExpose>()

const batchOptions = ref<any[]>([])
const schoolOptions = ref<any[]>([])
const gradeOptions = ref<any[]>([])
const classOptions = ref<any[]>([])
const currentSchoolName = ref<string>('')

const kpi = ref<any>(null)
const rankList = ref<any[]>([])

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
  { field: 'class_name', label: '班级', component: 'Select', required: true, componentProps: { options: classOptions.value } }
])

const titleText = computed(() => {
  const p = lastParams.value
  const batchText = batchOptions.value.find((b: any) => b.value === p.batch_id)?.label || '某批次'
  return `${batchText}-${p.school_name || '-'}-${p.grade_name || '-'}-${p.class_name || '-'} 体质测试情况分析`
})

const historyItemAvgOptions = reactive<any>({
  title: { text: '批次单项均分趋势', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0 },
  grid: { left: 25, right: 20, top: 45, bottom: 50, containLabel: true },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', name: '分值' },
  series: []
})

const currentRateOptions = reactive<any>({
  title: { text: '当前单项达成率', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
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

const applyCharts = (data: any) => {
  const history = data?.history_item_avg || {}
  historyItemAvgOptions.xAxis.data = history.batches || []
  historyItemAvgOptions.series = (history.series || []).map((s: any, idx: number) => ({
    name: s.name,
    type: 'line',
    smooth: true,
    data: s.values || [],
    label: { show: true, position: 'top' },
    itemStyle: { color: ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C'][idx % 4] }
  }))

  const rate = data?.current_item_rate || {}
  currentRateOptions.xAxis.data = rate.items || []
  currentRateOptions.series[0].data = rate.pass_rate || []
  currentRateOptions.series[1].data = rate.excellent_rate || []
  currentRateOptions.series[2].data = rate.full_rate || []
}

const loadData = async (params: Record<string, any> = lastParams.value) => {
  const query = { ...params, stage_type: stageType.value }
  lastParams.value = { ...params }
  const res = await getFitnessClassAnalysisApi(query).catch(() => null)
  if (!res?.data?.kpi) {
    kpi.value = null
    rankList.value = []
    return
  }
  kpi.value = res.data.kpi
  rankList.value = res.data.rank_list || []
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
  kpi.value = null
  rankList.value = []
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

      <div v-if="!kpi" class="py-30px"><ElEmpty description="请选择班级并查询" /></div>

      <template v-else>
        <ElRow :gutter="12" class="mb-14px">
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover"><ElStatistic title="学生人数" :value="kpi.student_count || 0" /></ElCard></ElCol>
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover"><ElStatistic title="项目数" :value="kpi.item_count || 0" /></ElCard></ElCol>
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover"><ElStatistic title="单项记录数" :value="kpi.item_records || 0" /></ElCard></ElCol>
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover" class="kpi-fail"><ElStatistic title="不及格单项记录" :value="kpi.fail_item_records || 0" /></ElCard></ElCol>
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover" class="kpi-full"><ElStatistic title="满分单项记录" :value="kpi.full_item_records || 0" /></ElCard></ElCol>
        </ElRow>

        <ElRow :gutter="14" class="mb-14px">
          <ElCol :xs="24" :sm="24" :md="12" :lg="12" :xl="12"><Echart :options="historyItemAvgOptions" height="320px" /></ElCol>
          <ElCol :xs="24" :sm="24" :md="12" :lg="12" :xl="12"><Echart :options="currentRateOptions" height="320px" /></ElCol>
        </ElRow>

        <ElTable :data="rankList" stripe>
          <ElTableColumn prop="rank" label="排名" min-width="70" align="center" />
          <ElTableColumn prop="student_name" label="学生" min-width="100" />
          <ElTableColumn label="BMI" min-width="130" align="center">
            <template #default="{ row }"><div>{{ row.bmi_score }}</div><div class="sub-cell">{{ row.bmi_point }}分</div></template>
          </ElTableColumn>
          <ElTableColumn label="肺活量" min-width="130" align="center">
            <template #default="{ row }"><div>{{ row.lung_score }}</div><div class="sub-cell">{{ row.lung_point }}分</div></template>
          </ElTableColumn>
          <ElTableColumn label="50米" min-width="130" align="center">
            <template #default="{ row }"><div>{{ row.sprint_score }}</div><div class="sub-cell">{{ row.sprint_point }}分</div></template>
          </ElTableColumn>
          <ElTableColumn label="体前屈" min-width="130" align="center">
            <template #default="{ row }"><div>{{ row.sit_score }}</div><div class="sub-cell">{{ row.sit_point }}分</div></template>
          </ElTableColumn>
          <ElTableColumn label="跳绳" min-width="130" align="center">
            <template #default="{ row }"><div>{{ row.rope_score }}</div><div class="sub-cell">{{ row.rope_point }}分</div></template>
          </ElTableColumn>
          <ElTableColumn prop="avg_score" label="单项均分" min-width="90" align="center" />
          <ElTableColumn prop="teacher_comment" label="老师评语" min-width="220" show-overflow-tooltip />
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

