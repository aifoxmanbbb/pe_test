<script setup lang="tsx">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import { ElRow, ElCol, ElCard, ElTabs, ElTabPane } from 'element-plus'
import { Echart } from '@/components/Echart'
import { Table, TableColumn } from '@/components/Table'
import { getPeGradeAnalysisApi } from '@/api/vadmin/pe'

defineOptions({
  name: 'GradeAnalysis'
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
      options: [
        { label: '初三', value: 3 },
        { label: '高三', value: 6 }
      ]
    }
  }
])

const searchParams = ref<Record<string, any>>({})
const setSearchParams = (data: Record<string, any>) => {
  searchParams.value = data
  loadData()
}

const panelTitle = computed(() => '某批次-某学校-年级 体育项目情况分析')

const kpiData = ref({
  avg_score: 39.7,
  pass_rate: 82.4,
  excellent_rate: 26.8,
  full_rate: 4.7
})

const classAvgCompareOptions = reactive({
  title: { text: '各班平均分对比', textStyle: { fontSize: 15, fontWeight: 'normal' } },
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: ['1班', '2班', '3班', '4班', '5班'] },
  yAxis: { type: 'value', max: 50 },
  series: [
    {
      name: '班均分',
      type: 'bar',
      data: [41.2, 38.7, 40.3, 36.9, 39.6],
      itemStyle: { color: '#409eff' },
      label: { show: true, position: 'top', formatter: '{c}分' },
      markLine: {
        symbol: 'none',
        data: [
          { yAxis: 30, name: '及格线', lineStyle: { color: '#E6A23C' } },
          { yAxis: 40, name: '优秀线', lineStyle: { color: '#67C23A' } },
          { yAxis: 50, name: '满分线', lineStyle: { color: '#000000' } }
        ]
      }
    }
  ]
})

const classRateOptions = reactive({
  title: { text: '班级分层率对比', textStyle: { fontSize: 15, fontWeight: 'normal' } },
  tooltip: { trigger: 'axis' },
  legend: { data: ['及格率', '优秀率', '满分率'] },
  xAxis: { type: 'category', data: ['1班', '2班', '3班', '4班', '5班'] },
  yAxis: { type: 'value', axisLabel: { formatter: '{value}%' }, max: 100 },
  series: [
    {
      name: '及格率',
      type: 'line',
      smooth: true,
      data: [88, 80, 84, 75, 82],
      itemStyle: { color: '#E6A23C' }
    },
    {
      name: '优秀率',
      type: 'line',
      smooth: true,
      data: [30, 23, 29, 20, 25],
      itemStyle: { color: '#67C23A' }
    },
    {
      name: '满分率',
      type: 'line',
      smooth: true,
      data: [6, 4, 5, 3, 4],
      itemStyle: { color: '#000000' }
    }
  ]
})

const classItemCompareOptions = reactive({
  title: { text: '班级项目均值对比', textStyle: { fontSize: 15, fontWeight: 'normal' } },
  tooltip: { trigger: 'axis' },
  legend: {
    data: [
      '门槛项平均分',
      '跳绳平均分',
      '跳远平均分',
      '实心球平均分',
      '门槛项平均成绩',
      '跳绳平均成绩',
      '跳远平均成绩',
      '实心球平均成绩'
    ]
  },
  xAxis: { type: 'category', data: ['1班', '2班', '3班', '4班'] },
  yAxis: [
    { type: 'value', name: '平均分', max: 20 },
    { type: 'value', name: '平均成绩指数', max: 220 }
  ],
  series: [
    {
      name: '门槛项平均分',
      type: 'bar',
      data: [11.1, 10.8, 11.0, 10.5],
      label: { show: true, position: 'top' }
    },
    {
      name: '跳绳平均分',
      type: 'bar',
      data: [17.2, 16.4, 16.8, 15.9],
      label: { show: true, position: 'top' }
    },
    {
      name: '跳远平均分',
      type: 'bar',
      data: [11.3, 10.5, 10.9, 10.1],
      label: { show: true, position: 'top' }
    },
    {
      name: '实心球平均分',
      type: 'bar',
      data: [10.6, 9.8, 10.1, 9.4],
      label: { show: true, position: 'top' }
    },
    {
      name: '门槛项平均成绩',
      type: 'line',
      yAxisIndex: 1,
      data: [240, 245, 242, 248],
      smooth: true
    },
    { name: '跳绳平均成绩', type: 'line', yAxisIndex: 1, data: [176, 172, 174, 168], smooth: true },
    { name: '跳远平均成绩', type: 'line', yAxisIndex: 1, data: [224, 219, 221, 216], smooth: true },
    { name: '实心球平均成绩', type: 'line', yAxisIndex: 1, data: [84, 79, 81, 76], smooth: true }
  ]
})

