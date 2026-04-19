<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { Echart } from '@/components/Echart'
import { useAuthStoreWithOut } from '@/store/modules/auth'
import {
  ElButton,
  ElCard,
  ElCol,
  ElDescriptions,
  ElDescriptionsItem,
  ElEmpty,
  ElOption,
  ElRow,
  ElSelect,
  ElTable,
  ElTableColumn,
  ElTag
} from 'element-plus'
import { getPeStudentAnalysisSelfApi } from '@/api/vadmin/pe'
import { getFitnessStudentAnalysisSelfApi } from '@/api/vadmin/fitness'
import { getSchoolOptionsApi, getGradeOptionsApi, getClassOptionsApi, getStudentListApi } from '@/api/vadmin/sport'
import { useHeaderTheme } from '@/hooks/web/useHeaderTheme'
import { analysisHeroImages } from '@/constants/cockpit'

defineOptions({ name: 'MyScores' })

const authStore = useAuthStoreWithOut()
const isStaff = computed(() => Boolean((authStore.getUser as any)?.is_staff))

const peData = ref<any>(null)
const fitnessData = ref<any>(null)
const loading = ref(false)
const descColumns = ref(3)

const schoolOptions = ref<any[]>([])
const gradeOptions = ref<any[]>([])
const classOptions = ref<any[]>([])
const studentOptions = ref<any[]>([])

const headerThemeMap = {
  fitness: { bg: '#081426', text: '#f8fafc', hover: 'rgba(45, 212, 191, 0.14)' }
}

const filters = reactive({
  school_name: '',
  grade_name: '',
  class_name: '',
  student_no: ''
})

const peTotalTrendOptions = reactive<any>({
  title: { text: '体考总分趋势', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0 },
  grid: { left: 25, right: 20, top: 48, bottom: 48, containLabel: true },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', name: '总分' },
  series: [
    { name: '总分', type: 'line', smooth: true, data: [], itemStyle: { color: '#409EFF' } },
    { name: '及格线', type: 'line', smooth: true, data: [], lineStyle: { color: '#E6A23C', type: 'dashed' } },
    { name: '优秀线', type: 'line', smooth: true, data: [], lineStyle: { color: '#67C23A', type: 'dashed' } },
    { name: '满分线', type: 'line', smooth: true, data: [], lineStyle: { color: '#303133', type: 'dashed' } }
  ]
})

const peItemTrendOptions = reactive<any>({
  title: { text: '体考单项评分分布', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0 },
  grid: { left: 25, right: 20, top: 48, bottom: 48, containLabel: true },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', name: '分值' },
  series: []
})

const peStateTrendOptions = reactive<any>({
  title: { text: '体考等级分布趋势', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0 },
  grid: { left: 25, right: 20, top: 48, bottom: 48, containLabel: true },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', name: '人次' },
  series: [
    { name: '不及格', type: 'bar', data: [], itemStyle: { color: '#F56C6C' } },
    { name: '及格', type: 'bar', data: [], itemStyle: { color: '#E6A23C' } },
    { name: '优秀', type: 'bar', data: [], itemStyle: { color: '#67C23A' } },
    { name: '满分', type: 'bar', data: [], itemStyle: { color: '#303133' } }
  ]
})

const fitnessItemTrendOptions = reactive<any>({
  title: { text: '体测单项评分分布', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0 },
  grid: { left: 25, right: 20, top: 48, bottom: 48, containLabel: true },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', name: '分值' },
  series: []
})

