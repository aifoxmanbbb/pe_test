<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import type { FormSchema } from '@/components/Form'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import type { SearchExpose } from '@/components/Search'
import { Echart } from '@/components/Echart'
import { ElCard, ElCol, ElEmpty, ElRow, ElStatistic, ElTable, ElTableColumn, ElTabs, ElTabPane } from 'element-plus'
import { getPeBatchOptionsApi, getPeOverviewApi } from '@/api/vadmin/pe'
import { getClassOptionsApi, getGradeOptionsApi, getSchoolOptionsApi } from '@/api/vadmin/sport'
import { setCssVar } from '@/utils'
import { analysisHeroImages } from '@/constants/cockpit'

defineOptions({ name: 'PEOverview' })

const stageType = ref<'mid' | 'high'>('mid')
const lastParams = ref<Record<string, any>>({})
const searchRef = ref<SearchExpose>()

const batchOptions = ref<any[]>([])
const schoolOptions = ref<any[]>([])
const gradeOptions = ref<any[]>([])
const classOptions = ref<any[]>([])
const currentSchoolName = ref<string>('')

const result = ref<any>(null)
const classList = ref<any[]>([])
const heroRateValue = computed(() => Number(kpi.value.passRate || 0).toFixed(1))
const heroStatCards = computed(() => [
  { label: '参考人数', value: Number(kpi.value.totalStudents || 0), suffix: '人' },
  { label: '平均分', value: Number(kpi.value.avgScore || 0).toFixed(1), suffix: '分' },
  { label: '优秀率', value: Number(kpi.value.excellentRate || 0).toFixed(1), suffix: '%' },
  { label: '满分率', value: Number(kpi.value.fullRate || 0).toFixed(1), suffix: '%' }
])

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
        currentSchoolName.value = val || ''
        gradeOptions.value = []
        classOptions.value = []
        await searchRef.value?.setValues({ grade_name: null, class_name: null })
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
        await searchRef.value?.setValues({ class_name: null })
        const schoolName = currentSchoolName.value || searchRef.value?.formModel?.school_name
        if (!val || !schoolName) return
        const res = await getClassOptionsApi({
          school_name: schoolName,
          grade_name: val
        }).catch(() => null)
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

const stageLabelMap: Record<string, string> = {
  mid: '初中',
  high: '高中'
}

const headerThemeMap: Record<string, { bg: string; text: string; hover: string }> = {
  mid: { bg: '#140d1f', text: '#f8fafc', hover: 'rgba(245, 158, 11, 0.14)' },
  high: { bg: '#1b223a', text: '#f8fafc', hover: 'rgba(56, 189, 248, 0.14)' }
}

const defaultHeaderTheme = {
  bg: '',
  text: '',
  hover: ''
}

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

const applyHeaderTheme = (stage: string) => {
  const theme = headerThemeMap[stage] || headerThemeMap.mid
  setCssVar('--top-header-bg-color', theme.bg)
  setCssVar('--top-header-text-color', theme.text)
  setCssVar('--top-header-hover-color', theme.hover)
}

const restoreHeaderTheme = () => {
  setCssVar('--top-header-bg-color', defaultHeaderTheme.bg)
  setCssVar('--top-header-text-color', defaultHeaderTheme.text)
  setCssVar('--top-header-hover-color', defaultHeaderTheme.hover)
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
  const rootStyle = getComputedStyle(document.documentElement)
  defaultHeaderTheme.bg = rootStyle.getPropertyValue('--top-header-bg-color').trim()
  defaultHeaderTheme.text = rootStyle.getPropertyValue('--top-header-text-color').trim()
  defaultHeaderTheme.hover = rootStyle.getPropertyValue('--top-header-hover-color').trim()
  applyHeaderTheme(stageType.value)
  await Promise.all([loadBatchOptions(), loadSchoolOptions()])
  const params = await buildDefaultParams()
  await syncSearchValues(params)
  await loadData(params)
})

watch(stageType, (val) => {
  applyHeaderTheme(val)
})