const classHistoryTrendOptions = reactive({
  title: { text: '班级批次均分趋势', textStyle: { fontSize: 15, fontWeight: 'normal' } },
  tooltip: { trigger: 'axis' },
  legend: { data: ['1班', '2班', '3班', '4班'] },
  xAxis: { type: 'category', data: ['2025春', '2025秋', '2026春', '2026秋'] },
  yAxis: { type: 'value', max: 50 },
  series: [
    { name: '1班', type: 'line', smooth: true, data: [38.2, 39.1, 41.2, 42.1] },
    { name: '2班', type: 'line', smooth: true, data: [36.7, 37.8, 38.7, 39.5] },
    { name: '3班', type: 'line', smooth: true, data: [37.5, 38.9, 40.3, 40.8] },
    { name: '4班', type: 'line', smooth: true, data: [35.9, 36.2, 36.9, 37.4] }
  ]
})

const classTableData = ref([
  {
    class_name: '1班',
    gate_score: '3分56秒',
    gate_point: 11.1,
    rope_score: '176次',
    rope_point: 17.2,
    jump_score: '2.24m',
    jump_point: 11.3,
    ball_score: '8.4m',
    ball_point: 10.6,
    avg_score: 41.2,
    pass_rate: 88,
    excellent_rate: 30,
    full_rate: 6
  },
  {
    class_name: '2班',
    gate_score: '4分01秒',
    gate_point: 10.8,
    rope_score: '172次',
    rope_point: 16.4,
    jump_score: '2.19m',
    jump_point: 10.5,
    ball_score: '7.9m',
    ball_point: 9.8,
    avg_score: 38.7,
    pass_rate: 80,
    excellent_rate: 23,
    full_rate: 4
  }
])

const renderScorePoint = (score: string, point: number) => (
  <div class="leading-5">
    <div>{score}</div>
    <div class="text-12px text-gray-500">{point}分</div>
  </div>
)

const tableColumns = reactive<TableColumn[]>([
  { field: 'class_name', label: '班级', width: '80px' },
  {
    field: 'gate_item',
    label: '门槛项(均成绩/均分)',
    minWidth: '140px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.gate_score, data.row.gate_point)
    }
  },
  {
    field: 'rope_item',
    label: '跳绳(均成绩/均分)',
    minWidth: '140px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.rope_score, data.row.rope_point)
    }
  },
  {
    field: 'jump_item',
    label: '跳远(均成绩/均分)',
    minWidth: '140px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.jump_score, data.row.jump_point)
    }
  },
  {
    field: 'ball_item',
    label: '实心球(均成绩/均分)',
    minWidth: '140px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.ball_score, data.row.ball_point)
    }
  },
  { field: 'avg_score', label: '班均分', width: '90px' },
  {
    field: 'pass_rate',
    label: '及格率',
    width: '80px',
    slots: {
      default: (data: any) => <span class="text-pass-yellow">{data.row.pass_rate}%</span>
    }
  },
  {
    field: 'excellent_rate',
    label: '优秀率',
    width: '80px',
    slots: {
      default: (data: any) => <span class="text-excellent-green">{data.row.excellent_rate}%</span>
    }
  },
  {
    field: 'full_rate',
    label: '满分率',
    width: '80px',
    slots: {
      default: (data: any) => <span class="text-full-black">{data.row.full_rate}%</span>
    }
  }
])

