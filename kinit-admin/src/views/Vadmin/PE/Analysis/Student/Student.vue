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
import { BaseButton } from '@/components/Button'
import { getPeStudentAnalysisApi, getPeStudentOptionsApi } from '@/api/vadmin/pe'
import { getClassOptionsApi, getGradeOptionsApi, getSchoolOptionsApi } from '@/api/vadmin/sport'

defineOptions({ name: 'PEStudentAnalysis' })

const stageType = ref<'mid' | 'high'>('mid')
const lastParams = ref<Record<string, any>>({})
const searchRef = ref<SearchExpose>()

const schoolOptions = ref<any[]>([])
const gradeOptions = ref<any[]>([])
const classOptions = ref<any[]>([])
const studentOptions = ref<any[]>([])
const currentSchoolName = ref<string>('')

const profile = ref<any>(null)
const stats = ref<any>(null)
const detailList = ref<any[]>([])

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
  if (!profile.value) return '某学校-学号-学生 体育项目情况分析'
  return `${profile.value.school || '-'}-${profile.value.student_no || '-'}-${profile.value.student_name || '-'} 体育项目情况分析`
})

const comprehensiveScore = computed(() => Number(stats.value?.latest_total || 0))
const comprehensiveTotal = computed(() => {
  const fullLine = totalTrendOptions.series?.[3]?.data || []
  for (let i = fullLine.length - 1; i >= 0; i--) {
    const v = Number(fullLine[i] || 0)
    if (v > 0) return v
  }
  return 100
})
const comprehensiveScoreClass = computed(() => {
  const v = Number(comprehensiveScore.value || 0)
  const passLine = Number(totalTrendOptions.series[1].data?.slice(-1)?.[0] || 0)
  const excellentLine = Number(totalTrendOptions.series[2].data?.slice(-1)?.[0] || 0)
  const fullLine = Number(totalTrendOptions.series[3].data?.slice(-1)?.[0] || 0)
  if (fullLine > 0 && v >= fullLine) return 'kpi-full-text'
  if (excellentLine > 0 && v >= excellentLine) return 'kpi-excellent-text'
  if (passLine > 0 && v >= passLine) return 'kpi-pass-text'
  return 'kpi-fail-text'
})

const totalTrendOptions = reactive<any>({
  title: { text: '总分趋势', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0 },
  grid: { left: 25, right: 20, top: 45, bottom: 50, containLabel: true },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', name: '总分' },
  series: [
    { name: '总分', type: 'line', smooth: true, data: [], itemStyle: { color: '#409EFF' }, label: { show: true, position: 'top' } },
    { name: '及格线', type: 'line', smooth: true, data: [], lineStyle: { color: '#E6A23C', type: 'dashed' } },
    { name: '优秀线', type: 'line', smooth: true, data: [], lineStyle: { color: '#67C23A', type: 'dashed' } },
    { name: '满分线', type: 'line', smooth: true, data: [], lineStyle: { color: '#000000', type: 'dashed' } }
  ]
})

const itemTrendOptions = reactive<any>({
  title: { text: '项目变化趋势', left: 'center', textStyle: { fontSize: 14, fontWeight: 600 } },
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0 },
  grid: { left: 25, right: 20, top: 45, bottom: 50, containLabel: true },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', name: '分值' },
  series: []
})

const loadStudentOptions = async (params: Record<string, any> = {}) => {
  const res = await getPeStudentOptionsApi({ ...params, stage_type: stageType.value }).catch(() => null)
  studentOptions.value = res?.data || []
}

const applyCharts = (data: any) => {
  const total = data?.total_trend || {}
  totalTrendOptions.xAxis.data = total.batches || []
  totalTrendOptions.series[0].data = total.total || []
  totalTrendOptions.series[1].data = total.pass_line || []
  totalTrendOptions.series[2].data = total.excellent_line || []
  totalTrendOptions.series[3].data = total.full_line || []

  const itemTrend = data?.item_trend || {}
  itemTrendOptions.xAxis.data = itemTrend.batches || []
  itemTrendOptions.series = (itemTrend.series || []).map((s: any, idx: number) => ({
    name: s.name,
    type: 'bar',
    data: s.values || [],
    label: { show: true, position: 'top' },
    itemStyle: { color: ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#000000'][idx % 5] }
  }))
}

const loadData = async (params: Record<string, any> = lastParams.value) => {
  const query = { ...params, stage_type: stageType.value }
  lastParams.value = { ...params }

  const res = await getPeStudentAnalysisApi(query).catch(() => null)
  if (!res?.data?.profile) {
    profile.value = null
    stats.value = null
    detailList.value = []
    return
  }

  profile.value = res.data.profile
  stats.value = res.data.stats || {}
  detailList.value = res.data.detail_list || []
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

const exportChart = () => {
  ElMessage.success('图表导出能力将在下一步对接文件下载。')
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
</script>

<template>
  <ContentWrap>
    <ElTabs v-model="stageType" class="mb-10px" @tab-change="onTabChange">
      <ElTabPane label="初中" name="mid" />
      <ElTabPane label="高中" name="high" />
    </ElTabs>

    <div class="flex items-start gap-10px mb-12px">
      <Search
        ref="searchRef"
        :schema="searchSchema"
        class="flex-1"
        @search="(params) => { loadStudentOptions(params); loadData(params) }"
        @reset="(params) => { loadStudentOptions(params); loadData(params) }"
      />
      <BaseButton type="primary" @click="exportChart">导出图表</BaseButton>
    </div>

    <ElCard shadow="never" class="analysis-card">
      <div class="card-title">{{ titleText }}</div>

      <div v-if="!profile" class="py-30px"><ElEmpty description="请选择学生后查看阶段对比" /></div>

      <template v-else>
        <ElRow :gutter="12" class="mb-14px profile-row">
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
                <ElDescriptionsItem label="学段">{{ profile.exam_type || '-' }}</ElDescriptionsItem>
              </ElDescriptions>
            </ElCard>
          </ElCol>
        </ElRow>

        <ElRow :gutter="12" class="mb-14px">
          <ElCol :xs="24" :sm="12" :md="8" :lg="6" :xl="6">
            <ElCard shadow="hover" class="stat-card">
              <ElStatistic :value="stats.history_max_total || 0">
                <template #title><span class="card-subtitle">历史最高总分</span></template>
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
          <ElCol :xs="24" :sm="24" :md="10" :lg="10" :xl="10"><Echart :options="totalTrendOptions" height="300px" /></ElCol>
          <ElCol :xs="24" :sm="24" :md="14" :lg="14" :xl="14"><Echart :options="itemTrendOptions" height="300px" /></ElCol>
        </ElRow>

        <ElTable :data="detailList" stripe>
          <ElTableColumn prop="batch_name" label="批次" min-width="160" />
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
          <ElTableColumn prop="teacher_comment" label="老师评语" min-width="200" show-overflow-tooltip />
        </ElTable>
      </template>
    </ElCard>
  </ContentWrap>
</template>

<style scoped>
.analysis-card { border-radius: 10px; }
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