onBeforeUnmount(() => {
  restoreHeaderTheme()
})
</script>

<template>
  <ContentWrap>
    <div class="overview-stage pe-stage">
      <ElTabs v-model="stageType" class="mb-10px overview-tabs" @tab-change="onTabChange">
        <ElTabPane label="初中" name="mid" />
        <ElTabPane label="高中" name="high" />
      </ElTabs>

      <div class="cockpit-search-shell mb-12px">
        <Search
          ref="searchRef"
          :schema="searchSchema"
          :show-reset="false"
          :search-button-circle="true"
          :search-button-icon-only="true"
          search-button-class="cockpit-search-button"
          search-button-icon="ep:refresh-right"
          @search="loadData"
          @reset="loadData"
        />
      </div>

      <section class="cockpit-hero pe-hero mb-16px" :style="{ '--hero-image': `url(${analysisHeroImages.peOverview}) center/cover no-repeat` }">
        <div class="hero-copy">
          <div class="hero-badge">KINETIC PE ANALYSIS</div>
          <h1 class="hero-title">
            成绩
            <span>总览</span>
          </h1>
          <p class="hero-desc">
            查看当前批次的均分、及格率、优秀率和班级分层，直接定位薄弱学校与班级。
          </p>
          <div class="hero-actions">
            <div class="hero-action-pill">{{ mainTitle }}</div>
            <div class="hero-action-sub">当前学段：{{ stageLabelMap[stageType] }}</div>
          </div>
        </div>

        <div class="hero-visual">
          <div class="hero-runner"></div>
          <div class="hero-gauge">
            <div class="hero-gauge-ring"></div>
            <div class="hero-gauge-inner">
              <div class="hero-gauge-label">及格率</div>
              <div class="hero-gauge-value">{{ heroRateValue }}</div>
              <div class="hero-gauge-unit">%</div>
            </div>
          </div>

          <div class="hero-stat-grid">
            <div v-for="item in heroStatCards" :key="item.label" class="hero-stat-card">
              <div class="hero-stat-label">{{ item.label }}</div>
              <div class="hero-stat-value">
                {{ item.value }}
                <span>{{ item.suffix }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <ElCard shadow="never" class="analysis-card">
        <div class="card-title">{{ mainTitle }}</div>

        <div v-if="!result || !kpi.totalStudents" class="py-30px">
          <ElEmpty description="暂无可展示数据" />
        </div>

        <template v-else>
          <ElRow :gutter="14" class="kpi-row mb-14px">
            <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover"><ElStatistic title="参考人数" :value="kpi.totalStudents" /></ElCard></ElCol>
            <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover"><ElStatistic title="平均分" :value="kpi.avgScore" :precision="2" /></ElCard></ElCol>
            <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover" class="kpi-pass"><ElStatistic title="及格率" :value="kpi.passRate" suffix="%" :precision="2" /></ElCard></ElCol>
            <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover" class="kpi-excellent"><ElStatistic title="优秀率" :value="kpi.excellentRate" suffix="%" :precision="2" /></ElCard></ElCol>
            <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover" class="kpi-full"><ElStatistic title="满分率" :value="kpi.fullRate" suffix="%" :precision="2" /></ElCard></ElCol>
          </ElRow>

          <ElRow :gutter="14" class="mb-14px">
            <ElCol :xs="24" :sm="24" :md="14" :lg="14" :xl="14"><Echart :options="itemAvgOptions" height="320px" /></ElCol>
            <ElCol :xs="24" :sm="24" :md="10" :lg="10" :xl="10"><Echart :options="classRateOptions" height="320px" /></ElCol>
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
    </div>
  </ContentWrap>
</template>

<style scoped>
.overview-stage {
  position: relative;
  overflow: hidden;
  border-radius: 0;
  margin: -20px;
  padding: 20px;
  background:
    radial-gradient(circle at 14% 10%, rgba(250, 204, 21, 0.14), transparent 24%),
    radial-gradient(circle at 82% 16%, rgba(56, 189, 248, 0.15), transparent 22%),
    linear-gradient(180deg, rgba(20, 13, 31, 0.97), rgba(24, 18, 42, 0.92) 28%, rgba(243, 244, 246, 0.95) 62%, rgba(248, 250, 252, 0.98) 100%);
  box-shadow: 0 32px 70px rgba(20, 13, 31, 0.18);
}

.overview-stage::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(148, 163, 184, 0.08) 1px, transparent 1px),
    linear-gradient(rgba(148, 163, 184, 0.08) 1px, transparent 1px);
  background-size: 22px 22px;
  opacity: 0.18;
  pointer-events: none;
}

