<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import type { FormSchema } from '@/components/Form'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import type { SearchExpose } from '@/components/Search'
import { Echart } from '@/components/Echart'
import {
  ElCard,
  ElCol,
  ElDescriptions,
  ElDescriptionsItem,
  ElEmpty,
  ElRow,
  ElStatistic,
  ElTable,
  ElTableColumn,
  ElTabs,
  ElTabPane
} from 'element-plus'
import { getFitnessStudentAnalysisApi, getFitnessStudentOptionsApi } from '@/api/vadmin/fitness'
import { getClassOptionsApi, getGradeOptionsApi, getSchoolOptionsApi } from '@/api/vadmin/sport'
import { useHeaderTheme } from '@/hooks/web/useHeaderTheme'
import { analysisHeroImages } from '@/constants/cockpit'

defineOptions({ name: 'FitnessStudentAnalysis' })

const stageType = ref<'primary' | 'mid' | 'high' | 'university'>('primary')
const lastParams = ref<Record<string, any>>({})
const searchRef = ref<SearchExpose>()

const schoolOptions = ref<any[]>([])
const gradeOptions = ref<any[]>([])
const classOptions = ref<any[]>([])
const studentOptions = ref<any[]>([])
const currentSchoolName = ref<string>('')

const headerThemeMap = {
  primary: { bg: '#0c2137', text: '#f8fafc', hover: 'rgba(56, 189, 248, 0.14)' },
  mid: { bg: '#081426', text: '#f8fafc', hover: 'rgba(45, 212, 191, 0.14)' },
  high: { bg: '#0b1a2e', text: '#f8fafc', hover: 'rgba(20, 184, 166, 0.14)' },
  university: { bg: '#10233d', text: '#f8fafc', hover: 'rgba(125, 211, 252, 0.14)' }
}

const profile = ref<any>(null)
const stats = ref<any>(null)
const detailList = ref<any[]>([])
const detailColumns = ref<any[]>([])

const searchSchema = computed<FormSchema[]>(() => [
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
        await searchRef.value?.setValues({ grade_name: null, class_name: null, student_no: null })
        if (!val) {
          studentOptions.value = []
          return
        }
        const res = await getGradeOptionsApi({ school_name: val }).catch(() => null)
        gradeOptions.value = (res?.data || []).map((i: any) => ({ label: i.label, value: i.grade_name || i.value }))
        await loadStudentOptions({ school_name: val, grade_name: null, class_name: null, student_no: null })
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
        await searchRef.value?.setValues({ class_name: null, student_no: null })
        const schoolName = currentSchoolName.value || searchRef.value?.formModel?.school_name
        if (!val || !schoolName) {
          await loadStudentOptions({
            school_name: schoolName,
            grade_name: val || null,
            class_name: null,
            student_no: null
          })
          return
        }
        const res = await getClassOptionsApi({
          school_name: schoolName,
          grade_name: val
        }).catch(() => null)
        classOptions.value = (res?.data || []).map((i: any) => ({ label: i.label, value: i.class_name || i.value }))
        await loadStudentOptions({ school_name: schoolName, grade_name: val, class_name: null, student_no: null })
      }
    }
  },
  {
    field: 'class_name',
    label: '班级',
    component: 'Select',
    componentProps: {
      options: classOptions.value,
      clearable: true,
      onChange: async (val: string) => {
        await searchRef.value?.setValues({ student_no: null })
        const current = searchRef.value?.formModel || {}
        await loadStudentOptions({
          school_name: current.school_name,
          grade_name: current.grade_name,
          class_name: val || null,
          student_no: null
        })
      }
    }
  },
  {
    field: 'student_no',
    label: '学生',
    component: 'Select',
    required: true,
    componentProps: {
      options: studentOptions.value,
      filterable: true,
      clearable: true
    }
  }
])

const titleText = computed(() => {
  if (!profile.value) return '某学校-学号-学生 体质测试情况分析'
  return `${profile.value.school || '-'}-${profile.value.student_no || '-'}-${profile.value.student_name || '-'} 体质测试情况分析`
})

const heroStats = computed(() => [
  { label: '综合评分', value: Number(comprehensiveScore.value || 0).toFixed(1), suffix: '分' },
  { label: '已测项目', value: Number(stats.value?.tested_item_count || 0), suffix: '项' },
  { label: '及格项目', value: Number(stats.value?.pass_items || 0), suffix: '项' },
  { label: '满分项目', value: Number(stats.value?.full_item_count || 0), suffix: '项' }
])

