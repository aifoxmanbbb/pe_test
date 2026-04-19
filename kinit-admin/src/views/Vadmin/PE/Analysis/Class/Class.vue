<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import type { FormSchema } from '@/components/Form'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import type { SearchExpose } from '@/components/Search'
import { Echart } from '@/components/Echart'
import { ElCard, ElCol, ElEmpty, ElRow, ElStatistic, ElTable, ElTableColumn, ElTabs, ElTabPane } from 'element-plus'
import { getPeBatchOptionsApi, getPeClassAnalysisApi } from '@/api/vadmin/pe'
import { getClassOptionsApi, getGradeOptionsApi, getSchoolOptionsApi } from '@/api/vadmin/sport'
import { useHeaderTheme } from '@/hooks/web/useHeaderTheme'
import { analysisHeroImages } from '@/constants/cockpit'

defineOptions({ name: 'PEClassAnalysis' })

const stageType = ref<'mid' | 'high'>('mid')
const lastParams = ref<Record<string, any>>({})
const searchRef = ref<SearchExpose>()

const batchOptions = ref<any[]>([])
const schoolOptions = ref<any[]>([])
const gradeOptions = ref<any[]>([])
const classOptions = ref<any[]>([])
const currentSchoolName = ref<string>('')

const headerThemeMap = {
  mid: { bg: '#140d1f', text: '#f8fafc', hover: 'rgba(245, 158, 11, 0.14)' },
  high: { bg: '#1b223a', text: '#f8fafc', hover: 'rgba(56, 189, 248, 0.14)' }
}

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
  const schoolText = p.school_name || '-'
  const gradeText = p.grade_name || '-'
  const classText = p.class_name || '-'
  return `${batchText}-${schoolText}-${gradeText}-${classText} 体育项目情况分析`
})

const heroGaugeValue = computed(() => Number(kpi.value?.avg_score || 0).toFixed(1))
const heroStats = computed(() => [
  { label: '班级均分', value: Number(kpi.value?.avg_score || 0).toFixed(1), suffix: '分' },
  { label: '及格率', value: Number(kpi.value?.pass_rate || 0).toFixed(1), suffix: '%' },
  { label: '优秀率', value: Number(kpi.value?.excellent_rate || 0).toFixed(1), suffix: '%' },
  { label: '满分率', value: Number(kpi.value?.full_rate || 0).toFixed(1), suffix: '%' }
])

const historyAvgOptions = reactive<any>({
  title: { text: '历史均分趋势', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0 },
  grid: { left: 25, right: 20, top: 45, bottom: 50, containLabel: true },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', name: '分值' },
  series: []
})

const historyItemOptions = reactive<any>({
  title: { text: '历史项目趋势', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0 },
  grid: { left: 25, right: 20, top: 45, bottom: 50, containLabel: true },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', name: '分值' },
  series: []
})

const applyCharts = (data: any) => {
  const historyAvg = data?.history_avg || {}
  historyAvgOptions.xAxis.data = historyAvg.batches || []
  historyAvgOptions.series = (historyAvg.series || []).map((s: any, idx: number) => ({
    name: s.name,
    type: 'line',
    smooth: true,
    data: s.values || [],
    label: { show: true, position: 'top' },
    itemStyle: { color: ['#409EFF', '#67C23A', '#E6A23C', '#000000'][idx % 4] }
  }))

  const item = data?.history_item_bar || {}
  historyItemOptions.xAxis.data = item.batches || []
  historyItemOptions.series = [
    { name: '跳绳', type: 'bar', data: item.rope_avg || [], itemStyle: { color: '#409EFF' }, label: { show: true, position: 'top' } },
    { name: '跳远', type: 'bar', data: item.jump_avg || [], itemStyle: { color: '#67C23A' }, label: { show: true, position: 'top' } },
    { name: '实心球', type: 'bar', data: item.ball_avg || [], itemStyle: { color: '#E6A23C' }, label: { show: true, position: 'top' } }
  ]

  const threshold = item.threshold || {}
  historyItemOptions.series.push(
    { name: '及格阈值', type: 'line', data: Array((item.batches || []).length).fill(threshold.pass || 10), lineStyle: { color: '#E6A23C', type: 'dashed' } },
    { name: '优秀阈值', type: 'line', data: Array((item.batches || []).length).fill(threshold.excellent || 14), lineStyle: { color: '#67C23A', type: 'dashed' } },
    { name: '满分阈值', type: 'line', data: Array((item.batches || []).length).fill(threshold.full || 20), lineStyle: { color: '#000000', type: 'dashed' } }
  )
}

