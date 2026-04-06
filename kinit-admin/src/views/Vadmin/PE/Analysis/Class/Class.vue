<script setup lang="tsx">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import { ElRow, ElCol, ElCard, ElTag, ElTabs, ElTabPane } from 'element-plus'
import { Echart } from '@/components/Echart'
import { Table, TableColumn } from '@/components/Table'
import { getPeClassAnalysisApi } from '@/api/vadmin/pe'

defineOptions({
  name: 'ClassAnalysis'
})

const examTypeTab = ref('mid')

const searchSchema = reactive<FormSchema[]>([
  {
    field: 'batch_id',
    label: '批次',
    component: 'Select',
    componentProps: {
      placeholder: '请选择批次',
      options: [{ label: '2026春季体考', value: 1 }]
    }
  },
  {
    field: 'school_id',
    label: '学校',
    component: 'Select',
    componentProps: {
      placeholder: '请选择学校',
      options: [
        { label: '第一中学', value: 1 },
        { label: '实验中学', value: 2 }
      ]
    }
  },
  {
    field: 'grade_id',
    label: '年级',
    component: 'Select',
    componentProps: {
      placeholder: '请选择年级',
      options: [{ label: '初三', value: 3 }]
    }
  },
  {
    field: 'class_id',
    label: '班级',
    component: 'Select',
    componentProps: {
      placeholder: '请选择班级',
      options: [
        { label: '3年1班', value: 1 },
        { label: '3年2班', value: 2 }
      ]
    }
  }
])

const searchParams = ref<Record<string, any>>({})
const setSearchParams = (data: Record<string, any>) => {
  searchParams.value = data
  loadData()
}

const panelTitle = computed(() => '某批次-某学校-年级-班级 体育项目情况分析')

const kpiData = ref({
  avg_score: 40.8,
  pass_rate: 86.3,
  excellent_rate: 28.4,
  full_rate: 5.2
})

const historyAvgTrendOptions = reactive({
  title: { text: '批次均分趋势', textStyle: { fontSize: 15, fontWeight: 'normal' } },
  tooltip: { trigger: 'axis' },
  legend: { data: ['门槛项均分', '跳绳均分', '跳远均分', '实心球均分'] },
  xAxis: { type: 'category', data: ['2025春', '2025秋', '2026春', '2026秋'] },
  yAxis: { type: 'value', max: 20 },
  series: [
    { name: '门槛项均分', type: 'line', smooth: true, data: [9.8, 10.4, 10.9, 11.2] },
    { name: '跳绳均分', type: 'line', smooth: true, data: [15.6, 16.3, 17.0, 17.4] },
    { name: '跳远均分', type: 'line', smooth: true, data: [9.8, 10.2, 10.9, 11.1] },
    { name: '实心球均分', type: 'line', smooth: true, data: [8.9, 9.3, 10.0, 10.4] }
  ]
})

const historyItemBarOptions = reactive({
  title: { text: '批次项目均分', textStyle: { fontSize: 15, fontWeight: 'normal' } },
  tooltip: { trigger: 'axis' },
  legend: { data: ['跳绳均分', '跳远均分', '实心球均分', '及格线', '优秀线', '满分线'] },
  xAxis: { type: 'category', data: ['2025春', '2025秋', '2026春', '2026秋'] },
  yAxis: { type: 'value', max: 20 },
  series: [
    {
      name: '跳绳均分',
      type: 'bar',
      data: [15.6, 16.3, 17.0, 17.4],
      label: { show: true, position: 'top', formatter: '{c}分' }
    },
    {
      name: '跳远均分',
      type: 'bar',
      data: [9.8, 10.2, 10.9, 11.1],
      label: { show: true, position: 'top', formatter: '{c}分' }
    },
    {
      name: '实心球均分',
      type: 'bar',
      data: [8.9, 9.3, 10.0, 10.4],
      label: { show: true, position: 'top', formatter: '{c}分' },
      markLine: {
        symbol: 'none',
        data: [
          { yAxis: 10, name: '及格线', lineStyle: { color: '#E6A23C' } },
          { yAxis: 14, name: '优秀线', lineStyle: { color: '#67C23A' } },
          { yAxis: 20, name: '满分线', lineStyle: { color: '#000000' } }
        ]
      }
    }
  ]
})

