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
import { useHeaderTheme } from '@/hooks/web/useHeaderTheme'
import { analysisHeroImages } from '@/constants/cockpit'

defineOptions({ name: 'FitnessClassAnalysis' })

const stageType = ref<'primary' | 'mid' | 'high' | 'university'>('primary')
const lastParams = ref<Record<string, any>>({})
const searchRef = ref<SearchExpose>()

const batchOptions = ref<any[]>([])
const schoolOptions = ref<any[]>([])
const gradeOptions = ref<any[]>([])
const classOptions = ref<any[]>([])
const currentSchoolName = ref<string>('')

const headerThemeMap = {
  primary: { bg: '#0c2137', text: '#f8fafc', hover: 'rgba(56, 189, 248, 0.14)' },
  mid: { bg: '#081426', text: '#f8fafc', hover: 'rgba(45, 212, 191, 0.14)' },
  high: { bg: '#0b1a2e', text: '#f8fafc', hover: 'rgba(20, 184, 166, 0.14)' },
  university: { bg: '#10233d', text: '#f8fafc', hover: 'rgba(125, 211, 252, 0.14)' }
}

const kpi = ref<any>(null)
const rankList = ref<any[]>([])
const detailColumns = ref<any[]>([])

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

const heroGaugeValue = computed(() => Number(kpi.value?.student_count || 0))
const heroStats = computed(() => [
  { label: '学生人数', value: Number(kpi.value?.student_count || 0), suffix: '人' },
  { label: '项目记录', value: Number(kpi.value?.item_records || 0), suffix: '条' },
  { label: '不及格记录', value: Number(kpi.value?.fail_item_records || 0), suffix: '项' },
  { label: '满分记录', value: Number(kpi.value?.full_item_records || 0), suffix: '项' }
])

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
    detailColumns.value = []
    return
  }
  kpi.value = res.data.kpi
  rankList.value = res.data.rank_list || []
  detailColumns.value = res.data.detail_columns || []
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

useHeaderTheme(() => stageType.value, headerThemeMap, 'primary')
</script>

<template>
  <ContentWrap>
    <div class="analysis-stage analysis-stage--fitness">
      <ElTabs v-model="stageType" class="analysis-tabs mb-10px" @tab-change="onTabChange">
        <ElTabPane label="小学" name="primary" />
        <ElTabPane label="初中" name="mid" />
        <ElTabPane label="高中" name="high" />
        <ElTabPane label="大学" name="university" />
      </ElTabs>

      <div class="analysis-search-shell mb-12px">
        <Search ref="searchRef" :schema="searchSchema" :show-reset="false" @search="loadData" @reset="loadData" />
      </div>

      <section class="analysis-hero mb-16px" :style="{ '--analysis-hero-image': `url(${analysisHeroImages.fitnessClass}) center/cover no-repeat` }">
        <div class="analysis-hero__copy">
          <div class="analysis-hero__eyebrow">FITNESS CLASS ANALYSIS</div>
          <h1 class="analysis-hero__title">班级 <span>对比</span></h1>
          <p class="analysis-hero__desc">把单个班级的体测规模、单项达成和历史均分放到一个驾驶舱里，快速识别哪类项目正在拖后腿。</p>
          <div class="analysis-hero__meta">
            <div class="analysis-hero__pill">{{ titleText }}</div>
            <div class="analysis-hero__sub">当前学段：{{ ({ primary: '小学', mid: '初中', high: '高中', university: '大学' } as any)[stageType] }}</div>
          </div>
        </div>
        <div class="analysis-hero__visual">
          <div class="analysis-hero__runner"></div>
          <div class="analysis-hero__gauge">
            <div class="analysis-hero__gauge-ring"></div>
            <div class="analysis-hero__gauge-inner">
              <div class="analysis-hero__gauge-label">学生人数</div>
              <div class="analysis-hero__gauge-value">{{ heroGaugeValue }}</div>
              <div class="analysis-hero__gauge-unit">人</div>
            </div>
          </div>
          <div class="analysis-hero__stats">
            <div v-for="item in heroStats" :key="item.label" class="analysis-hero__stat">
              <div class="analysis-hero__stat-label">{{ item.label }}</div>
              <div class="analysis-hero__stat-value">{{ item.value }}<span>{{ item.suffix }}</span></div>
            </div>
          </div>
        </div>
      </section>

      <ElCard shadow="never" class="analysis-card">
        <div class="card-title">{{ titleText }}</div>

        <div v-if="!kpi" class="py-30px"><ElEmpty description="请选择班级并查询" /></div>

        <template v-else>
        <ElRow :gutter="12" class="analysis-kpi-row mb-14px">
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
          <ElTableColumn
            v-for="(col, idx) in detailColumns"
            :key="`${col.item_code}-${idx}`"
            :label="col.item_name"
            min-width="130"
            align="center"
          >
            <template #default="{ row }"><div>{{ row.items?.[idx]?.raw_score ?? '-' }}</div><div class="sub-cell">{{ row.items?.[idx]?.score_value ?? 0 }}分</div></template>
          </ElTableColumn>
          <ElTableColumn prop="avg_score" label="单项均分" min-width="90" align="center" />
          <ElTableColumn prop="teacher_comment" label="老师评语" min-width="220" show-overflow-tooltip />
        </ElTable>
        </template>
      </ElCard>
    </div>
  </ContentWrap>
</template>

<style scoped>
@import '@/styles/analysis-cockpit.less';

.card-title { text-align: center; font-size: 22px; font-weight: 700; margin-bottom: 16px; }
.sub-cell { color: #909399; font-size: 12px; }
.analysis-card :deep(.el-statistic__head) { font-size: 14px; color: #606266; font-weight: 500; }
.kpi-pass :deep(.el-statistic__content-value), .kpi-pass :deep(.el-statistic__content), .kpi-pass-text { color: #E6A23C !important; }
.kpi-fail :deep(.el-statistic__content-value), .kpi-fail :deep(.el-statistic__content), .kpi-fail-text { color: #F56C6C !important; }
.kpi-excellent :deep(.el-statistic__content-value), .kpi-excellent :deep(.el-statistic__content), .kpi-excellent-text { color: #67C23A !important; }
.kpi-full :deep(.el-statistic__content-value), .kpi-full :deep(.el-statistic__content), .kpi-full-text { color: #000000 !important; }
</style>