const loadData = async (params: Record<string, any> = lastParams.value) => {
  const query = { ...params, stage_type: stageType.value }
  lastParams.value = { ...params }
  const res = await getPeClassAnalysisApi(query).catch(() => null)
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

useHeaderTheme(() => stageType.value, headerThemeMap, 'mid')
</script>

<template>
  <ContentWrap>
    <div class="analysis-stage analysis-stage--pe">
      <ElTabs v-model="stageType" class="analysis-tabs mb-10px" @tab-change="onTabChange">
        <ElTabPane label="初中" name="mid" />
        <ElTabPane label="高中" name="high" />
      </ElTabs>

      <div class="analysis-search-shell mb-12px">
        <Search ref="searchRef" :schema="searchSchema" :show-reset="false" @search="loadData" @reset="loadData" />
      </div>

      <section class="analysis-hero mb-16px" :style="{ '--analysis-hero-image': `url(${analysisHeroImages.peClass}) center/cover no-repeat` }">
        <div class="analysis-hero__copy">
          <div class="analysis-hero__eyebrow">PE CLASS ANALYSIS</div>
          <h1 class="analysis-hero__title">班级 <span>对比</span></h1>
          <p class="analysis-hero__desc">聚焦单个班级的历史均分、项目表现和分层情况，直接识别班级训练结构是否均衡。</p>
          <div class="analysis-hero__meta">
            <div class="analysis-hero__pill">{{ titleText }}</div>
            <div class="analysis-hero__sub">当前学段：{{ stageType === 'mid' ? '初中' : '高中' }}</div>
          </div>
        </div>
        <div class="analysis-hero__visual">
          <div class="analysis-hero__runner"></div>
          <div class="analysis-hero__gauge">
            <div class="analysis-hero__gauge-ring"></div>
            <div class="analysis-hero__gauge-inner">
              <div class="analysis-hero__gauge-label">班级均分</div>
              <div class="analysis-hero__gauge-value">{{ heroGaugeValue }}</div>
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

        <div v-if="!kpi" class="py-30px"><ElEmpty description="请选择班级并查询" /></div>

        <template v-else>
          <ElRow :gutter="12" class="analysis-kpi-row mb-14px">
            <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover"><ElStatistic title="班级平均分" :value="kpi.avg_score || 0" :precision="2" /></ElCard></ElCol>
            <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover" class="kpi-pass"><ElStatistic title="及格率" :value="kpi.pass_rate || 0" suffix="%" :precision="2" /></ElCard></ElCol>
            <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover" class="kpi-excellent"><ElStatistic title="优秀率" :value="kpi.excellent_rate || 0" suffix="%" :precision="2" /></ElCard></ElCol>
            <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6"><ElCard shadow="hover" class="kpi-full"><ElStatistic title="满分率" :value="kpi.full_rate || 0" suffix="%" :precision="2" /></ElCard></ElCol>
          </ElRow>

          <ElRow :gutter="14" class="mb-14px">
            <ElCol :xs="24" :sm="24" :md="12" :lg="12" :xl="12"><Echart :options="historyAvgOptions" height="320px" /></ElCol>
            <ElCol :xs="24" :sm="24" :md="12" :lg="12" :xl="12"><Echart :options="historyItemOptions" height="320px" /></ElCol>
          </ElRow>

          <ElTable :data="rankList" stripe>
            <ElTableColumn prop="rank" label="排名" min-width="70" align="center" />
            <ElTableColumn prop="student_name" label="学生" min-width="100" />
            <ElTableColumn prop="gender" label="性别" min-width="70" align="center">
              <template #default="{ row }">{{ row.gender === 'male' ? '男' : '女' }}</template>
            </ElTableColumn>
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
            <ElTableColumn prop="total_score" label="总分" min-width="90" align="center" />
            <ElTableColumn label="及格" min-width="70" align="center">
              <template #default="{ row }"><span :class="row.pass_state ? 'kpi-pass-text' : 'kpi-fail-text'">{{ row.pass_state ? '及格' : '不及格' }}</span></template>
            </ElTableColumn>
            <ElTableColumn label="优秀" min-width="70" align="center">
              <template #default="{ row }"><span class="kpi-excellent-text">{{ row.excellent_state ? '优秀' : '-' }}</span></template>
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
.sub-cell { color: #909399; font-size: 12px; }
.analysis-card :deep(.el-statistic__head) { font-size: 14px; color: #606266; font-weight: 500; }
.kpi-pass :deep(.el-statistic__content-value), .kpi-pass :deep(.el-statistic__content), .kpi-pass-text { color: #E6A23C !important; }
.kpi-fail :deep(.el-statistic__content-value), .kpi-fail :deep(.el-statistic__content), .kpi-fail-text { color: #F56C6C !important; }
.kpi-excellent :deep(.el-statistic__content-value), .kpi-excellent :deep(.el-statistic__content), .kpi-excellent-text { color: #67C23A !important; }
.kpi-full :deep(.el-statistic__content-value), .kpi-full :deep(.el-statistic__content), .kpi-full-text { color: #000000 !important; }
</style>