const rankData = ref([
  {
    rank: 1,
    student_name: '张三',
    gender: '男',
    student_no: '2023030101',
    gate_score: '3分52秒',
    gate_point: 12,
    rope_score: '190次',
    rope_point: 19,
    jump_score: '2.34m',
    jump_point: 14,
    ball_score: '9.2m',
    ball_point: 13,
    total_score: 46,
    pass_state: true,
    excellent_state: true,
    teacher_comment: '技术稳定，冲刺阶段建议加强爆发力。'
  },
  {
    rank: 2,
    student_name: '李四',
    gender: '女',
    student_no: '2023030102',
    gate_score: '4分01秒',
    gate_point: 10,
    rope_score: '182次',
    rope_point: 18,
    jump_score: '1.95m',
    jump_point: 12,
    ball_score: '6.1m',
    ball_point: 12,
    total_score: 42,
    pass_state: true,
    excellent_state: true,
    teacher_comment: '门槛项仍有提升空间，需稳定节奏。'
  },
  {
    rank: 3,
    student_name: '王五',
    gender: '男',
    student_no: '2023030103',
    gate_score: '4分18秒',
    gate_point: 8,
    rope_score: '168次',
    rope_point: 16,
    jump_score: '2.14m',
    jump_point: 9,
    ball_score: '7.6m',
    ball_point: 8,
    total_score: 35,
    pass_state: false,
    excellent_state: false,
    teacher_comment: '门槛项需重点补训，先保证基础达线。'
  }
])

const renderScorePoint = (score: string, point: number) => (
  <div class="leading-5">
    <div>{score}</div>
    <div class="text-12px text-gray-500">{point}分</div>
  </div>
)

const tableColumns = reactive<TableColumn[]>([
  { field: 'rank', label: '排名', width: '70px' },
  { field: 'student_name', label: '学生', width: '90px' },
  { field: 'gender', label: '性别', width: '70px' },
  { field: 'student_no', label: '学号', width: '120px' },
  {
    field: 'gate_item',
    label: '门槛项(成绩/分)',
    minWidth: '130px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.gate_score, data.row.gate_point)
    }
  },
  {
    field: 'rope_item',
    label: '跳绳(成绩/分)',
    minWidth: '120px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.rope_score, data.row.rope_point)
    }
  },
  {
    field: 'jump_item',
    label: '跳远(成绩/分)',
    minWidth: '120px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.jump_score, data.row.jump_point)
    }
  },
  {
    field: 'ball_item',
    label: '实心球(成绩/分)',
    minWidth: '130px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.ball_score, data.row.ball_point)
    }
  },
  { field: 'total_score', label: '总分', width: '80px' },
  {
    field: 'pass_state',
    label: '及格状态',
    width: '90px',
    slots: {
      default: (data: any) =>
        data.row.pass_state ? (
          <ElTag style={{ backgroundColor: '#e6a23c', borderColor: '#e6a23c', color: '#fff' }}>
            及格
          </ElTag>
        ) : (
          <ElTag type="danger">不及格</ElTag>
        )
    }
  },
  {
    field: 'excellent_state',
    label: '优秀状态',
    width: '90px',
    slots: {
      default: (data: any) =>
        data.row.excellent_state ? (
          <ElTag style={{ backgroundColor: '#67c23a', borderColor: '#67c23a', color: '#fff' }}>
            优秀
          </ElTag>
        ) : (
          <ElTag type="info">未优秀</ElTag>
        )
    }
  },
  { field: 'teacher_comment', label: '老师评语', minWidth: '170px' }
])