const loadData = async () => {
  const res = await getPeGradeAnalysisApi({
    ...searchParams.value,
    stage_type: examTypeTab.value
  }).catch(() => null)
  if (!res) return
  const data = res.data || {}
  if (data.kpi) {
    kpiData.value = Object.assign(kpiData.value, data.kpi)
  }
  if (data.class_avg_compare) {
    classAvgCompareOptions.xAxis.data = data.class_avg_compare.classes || []
    classAvgCompareOptions.series[0].data = data.class_avg_compare.avg_score || []
    const threshold = data.class_avg_compare.threshold || {}
    classAvgCompareOptions.series[0].markLine.data = [
      { yAxis: threshold.pass || 30, name: '及格线', lineStyle: { color: '#E6A23C' } },
      { yAxis: threshold.excellent || 40, name: '优秀线', lineStyle: { color: '#67C23A' } },
      { yAxis: threshold.full || 50, name: '满分线', lineStyle: { color: '#000000' } }
    ]
  }
  if (data.class_rate) {
    classRateOptions.xAxis.data = data.class_rate.classes || []
    classRateOptions.series[0].data = data.class_rate.pass_rate || []
    classRateOptions.series[1].data = data.class_rate.excellent_rate || []
    classRateOptions.series[2].data = data.class_rate.full_rate || []
  }
  if (data.class_item_compare) {
    classItemCompareOptions.xAxis.data = data.class_item_compare.classes || []
    classItemCompareOptions.series[0].data = data.class_item_compare.gate_point_avg || []
    classItemCompareOptions.series[1].data = data.class_item_compare.rope_point_avg || []
    classItemCompareOptions.series[2].data = data.class_item_compare.jump_point_avg || []
    classItemCompareOptions.series[3].data = data.class_item_compare.ball_point_avg || []
    classItemCompareOptions.series[4].data = data.class_item_compare.gate_score_avg || []
    classItemCompareOptions.series[5].data = data.class_item_compare.rope_score_avg || []
    classItemCompareOptions.series[6].data = data.class_item_compare.jump_score_avg || []
    classItemCompareOptions.series[7].data = data.class_item_compare.ball_score_avg || []
  }
  if (data.class_history_trend) {
    classHistoryTrendOptions.xAxis.data = data.class_history_trend.batches || []
    const historySeries = data.class_history_trend.series || []
    classHistoryTrendOptions.legend.data = historySeries.map((s: any) => s.name)
    classHistoryTrendOptions.series = historySeries.map((s: any) => ({
      name: s.name,
      type: 'line',
      smooth: true,
      data: s.values || []
    }))
  }
  if (Array.isArray(data.class_list)) {
    classTableData.value = data.class_list
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
            <div class="text-gray-400 text-14px mb-10px">年级平均分</div>
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
          <ElCard shadow="never" title="各班平均分对比">
            <Echart :options="classAvgCompareOptions" height="330px" />
          </ElCard>
        </ElCol>
        <ElCol :span="12">
          <ElCard shadow="never" title="班级分层率对比">
            <Echart :options="classRateOptions" height="330px" />
          </ElCard>
        </ElCol>
      </ElRow>

      <ElRow :gutter="20" class="mb-20px">
        <ElCol :span="24">
          <ElCard shadow="never" title="班级项目均值对比">
            <Echart :options="classItemCompareOptions" height="360px" />
          </ElCard>
        </ElCol>
      </ElRow>

      <ElRow :gutter="20" class="mb-20px">
        <ElCol :span="24">
          <ElCard shadow="never" title="班级批次均分趋势">
            <Echart :options="classHistoryTrendOptions" height="320px" />
          </ElCard>
        </ElCol>
      </ElRow>

      <div class="mb-8px text-15px font-600">班级成绩列表</div>
      <Table :columns="tableColumns" :data="classTableData" :pagination="false" :border="false" />
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