.overview-stage::after {
  content: '';
  position: absolute;
  inset: 180px auto auto -10%;
  width: 420px;
  height: 420px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(245, 158, 11, 0.14), transparent 66%);
  filter: blur(14px);
  pointer-events: none;
}

.overview-stage > * {
  position: relative;
  z-index: 1;
}

.overview-stage > .analysis-card {
  position: relative;
  margin-top: 14px;
}

.overview-stage > .analysis-card::before {
  content: '';
  position: absolute;
  left: 28px;
  right: 28px;
  top: -18px;
  height: 42px;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0), rgba(244, 247, 251, 0.58));
  filter: blur(10px);
  pointer-events: none;
}

.overview-tabs :deep(.el-tabs__header) {
  margin-bottom: 10px;
}

.overview-tabs :deep(.el-tabs__item) {
  padding: 0 16px;
  color: rgba(226, 232, 240, 0.76);
  font-weight: 700;
}

.overview-tabs :deep(.el-tabs__item.is-active) {
  color: #f8fafc;
}

.overview-tabs :deep(.el-tabs__active-bar) {
  background: linear-gradient(90deg, #f59e0b, #38bdf8);
}

.overview-tabs :deep(.el-tabs__nav-wrap::after) {
  background-color: transparent;
}

.cockpit-hero {
  position: relative;
  overflow: hidden;
  border-radius: 32px;
  padding: 32px;
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(320px, 0.95fr);
  gap: 24px;
  color: #f8fafc;
  background:
    linear-gradient(180deg, rgba(8, 16, 30, 0.16), rgba(8, 16, 30, 0.52)),
    var(--hero-image, linear-gradient(135deg, rgba(250, 204, 21, 0.1), rgba(31, 47, 73, 0.22))),
    radial-gradient(circle at top left, rgba(250, 204, 21, 0.15), transparent 30%),
    radial-gradient(circle at 82% 18%, rgba(16, 185, 129, 0.2), transparent 28%),
    linear-gradient(135deg, #140d1f 0%, #1b1530 48%, #1f2f49 100%);
  background-size: cover, cover, auto, auto, auto;
  background-position: center, center, center, center, center;
  box-shadow: 0 28px 60px rgba(20, 13, 31, 0.26);
}

.cockpit-hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(rgba(148, 163, 184, 0.12) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.12) 1px, transparent 1px),
    linear-gradient(135deg, rgba(7, 11, 24, 0.08), rgba(7, 11, 24, 0.42));
  background-size: 24px 24px, 24px 24px, auto;
  opacity: 0.2;
  pointer-events: none;
}

.cockpit-hero::after {
  content: '';
  position: absolute;
  inset: auto -10% -24% auto;
  width: 460px;
  height: 460px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.18), transparent 66%);
  filter: blur(14px);
  pointer-events: none;
}

.hero-copy,
.hero-visual {
  position: relative;
  z-index: 1;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 999px;
  border: 1px solid rgba(250, 204, 21, 0.18);
  background: rgba(245, 158, 11, 0.16);
  color: #fcd34d;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.18em;
}

.hero-title {
  margin: 22px 0 10px;
  font-size: clamp(58px, 8vw, 104px);
  line-height: 0.88;
  font-weight: 900;
  letter-spacing: -0.06em;
}