const loadData = async () => {
  const res = await getPeClassAnalysisApi({
    ...searchParams.value,
    stage_type: examTypeTab.value
  }).catch(() => null)
  if (!res) return
  const data = res.data || {}
  if (data.kpi) {
    kpiData.value = Object.assign(kpiData.value, data.kpi)
  }
  if (data.history_avg) {
    historyAvgTrendOptions.xAxis.data = data.history_avg.batches || []
    const avgSeries = data.history_avg.series || []
    historyAvgTrendOptions.legend.data = avgSeries.map((s: any) => s.name)
    historyAvgTrendOptions.series = avgSeries.map((s: any) => ({
      name: s.name,
      type: 'line',
      smooth: true,
      data: s.values || []
    }))
  }
  if (data.history_item_bar) {
    historyItemBarOptions.xAxis.data = data.history_item_bar.batches || []
    historyItemBarOptions.series[0].data = data.history_item_bar.rope_avg || []
    historyItemBarOptions.series[1].data = data.history_item_bar.jump_avg || []
    historyItemBarOptions.series[2].data = data.history_item_bar.ball_avg || []
    const threshold = data.history_item_bar.threshold || {}
    historyItemBarOptions.series[2].markLine.data = [
      { yAxis: threshold.pass || 10, name: '及格线', lineStyle: { color: '#E6A23C' } },
      { yAxis: threshold.excellent || 14, name: '优秀线', lineStyle: { color: '#67C23A' } },
      { yAxis: threshold.full || 20, name: '满分线', lineStyle: { color: '#000000' } }
    ]
  }
  if (Array.isArray(data.rank_list)) {
    rankData.value = data.rank_list
  }
}

onMounted(() => {
  loadData()
})

watch(examTypeTab, () => {
  loadData()
})
</script>

<template>
  <ContentWrap>
    <ElTabs v-model="examTypeTab" class="mb-10px">
      <ElTabPane label="初中" name="mid" />
      <ElTabPane label="高中" name="high" />
    </ElTabs>

    <Search
      :schema="searchSchema"
      @search="setSearchParams"
      @reset="setSearchParams"
      class="mb-10px"
    />

    <ElCard shadow="never" class="main-card">
      <template #header>{{ panelTitle }}</template>
      <ElRow :gutter="20" class="mb-20px">
        <ElCol :span="6">
          <ElCard shadow="hover" class="text-center">
            <div class="text-gray-400 text-14px mb-10px">班级平均分</div>
            <div class="text-24px font-bold text-blue-500">{{ kpiData.avg_score }}</div>
          </ElCard>
        </ElCol>
        <ElCol :span="6">
          <ElCard shadow="hover" class="text-center">
            <div class="text-gray-400 text-14px mb-10px">及格率</div>
            <div class="text-24px font-bold text-pass-yellow">{{ kpiData.pass_rate }}%</div>
          </ElCard>
        </ElCol>
        <ElCol :span="6">
          <ElCard shadow="hover" class="text-center">
            <div class="text-gray-400 text-14px mb-10px">优秀率</div>
            <div class="text-24px font-bold text-excellent-green"
              >{{ kpiData.excellent_rate }}%</div
            >
          </ElCard>
        </ElCol>
        <ElCol :span="6">
          <ElCard shadow="hover" class="text-center">
            <div class="text-gray-400 text-14px mb-10px">满分率</div>
            <div class="text-24px font-bold text-full-black">{{ kpiData.full_rate }}%</div>
          </ElCard>
        </ElCol>
      </ElRow>

      <ElRow :gutter="20" class="mb-20px">
        <ElCol :span="12">
          <ElCard shadow="never" title="批次均分趋势">
            <Echart :options="historyAvgTrendOptions" height="340px" />
          </ElCard>
        </ElCol>
        <ElCol :span="12">
          <ElCard shadow="never" title="批次项目均分">
            <Echart :options="historyItemBarOptions" height="340px" />
          </ElCard>
        </ElCol>
      </ElRow>

      <div class="mb-8px text-15px font-600">班级学生排名列表</div>
      <Table :columns="tableColumns" :data="rankData" :pagination="false" :border="false" />
    </ElCard>
  </ContentWrap>
</template>

<style scoped lang="less">
:deep(.el-card__header) {
  text-align: center;
  font-size: 15px;
  font-weight: 600;
}

:deep(.main-card > .el-card__header) {
  font-size: 20px;
  font-weight: 700;
}

.text-pass-yellow {
  color: #e6a23c;
}

.text-fail-red {
  color: #f56c6c;
}

.text-excellent-green {
  color: #67c23a;
}

.text-full-black {
  color: #000000;
}

.text-blue-500 {
  color: #409eff;
}
</style>