const fitnessRadarOptions = reactive<any>({
  title: { text: '体测多维综合评估', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
  tooltip: { trigger: 'item' },
  radar: { indicator: [] },
  series: [{ type: 'radar', data: [] }]
})

const fitnessStateTrendOptions = reactive<any>({
  title: { text: '体测状态数量趋势', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0 },
  grid: { left: 25, right: 20, top: 48, bottom: 48, containLabel: true },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', name: '项目数' },
  series: [
    { name: '不及格项目数', type: 'bar', data: [], itemStyle: { color: '#F56C6C' } },
    { name: '及格项目数', type: 'bar', data: [], itemStyle: { color: '#E6A23C' } },
    { name: '优秀项目数', type: 'bar', data: [], itemStyle: { color: '#67C23A' } },
    { name: '满分项目数', type: 'bar', data: [], itemStyle: { color: '#303133' } }
  ]
})

const profile = computed(() => peData.value?.profile || fitnessData.value?.profile || null)
const fitnessDetailColumns = computed(() => fitnessData.value?.detail_columns || [])
const peLatestScore = computed(() => Number(peData.value?.stats?.latest_total || 0))
const fitnessLatestScore = computed(() => {
  const row = fitnessData.value?.detail_list?.[0]
  if (!row) return 0
  const values = (row.items || []).map((item: any) => Number(item.score_value) || 0)
  if (!values.length) return 0
  return Number((values.reduce((a: number, b: number) => a + b, 0) / values.length).toFixed(2))
})

const heroStats = computed(() => [
  { label: '体考总分', value: Number(peLatestScore.value || 0).toFixed(1), suffix: '分' },
  { label: '体测评分', value: Number(fitnessLatestScore.value || 0).toFixed(1), suffix: '分' },
  { label: '体考批次', value: Number(peData.value?.detail_list?.length || 0), suffix: '次' },
  { label: '体测批次', value: Number(fitnessData.value?.detail_list?.length || 0), suffix: '次' }
])

const summaryCards = computed(() => [
  {
    key: 'pe',
    title: '最新体考总分',
    value: Number(peLatestScore.value || 0).toFixed(1),
    unit: '分',
    eyebrow: 'PE SCORE',
    desc: `最近 ${Number(peData.value?.detail_list?.length || 0)} 次体考记录中的最新成绩`,
    meta: peData.value?.detail_list?.[0]?.batch_name || '暂无体考批次',
    tone: 'pe'
  },
  {
    key: 'fitness',
    title: '最新体测综合评分',
    value: Number(fitnessLatestScore.value || 0).toFixed(1),
    unit: '分',
    eyebrow: 'FITNESS SCORE',
    desc: `最近 ${Number(fitnessData.value?.detail_list?.length || 0)} 次体测记录的综合表现`,
    meta: fitnessData.value?.detail_list?.[0]?.batch_name || '暂无体测批次',
    tone: 'fitness'
  }
])

const hasPeTotalTrend = computed(() => (peTotalTrendOptions.xAxis.data || []).length > 0)
const hasPeItemTrend = computed(() => (peItemTrendOptions.series || []).length > 0)
const hasPeStateTrend = computed(() => (peStateTrendOptions.xAxis.data || []).length > 0)
const hasFitnessItemTrend = computed(() => (fitnessItemTrendOptions.series || []).length > 0)
const hasFitnessRadar = computed(() => (fitnessRadarOptions.radar?.indicator || []).length > 0)
const hasFitnessStateTrend = computed(() => (fitnessStateTrendOptions.xAxis.data || []).length > 0)

const chartColors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399']

const applyPeCharts = () => {
  const total = peData.value?.total_trend || {}
  peTotalTrendOptions.xAxis.data = total.batches || []
  peTotalTrendOptions.series[0].data = total.total || []
  peTotalTrendOptions.series[1].data = total.pass_line || []
  peTotalTrendOptions.series[2].data = total.excellent_line || []
  peTotalTrendOptions.series[3].data = total.full_line || []

  const item = peData.value?.item_trend || {}
  peItemTrendOptions.xAxis.data = item.batches || []
  peItemTrendOptions.series = (item.series || []).map((s: any, idx: number) => ({
    name: s.name,
    type: 'bar',
    data: s.values || [],
    label: { show: true, position: 'top' },
    itemStyle: { color: chartColors[idx % chartColors.length] }
  }))

  const batches = total.batches || []
  const totals = total.total || []
  const passLine = total.pass_line || []
  const excellentLine = total.excellent_line || []
  const fullLine = total.full_line || []
  peStateTrendOptions.xAxis.data = batches
  peStateTrendOptions.series[0].data = totals.map((v: any, i: number) => (Number(v) < Number(passLine[i] || 0) ? 1 : 0))
  peStateTrendOptions.series[1].data = totals.map((v: any, i: number) =>
    Number(v) >= Number(passLine[i] || 0) && Number(v) < Number(excellentLine[i] || 0) ? 1 : 0
  )
  peStateTrendOptions.series[2].data = totals.map((v: any, i: number) =>
    Number(v) >= Number(excellentLine[i] || 0) && Number(v) < Number(fullLine[i] || 0) ? 1 : 0
  )
  peStateTrendOptions.series[3].data = totals.map((v: any, i: number) => (Number(v) >= Number(fullLine[i] || 0) ? 1 : 0))
}

const applyFitnessCharts = () => {
  const itemScore = fitnessData.value?.item_score_trend || {}
  fitnessItemTrendOptions.xAxis.data = itemScore.batches || []
  fitnessItemTrendOptions.series = (itemScore.series || []).map((s: any, idx: number) => ({
    name: s.name,
    type: 'line',
    smooth: true,
    data: s.values || [],
    label: { show: true, position: 'top' },
    itemStyle: { color: chartColors[idx % chartColors.length] }
  }))

  const radar = fitnessData.value?.multi_dim_radar || {}
  const items = radar.items || []
  const values = radar.values || []
  const maxVals = radar.max || []
  fitnessRadarOptions.radar.indicator = items.map((name: string, idx: number) => ({
    name,
    max: Number(maxVals[idx] || 100)
  }))
  fitnessRadarOptions.series[0].data = items.length ? [{ name: '当前表现', value: values }] : []

  const state = fitnessData.value?.item_state_trend || {}
  fitnessStateTrendOptions.xAxis.data = state.batches || []
  fitnessStateTrendOptions.series[0].data = state.fail_items || []
  fitnessStateTrendOptions.series[1].data = state.pass_items || []
  fitnessStateTrendOptions.series[2].data = state.excellent_items || []
  fitnessStateTrendOptions.series[3].data = state.full_items || []
}

const loadData = async (params?: Record<string, any>) => {
  loading.value = true
  const query = isStaff.value ? params || {} : undefined
  const [peRes, fitnessRes] = await Promise.all([
    getPeStudentAnalysisSelfApi(query).catch(() => null),
    getFitnessStudentAnalysisSelfApi(query).catch(() => null)
  ])
  peData.value = peRes?.data || null
  fitnessData.value = fitnessRes?.data || null
  applyPeCharts()
  applyFitnessCharts()
  loading.value = false
}

const loadSchoolOptions = async () => {
  const res = await getSchoolOptionsApi().catch(() => null)
  schoolOptions.value = (res?.data || []).map((i: any) => ({
    label: i.label || i.school_name,
    value: i.school_name || i.value
  }))
}

const loadGradeOptions = async () => {
  filters.grade_name = ''
  filters.class_name = ''
  filters.student_no = ''
  classOptions.value = []
  studentOptions.value = []
  if (!filters.school_name) {
    gradeOptions.value = []
    return
  }
  const res = await getGradeOptionsApi({ school_name: filters.school_name }).catch(() => null)
  gradeOptions.value = (res?.data || []).map((i: any) => ({
    label: i.label || i.grade_name,
    value: i.grade_name || i.value
  }))
}

const loadClassOptions = async () => {
  filters.class_name = ''
  filters.student_no = ''
  studentOptions.value = []
  if (!filters.school_name || !filters.grade_name) {
    classOptions.value = []
    return
  }
  const res = await getClassOptionsApi({
    school_name: filters.school_name,
    grade_name: filters.grade_name
  }).catch(() => null)
  classOptions.value = (res?.data || []).map((i: any) => ({
    label: i.label || i.class_name,
    value: i.class_name || i.value
  }))
}

const loadStudentOptions = async () => {
  filters.student_no = ''
  if (!filters.school_name) {
    studentOptions.value = []
    return
  }
  const res = await getStudentListApi({
    school_name: filters.school_name,
    grade_name: filters.grade_name || undefined,
    class_name: filters.class_name || undefined,
    limit: 1000,
    page: 1
  }).catch(() => null)
  studentOptions.value = (res?.data?.items || []).map((s: any) => ({
    label: `${s.student_no} ${s.name}`,
    value: s.student_no
  }))
}

const queryByFilter = async () => {
  if (!isStaff.value) return
  if (!filters.student_no) {
    peData.value = null
    fitnessData.value = null
    applyPeCharts()
    applyFitnessCharts()
    return
  }
  await loadData({
    school_name: filters.school_name || undefined,
    grade_name: filters.grade_name || undefined,
    class_name: filters.class_name || undefined,
    student_no: filters.student_no
  })
}

const initStaffDefault = async () => {
  await loadSchoolOptions()
  if (!schoolOptions.value.length) {
    peData.value = null
    fitnessData.value = null
    return
  }
  filters.school_name = schoolOptions.value[0].value
  await loadGradeOptions()
  await loadStudentOptions()
  if (studentOptions.value.length) {
    filters.student_no = studentOptions.value[0].value
    await queryByFilter()
  } else {
    peData.value = null
    fitnessData.value = null
  }
}

const syncLayout = () => {
  descColumns.value = window.innerWidth <= 768 ? 1 : 3
}

onMounted(async () => {
  syncLayout()
  window.addEventListener('resize', syncLayout)
  if (isStaff.value) {
    await initStaffDefault()
  } else {
    await loadData()
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', syncLayout)
})

useHeaderTheme(() => 'fitness', headerThemeMap, 'fitness')
</script>

<template>
  <ContentWrap>
    <div class="analysis-stage analysis-stage--fitness my-scores-cockpit">
      <div v-if="isStaff" class="analysis-search-shell mb-12px">
        <div class="filter-row">
          <ElSelect v-model="filters.school_name" placeholder="学校" clearable @change="loadGradeOptions" class="w-220px">
            <ElOption v-for="o in schoolOptions" :key="o.value" :label="o.label" :value="o.value" />
          </ElSelect>
          <ElSelect v-model="filters.grade_name" placeholder="年级" clearable @change="loadClassOptions" class="w-180px">
            <ElOption v-for="o in gradeOptions" :key="o.value" :label="o.label" :value="o.value" />
          </ElSelect>
          <ElSelect v-model="filters.class_name" placeholder="班级" clearable @change="loadStudentOptions" class="w-180px">
            <ElOption v-for="o in classOptions" :key="o.value" :label="o.label" :value="o.value" />
          </ElSelect>
          <ElSelect v-model="filters.student_no" placeholder="学生" clearable filterable class="w-240px">
            <ElOption v-for="o in studentOptions" :key="o.value" :label="o.label" :value="o.value" />
          </ElSelect>
          <ElButton type="primary" @click="queryByFilter">查询</ElButton>
        </div>
      </div>

      <section class="analysis-hero mb-16px" :style="{ '--analysis-hero-image': `url(${analysisHeroImages.myScores}) center/cover no-repeat` }">
        <div class="analysis-hero__copy">
          <div class="analysis-hero__eyebrow">MY SPORTS SCOREBOARD</div>
          <h1 class="analysis-hero__title">我的 <span>成绩</span></h1>
          <p class="analysis-hero__desc">把体考与体测的最近表现、批次轨迹和项目分布放到同一张成绩驾驶舱里，查看个人阶段性变化。</p>
          <div class="analysis-hero__meta">
            <div class="analysis-hero__pill">{{ profile ? `${profile.school || '-'}-${profile.student_name || '-'}-${profile.student_no || '-'}` : (isStaff ? '请选择学生查看' : '我的成绩驾驶舱') }}</div>
            <div class="analysis-hero__sub">{{ isStaff ? '管理员筛选视角' : '学生个人视角' }}</div>
          </div>
        </div>
        <div class="analysis-hero__visual">
          <div class="analysis-hero__runner"></div>
          <div class="analysis-hero__gauge">
            <div class="analysis-hero__gauge-ring"></div>
            <div class="analysis-hero__gauge-inner">
              <div class="analysis-hero__gauge-label">体考总分</div>
              <div class="analysis-hero__gauge-value">{{ peLatestScore }}</div>
              <div class="analysis-hero__gauge-unit">分</div>
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

      <div v-if="loading" class="analysis-card text-center py-32px text-gray-400">正在加载成绩数据...</div>
      <div v-else-if="!profile" class="analysis-card">
        <ElEmpty :description="isStaff ? '请选择学生后查看成绩' : '暂无成绩信息，请联系老师或管理员'" />
      </div>
      <div v-else class="my-scores-page">
        <ElCard shadow="never" class="analysis-card mb-12px" header="个人档案">
          <ElDescriptions :column="descColumns" border>
            <ElDescriptionsItem label="姓名">{{ profile.student_name || '-' }}</ElDescriptionsItem>
            <ElDescriptionsItem label="性别">{{ profile.gender || '-' }}</ElDescriptionsItem>
            <ElDescriptionsItem label="学号">{{ profile.student_no || '-' }}</ElDescriptionsItem>
            <ElDescriptionsItem label="学校">{{ profile.school || '-' }}</ElDescriptionsItem>
            <ElDescriptionsItem label="年级">{{ profile.grade || '-' }}</ElDescriptionsItem>
            <ElDescriptionsItem label="班级">{{ profile.class_name || '-' }}</ElDescriptionsItem>
          </ElDescriptions>
        </ElCard>

        <ElRow :gutter="12" class="mb-12px">
          <ElCol v-for="card in summaryCards" :key="card.key" :xs="24" :sm="12">
            <ElCard shadow="never" class="score-highlight-card" :class="`score-highlight-card--${card.tone}`">
              <div class="score-highlight-card__eyebrow">{{ card.eyebrow }}</div>
              <div class="score-highlight-card__title">{{ card.title }}</div>
              <div class="score-highlight-card__value">
                {{ card.value }}
                <span>{{ card.unit }}</span>
              </div>
              <div class="score-highlight-card__desc">{{ card.desc }}</div>
              <div class="score-highlight-card__meta">{{ card.meta }}</div>
            </ElCard>
          </ElCol>
        </ElRow>

        <ElCard shadow="never" class="analysis-card mb-12px" header="体考分析（3图）">
          <ElRow :gutter="12">
            <ElCol :xs="24" :md="8" class="mb-12px">
              <Echart v-if="hasPeTotalTrend" :options="peTotalTrendOptions" :height="300" />
              <ElEmpty v-else description="暂无体考总分趋势" />
            </ElCol>
            <ElCol :xs="24" :md="8" class="mb-12px">
              <Echart v-if="hasPeItemTrend" :options="peItemTrendOptions" :height="300" />
              <ElEmpty v-else description="暂无体考单项分布" />
            </ElCol>
            <ElCol :xs="24" :md="8" class="mb-12px">
              <Echart v-if="hasPeStateTrend" :options="peStateTrendOptions" :height="300" />
              <ElEmpty v-else description="暂无体考等级分布" />
            </ElCol>
          </ElRow>
        </ElCard>

        <ElCard shadow="never" class="analysis-card mb-12px" header="体测分析（3图）">
          <ElRow :gutter="12">
            <ElCol :xs="24" :md="8" class="mb-12px">
              <Echart v-if="hasFitnessItemTrend" :options="fitnessItemTrendOptions" :height="300" />
              <ElEmpty v-else description="暂无体测单项分布" />
            </ElCol>
            <ElCol :xs="24" :md="8" class="mb-12px">
              <Echart v-if="hasFitnessRadar" :options="fitnessRadarOptions" :height="300" />
              <ElEmpty v-else description="暂无体测雷达图" />
            </ElCol>
            <ElCol :xs="24" :md="8" class="mb-12px">
              <Echart v-if="hasFitnessStateTrend" :options="fitnessStateTrendOptions" :height="300" />
              <ElEmpty v-else description="暂无体测状态趋势" />
            </ElCol>
          </ElRow>
        </ElCard>

        <ElRow :gutter="12">
          <ElCol :xs="24" :lg="12" class="mb-12px">
            <ElCard shadow="never" class="analysis-card" header="体考成绩明细">
              <ElTable v-if="peData?.detail_list?.length" :data="peData.detail_list" border stripe>
                <ElTableColumn prop="batch_name" label="测试批次" min-width="140" />
                <ElTableColumn prop="total_score" label="总分" width="90" align="center" />
                <ElTableColumn label="状态" width="100" align="center">
                  <template #default="{ row }">
                    <ElTag :type="row.pass_state ? 'success' : 'danger'">{{ row.pass_state ? '及格' : '不及格' }}</ElTag>
                  </template>
                </ElTableColumn>
              </ElTable>
              <ElEmpty v-else description="暂无体考明细" />
            </ElCard>
          </ElCol>
          <ElCol :xs="24" :lg="12" class="mb-12px">
            <ElCard shadow="never" class="analysis-card" header="体测成绩明细">
              <ElTable v-if="fitnessData?.detail_list?.length" :data="fitnessData.detail_list" border stripe>
                <ElTableColumn prop="batch_name" label="测试批次" min-width="140" />
                <ElTableColumn
                  v-for="(col, idx) in fitnessDetailColumns"
                  :key="`${col.item_code}-${idx}`"
                  :label="col.item_name"
                  min-width="110"
                  align="center"
                >
                  <template #default="{ row }">
                    {{ row.items?.[idx]?.score_value ?? 0 }}
                  </template>
                </ElTableColumn>
              </ElTable>
              <ElEmpty v-else description="暂无体测明细" />
            </ElCard>
          </ElCol>
        </ElRow>
      </div>
    </div>
  </ContentWrap>
</template>

<style scoped>
@import '@/styles/analysis-cockpit.less';

.filter-row {
  display: flex;
  flex-wrap: nowrap;
  gap: 10px;
  align-items: center;
}

.filter-row :deep(.el-select) {
  flex: 1 1 0;
  min-width: 0;
  width: auto !important;
}

.filter-row :deep(.el-button) {
  flex: 0 0 auto;
}

.my-scores-page :deep(.el-descriptions__label) {
  width: 72px;
}

.score-highlight-card {
  position: relative;
  overflow: hidden;
  min-height: 172px;
  color: #0f172a;
  border: none;
  border-radius: 22px;
}

.score-highlight-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.72), transparent 30%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0.04));
  pointer-events: none;
}