.hero-title span {
  display: block;
  color: #67e8f9;
  text-shadow: 0 0 24px rgba(103, 232, 249, 0.26);
}

.hero-desc {
  max-width: 520px;
  color: rgba(226, 232, 240, 0.8);
  font-size: 16px;
  line-height: 1.8;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-top: 28px;
}

.hero-action-pill {
  padding: 14px 20px;
  border-radius: 18px;
  background: linear-gradient(135deg, #0f766e 0%, #0ea5e9 100%);
  color: #ecfeff;
  font-weight: 800;
  box-shadow: 0 12px 28px rgba(14, 165, 233, 0.18);
}

.hero-action-sub {
  color: rgba(226, 232, 240, 0.72);
  font-size: 13px;
  letter-spacing: 0.08em;
}

.hero-visual {
  position: relative;
  display: grid;
  grid-template-columns: minmax(180px, 240px) minmax(0, 1fr);
  gap: 18px;
  align-items: center;
  min-height: 340px;
}

.hero-runner {
  position: absolute;
  inset: 18px 12px 14px 8px;
  border-radius: 32px;
  background:
    radial-gradient(circle at 28% 30%, rgba(250, 204, 21, 0.22), transparent 32%),
    radial-gradient(circle at 72% 64%, rgba(56, 189, 248, 0.2), transparent 28%),
    linear-gradient(180deg, rgba(20, 13, 31, 0.06), rgba(20, 13, 31, 0.3));
  opacity: 0.9;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.06);
  overflow: hidden;
}

.hero-runner::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 68% 46%, rgba(250, 204, 21, 0.18), transparent 28%),
    linear-gradient(135deg, rgba(20, 13, 31, 0.04), rgba(20, 13, 31, 0.28));
}

.hero-gauge {
  position: relative;
  width: 220px;
  height: 220px;
  justify-self: center;
  display: grid;
  place-items: center;
}

.hero-gauge-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background:
    radial-gradient(circle at center, rgba(20, 13, 31, 0.96) 54%, transparent 55%),
    conic-gradient(from 190deg, rgba(250, 204, 21, 0.15), #f59e0b, #38bdf8, rgba(56, 189, 248, 0.18));
  box-shadow: inset 0 0 40px rgba(250, 204, 21, 0.12), 0 0 36px rgba(56, 189, 248, 0.18);
}

.hero-gauge-inner {
  position: relative;
  display: grid;
  place-items: center;
  text-align: center;
}

.hero-gauge-label {
  color: rgba(148, 163, 184, 0.92);
  font-size: 13px;
  letter-spacing: 0.18em;
}

.hero-gauge-value {
  font-size: 64px;
  line-height: 1;
  font-weight: 900;
  letter-spacing: -0.06em;
}

.hero-gauge-unit {
  color: #fcd34d;
  font-size: 18px;
  font-weight: 700;
}

.hero-stat-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.hero-stat-card {
  padding: 18px;
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.08));
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.14);
}

.hero-stat-label {
  color: rgba(226, 232, 240, 0.72);
  font-size: 12px;
  letter-spacing: 0.12em;
}

.hero-stat-value {
  margin-top: 10px;
  font-size: 34px;
  line-height: 1;
  font-weight: 800;
}

.hero-stat-value span {
  margin-left: 6px;
  font-size: 13px;
  color: rgba(191, 219, 254, 0.85);
}

.cockpit-search-shell :deep(.el-form) {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 12px;
}

.cockpit-search-shell :deep(.el-form-item) {
  margin-bottom: 0;
  min-width: 0;
}

.cockpit-search-shell :deep(.el-form-item__content) {
  min-width: 0;
}

.cockpit-search-shell :deep(.el-form-item__content > :first-child) {
  min-width: 0 !important;
  width: 100%;
}

.cockpit-search-shell :deep(.cockpit-search-button) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  min-width: 42px;
  height: 42px;
  min-height: 42px;
  padding: 0;
  border: none;
  border-radius: 999px;
  background: linear-gradient(135deg, #0f766e 0%, #0ea5e9 100%);
  box-shadow: 0 10px 22px rgba(14, 165, 233, 0.18);
}