const comprehensiveScore = computed(() => {
  if (!detailList.value.length) return 0
  const row = detailList.value[0]
  const values = [row.bmi_point, row.lung_point, row.sprint_point, row.sit_point, row.rope_point].map((v) => Number(v) || 0)
  return Number((values.reduce((a, b) => a + b, 0) / values.length).toFixed(2))
})
const comprehensiveTotal = computed(() => {
  const maxList = (radarOptions.radar?.indicator || []).map((i: any) => Number(i?.max) || 0).filter((n: number) => n > 0)
  if (!maxList.length) return 100
  return Number((maxList.reduce((a: number, b: number) => a + b, 0) / maxList.length).toFixed(2))
})

const comprehensiveScoreClass = computed(() => {
  const v = Number(comprehensiveScore.value || 0)
  if (v >= 100) return 'kpi-full-text'
  if (v >= 80) return 'kpi-excellent-text'
  if (v >= 60) return 'kpi-pass-text'
  return 'kpi-fail-text'
})

const radarOptions = reactive<any>({
  title: { text: '学生多维综合评估', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
  tooltip: { trigger: 'item' },
  radar: {
    indicator: []
  },
  series: [{ type: 'radar', data: [] }]
})

const itemScoreTrendOptions = reactive<any>({
  title: { text: '单项分值变化趋势', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0 },
  grid: { left: 25, right: 20, top: 45, bottom: 50, containLabel: true },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', name: '分值' },
  series: []
})

const itemStateTrendOptions = reactive<any>({
  title: { text: '单项状态数量变化', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0 },
  grid: { left: 25, right: 20, top: 45, bottom: 50, containLabel: true },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', name: '项目数' },
  series: [
    { name: '不及格项目数', type: 'bar', data: [], itemStyle: { color: '#F56C6C' } },
    { name: '及格项目数', type: 'bar', data: [], itemStyle: { color: '#E6A23C' } },
    { name: '优秀项目数', type: 'bar', data: [], itemStyle: { color: '#67C23A' } },
    { name: '满分项目数', type: 'bar', data: [], itemStyle: { color: '#000000' } }
  ]
})

const loadStudentOptions = async (params: Record<string, any> = {}) => {
  const res = await getFitnessStudentOptionsApi({ ...params, stage_type: stageType.value }).catch(() => null)
  studentOptions.value = res?.data || []
}

const applyCharts = (data: any) => {
  const scoreTrend = data?.item_score_trend || {}
  itemScoreTrendOptions.xAxis.data = scoreTrend.batches || []
  itemScoreTrendOptions.series = (scoreTrend.series || []).map((s: any, idx: number) => ({
    name: s.name,
    type: 'line',
    smooth: true,
    data: s.values || [],
    label: { show: true, position: 'top' },
    itemStyle: { color: ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#000000'][idx % 5] }
  }))

  const stateTrend = data?.item_state_trend || {}
  itemStateTrendOptions.xAxis.data = stateTrend.batches || []
  itemStateTrendOptions.series[0].data = stateTrend.fail_items || []
  itemStateTrendOptions.series[1].data = stateTrend.pass_items || []
  itemStateTrendOptions.series[2].data = stateTrend.excellent_items || []
  itemStateTrendOptions.series[3].data = stateTrend.full_items || []

  const radar = data?.multi_dim_radar || {}
  const items = radar.items || []
  const values = radar.values || []
  const maxVals = radar.max || []
  const indicators = items
    .map((name: string, idx: number) => ({ name, max: Number(maxVals[idx] || 100) }))
    .filter((i: any) => i.name)
  radarOptions.radar.indicator = indicators
  if (!indicators.length) {
    radarOptions.series[0].data = []
  } else {
    const alignedValues = indicators.map((_: any, idx: number) => Number(values[idx]) || 0)
    radarOptions.series[0].data = [{ name: '当前表现', value: alignedValues }]
  }
}

const loadData = async (params: Record<string, any> = lastParams.value) => {
  const query = { ...params, stage_type: stageType.value }
  lastParams.value = { ...params }
  const res = await getFitnessStudentAnalysisApi(query).catch(() => null)
  if (!res?.data?.profile) {
    profile.value = null
    stats.value = null
    detailList.value = []
    detailColumns.value = []
    return
  }
  profile.value = res.data.profile
  stats.value = res.data.stats || {}
  detailList.value = res.data.detail_list || []
  detailColumns.value = res.data.detail_columns || []
  applyCharts(res.data)
}

const onTabChange = async () => {
  lastParams.value = {}
  currentSchoolName.value = ''
  gradeOptions.value = []
  classOptions.value = []
  studentOptions.value = []
  profile.value = null
  stats.value = null
  detailList.value = []
  await syncSearchValues({ school_name: null, grade_name: null, class_name: null, student_no: null })
  await initDefaultQuery()
}

const syncSearchValues = async (params: Record<string, any>) => {
  await nextTick()
  await searchRef.value?.setValues(params)
}

const initDefaultQuery = async () => {
  const schoolRes = await getSchoolOptionsApi({ stage_type: stageType.value }).catch(() => null)
  schoolOptions.value = (schoolRes?.data || []).map((i: any) => ({ label: i.label, value: i.school_name || i.value }))

  const params: Record<string, any> = { school_name: null, grade_name: null, class_name: null, student_no: null }
  if (schoolOptions.value.length) {
    params.school_name = schoolOptions.value[0].value
    currentSchoolName.value = params.school_name
    const gradeRes = await getGradeOptionsApi({ school_name: params.school_name }).catch(() => null)
    gradeOptions.value = (gradeRes?.data || []).map((i: any) => ({ label: i.label, value: i.grade_name || i.value }))
  }
  await loadStudentOptions(params)
  await syncSearchValues(params)
  await loadData(params)
}

onMounted(async () => {
  await initDefaultQuery()
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
        <Search
          ref="searchRef"
          :schema="searchSchema"
          :show-reset="false"
          @search="(params) => { loadStudentOptions(params); loadData(params) }"
          @reset="(params) => { loadStudentOptions(params); loadData(params) }"
        />
      </div>

      <section class="analysis-hero mb-16px" :style="{ '--analysis-hero-image': `url(${analysisHeroImages.fitnessStudent}) center/cover no-repeat` }">
        <div class="analysis-hero__copy">
          <div class="analysis-hero__eyebrow">FITNESS STUDENT ANALYSIS</div>
          <h1 class="analysis-hero__title">学生 <span>阶段对比</span></h1>
          <p class="analysis-hero__desc">集中查看学生在不同批次中的体测雷达、分值波动和状态数量变化，判断成长是单点提升还是整体抬升。</p>
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
              <div class="analysis-hero__gauge-label">综合评分</div>
              <div class="analysis-hero__gauge-value">{{ comprehensiveScore }}</div>
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

      <ElCard shadow="never" class="analysis-card">
        <div class="card-title">{{ titleText }}</div>

        <div v-if="!profile" class="py-30px"><ElEmpty description="请选择学生后查看体测分析" /></div>

        <template v-else>
        <ElRow :gutter="12" class="analysis-kpi-row mb-14px profile-row">
          <ElCol :xs="24" :sm="24" :md="8" :lg="6" :xl="6" class="stretch-col">
            <ElCard shadow="hover" class="text-center same-height-card score-card">
              <div class="card-subtitle mb-6px">综合评分</div>
              <div class="score-line">
                <span class="text-30px font-700" :class="comprehensiveScoreClass">{{ comprehensiveScore }}</span>
                <span class="score-total">/{{ comprehensiveTotal }}</span>
              </div>
            </ElCard>
          </ElCol>
          <ElCol :xs="24" :sm="24" :md="16" :lg="18" :xl="18" class="stretch-col">
            <ElCard shadow="hover" class="profile-card same-height-card">
            <ElDescriptions :column="4" border class="striped-desc">
              <ElDescriptionsItem label="姓名">{{ profile.student_name }}</ElDescriptionsItem>
              <ElDescriptionsItem label="性别">{{ profile.gender === 'male' ? '男' : '女' }}</ElDescriptionsItem>
              <ElDescriptionsItem label="联系方式">{{ profile.mobile || '-' }}</ElDescriptionsItem>
              <ElDescriptionsItem label="学校">{{ profile.school || '-' }}</ElDescriptionsItem>
              <ElDescriptionsItem label="入学年">{{ profile.enrollment_year || '-' }}</ElDescriptionsItem>
              <ElDescriptionsItem label="年级">{{ profile.grade || '-' }}</ElDescriptionsItem>
              <ElDescriptionsItem label="班级">{{ profile.class_name || '-' }}</ElDescriptionsItem>
              <ElDescriptionsItem label="学号">{{ profile.student_no || '-' }}</ElDescriptionsItem>
              <ElDescriptionsItem label="学段">{{ profile.stage_type || '-' }}</ElDescriptionsItem>
            </ElDescriptions>
            </ElCard>
          </ElCol>
        </ElRow>

        <ElRow :gutter="12" class="mb-14px">
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6">
            <ElCard shadow="hover" class="stat-card">
              <ElStatistic :value="stats.tested_item_count || 0">
                <template #title><span class="card-subtitle">已测项目数</span></template>
              </ElStatistic>
            </ElCard>
          </ElCol>
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6">
            <ElCard shadow="hover" class="kpi-pass stat-card">
              <ElStatistic :value="stats.pass_items || 0">
                <template #title><span class="card-subtitle">及格项目数</span></template>
              </ElStatistic>
            </ElCard>
          </ElCol>
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6">
            <ElCard shadow="hover" class="kpi-fail stat-card">
              <ElStatistic :value="stats.fail_items || 0">
                <template #title><span class="card-subtitle">不及格项目数</span></template>
              </ElStatistic>
            </ElCard>
          </ElCol>
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6">
            <ElCard shadow="hover" class="kpi-excellent stat-card">
              <ElStatistic :value="stats.excellent_item_count || 0">
                <template #title><span class="card-subtitle">优秀项目数</span></template>
              </ElStatistic>
            </ElCard>
          </ElCol>
        </ElRow>

        <ElRow :gutter="12" class="mb-14px">
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6">
            <ElCard shadow="hover" class="kpi-full stat-card">
              <ElStatistic :value="stats.full_item_count || 0">
                <template #title><span class="card-subtitle">满分项目数</span></template>
              </ElStatistic>
            </ElCard>
          </ElCol>
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6">
            <ElCard shadow="hover" class="kpi-fail stat-card text-card">
              <div class="card-subtitle mb-6px">不及格项目</div>
              <div class="text-14px kpi-fail-text">{{ stats.fail_items_text || '-' }}</div>
            </ElCard>
          </ElCol>
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6">
            <ElCard shadow="hover" class="kpi-excellent stat-card text-card">
              <div class="card-subtitle mb-6px">优秀项目</div>
              <div class="text-14px kpi-excellent-text">{{ stats.excellent_items || '-' }}</div>
            </ElCard>
          </ElCol>
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6">
            <ElCard shadow="hover" class="kpi-full stat-card text-card">
              <div class="card-subtitle mb-6px">满分项目</div>
              <div class="text-14px kpi-full-text">{{ stats.full_items || '-' }}</div>
            </ElCard>
          </ElCol>
        </ElRow>

        <ElRow :gutter="14" class="mb-14px">
          <ElCol :xs="24" :sm="24" :md="10" :lg="10" :xl="10"><Echart :options="radarOptions" height="300px" /></ElCol>
          <ElCol :xs="24" :sm="24" :md="14" :lg="14" :xl="14"><Echart :options="itemScoreTrendOptions" height="300px" /></ElCol>
        </ElRow>

        <Echart :options="itemStateTrendOptions" height="300px" class="mb-14px" />

        <ElTable :data="detailList" stripe>
          <ElTableColumn prop="batch_name" label="批次" min-width="160" />
          <ElTableColumn
            v-for="(col, idx) in detailColumns"
            :key="`${col.item_code}-${idx}`"
            :label="col.item_name"
            min-width="130"
            align="center"
          >
            <template #default="{ row }"><div>{{ row.items?.[idx]?.raw_score ?? '-' }}</div><div class="sub-cell">{{ row.items?.[idx]?.score_value ?? 0 }}分</div></template>
          </ElTableColumn>
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
.card-subtitle { font-size: 14px; color: #606266; font-weight: 500; }
.sub-cell { color: #909399; font-size: 12px; }
.profile-row { align-items: stretch; }
.stretch-col { display: flex; }
.same-height-card { width: 100%; }
.stat-card :deep(.el-card__body) {
  min-height: 94px;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.text-card :deep(.el-card__body) { align-items: flex-start; }
.score-card :deep(.el-card__body) {
  min-height: 168px;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.score-line {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 4px;
}
.score-total {
  font-size: 14px;
  font-weight: 500;
  color: #000000;
}
.profile-card { height: 100%; }
.striped-desc :deep(.el-descriptions__body .el-descriptions__table tr:nth-child(odd) td) { background: #f8fafc; }
.kpi-pass :deep(.el-statistic__content-value), .kpi-pass :deep(.el-statistic__content) { color: #E6A23C !important; }
.kpi-fail :deep(.el-statistic__content-value), .kpi-fail :deep(.el-statistic__content) { color: #F56C6C !important; }
.kpi-excellent :deep(.el-statistic__content-value), .kpi-excellent :deep(.el-statistic__content) { color: #67C23A !important; }
.kpi-full :deep(.el-statistic__content-value), .kpi-full :deep(.el-statistic__content) { color: #000000 !important; }
.kpi-pass-text { color: #E6A23C; }
.kpi-fail-text { color: #F56C6C; }
.kpi-excellent-text { color: #67C23A; }
.kpi-full-text { color: #000000; }
</style>