.score-highlight-card :deep(.el-card__body) {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  min-height: 172px;
  padding: 20px 20px 16px;
}

.score-highlight-card--pe {
  background:
    radial-gradient(circle at 85% 18%, rgba(251, 191, 36, 0.22), transparent 24%),
    linear-gradient(180deg, rgba(255, 250, 235, 0.92), rgba(255, 245, 225, 0.88));
  box-shadow: 0 14px 28px rgba(180, 83, 9, 0.08);
}

.score-highlight-card--fitness {
  background:
    radial-gradient(circle at 85% 18%, rgba(125, 211, 252, 0.22), transparent 24%),
    linear-gradient(180deg, rgba(239, 246, 255, 0.94), rgba(236, 253, 250, 0.88));
  box-shadow: 0 14px 28px rgba(14, 116, 144, 0.08);
}

.score-highlight-card__eyebrow {
  display: inline-flex;
  width: fit-content;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  color: rgba(71, 85, 105, 0.88);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.18em;
}

.score-highlight-card__title {
  margin-top: 16px;
  color: #334155;
  font-size: 18px;
  font-weight: 700;
}

.score-highlight-card__value {
  margin-top: 12px;
  font-size: clamp(44px, 5vw, 64px);
  line-height: 0.95;
  font-weight: 900;
  letter-spacing: -0.06em;
}

.score-highlight-card--pe .score-highlight-card__value {
  color: #b45309;
}

.score-highlight-card--fitness .score-highlight-card__value {
  color: #0f766e;
}

.score-highlight-card__value span {
  margin-left: 8px;
  font-size: 18px;
  font-weight: 700;
  color: #64748b;
}

.score-highlight-card__desc {
  margin-top: 14px;
  max-width: 320px;
  color: #64748b;
  font-size: 13px;
  line-height: 1.6;
}

.score-highlight-card__meta {
  margin-top: auto;
  padding-top: 18px;
  color: #94a3b8;
  font-size: 12px;
  letter-spacing: 0.08em;
}

@media (max-width: 768px) {
  .filter-row {
    flex-wrap: wrap;
    gap: 8px;
  }

  .filter-row .el-select,
  .filter-row .el-button {
    width: 100% !important;
  }

  .my-scores-page :deep(.el-card__header) {
    padding: 12px 14px;
  }

  .my-scores-page :deep(.el-card__body) {
    padding: 12px;
  }

  .score-highlight-card {
    min-height: 160px;
  }

  .score-highlight-card :deep(.el-card__body) {
    min-height: 160px;
    padding: 18px 18px 16px;
  }
}
</style>