.cockpit-search-shell :deep(.cockpit-search-button .el-icon) {
  margin: 0;
  font-size: 18px;
}

.cockpit-search-shell :deep(.cockpit-search-button > span:empty) {
  display: none;
}

@media (min-width: 1200px) {
  .cockpit-search-shell :deep(.el-form) {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr)) 42px;
    align-items: center;
    gap: 10px 12px;
  }

  .cockpit-search-shell :deep(.el-form-item:not(:last-child)) {
    min-width: 0;
  }

  .cockpit-search-shell :deep(.el-form-item:last-child) {
    justify-self: end;
    min-width: 42px;
    width: 42px;
  }
}

.analysis-card {
  border-radius: 28px;
  border: none;
  background: linear-gradient(180deg, rgba(246, 248, 251, 0.76), rgba(243, 246, 250, 0.9));
  backdrop-filter: blur(18px);
  box-shadow: 0 22px 44px rgba(15, 23, 42, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.28);
}
.analysis-card :deep(.el-card__body) {
  padding: 24px;
}
.card-title { text-align: center; font-size: 22px; font-weight: 700; margin-bottom: 16px; }
.sub-cell { color: #909399; font-size: 12px; }
.analysis-card :deep(.el-statistic__head) { font-size: 14px; color: #606266; font-weight: 500; }
.analysis-card :deep(.el-card) {
  border-radius: 20px;
  border: none;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.64), rgba(246, 248, 251, 0.88));
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.06);
}
.analysis-card :deep(.el-row > .el-col .el-card__body) {
  padding: 18px 16px;
}

.analysis-card :deep(.kpi-row > .el-col) {
  margin-bottom: 14px;
}

.analysis-card :deep(.el-table) {
  --el-table-bg-color: rgba(255, 255, 255, 0.62);
  --el-table-tr-bg-color: rgba(255, 255, 255, 0.4);
  --el-table-header-bg-color: rgba(241, 245, 249, 0.88);
}
.kpi-pass :deep(.el-statistic__content-value), .kpi-pass :deep(.el-statistic__content), .kpi-pass-text { color: #E6A23C !important; }
.kpi-fail :deep(.el-statistic__content-value), .kpi-fail :deep(.el-statistic__content), .kpi-fail-text { color: #F56C6C !important; }
.kpi-excellent :deep(.el-statistic__content-value), .kpi-excellent :deep(.el-statistic__content), .kpi-excellent-text { color: #67C23A !important; }
.kpi-full :deep(.el-statistic__content-value), .kpi-full :deep(.el-statistic__content), .kpi-full-text { color: #000000 !important; }

@media (max-width: 1024px) {
  .cockpit-hero {
    grid-template-columns: 1fr;
  }

  .hero-visual {
    grid-template-columns: 1fr;
  }

  .hero-runner {
    inset: 0;
    opacity: 0.24;
  }
}

@media (max-width: 768px) {
  .overview-stage {
    margin: -14px;
    padding: 14px;
    border-radius: 0;
  }

  .analysis-card :deep(.el-card__body) {
    padding: 18px;
  }

  .overview-stage > .analysis-card::before {
    left: 14px;
    right: 14px;
  }

  .cockpit-hero {
    padding: 22px;
    border-radius: 24px;
  }

  .hero-title {
    font-size: 56px;
  }

  .hero-stat-grid {
    grid-template-columns: 1fr;
  }

  .hero-gauge {
    width: 188px;
    height: 188px;
  }

  .hero-gauge-value {
    font-size: 52px;
  }

  .overview-tabs :deep(.el-tabs__item) {
    padding: 0 12px;
  }

  .cockpit-search-shell :deep(.el-form) {
    align-items: stretch;
  }

  .cockpit-search-shell :deep(.el-form-item) {
    width: 100%;
  }

  .hero-runner {
    border-radius: 24px;
  }
}
</style>

