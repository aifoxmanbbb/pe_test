<script setup lang="tsx">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import { ElRow, ElCol, ElCard, ElTabs, ElTabPane } from 'element-plus'
import { Echart } from '@/components/Echart'
import { Table, TableColumn } from '@/components/Table'
import { getPeOverviewApi } from '@/api/vadmin/pe'

defineOptions({
  name: 'PEOverview'
})

const examTypeTab = ref('mid')

const searchSchema = reactive<FormSchema[]>([
  {
    field: 'batch_id',
    label: '批次',
    component: 'Select',
    componentProps: {
      placeholder: '请选择批次',
      options: [
        { label: '2026春季体考', value: 1 },
        { label: '2025秋季体考', value: 2 }
      ]
    }
  },
  {
    field: 'school_id',
    label: '学校',
    component: 'Select',
    componentProps: {
      placeholder: '管理视角可不选学校',
      clearable: true,
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

const analysisTitle = computed(() => {
  return '某批次-某学校/所有学校（管理视角可不筛选学校） 体育项目情况分析'
})

const kpiData = ref({
  total_students: 1380,
  avg_score: 42.3,
  pass_rate: 84.2,
  excellent_rate: 29.7,
  full_rate: 6.3
})

const itemAvgOptions = reactive({
  title: { text: '项目均分柱状图（含门槛项）', textStyle: { fontSize: 15, fontWeight: 'normal' } },
  tooltip: { trigger: 'axis' },
  legend: { data: ['平均分', '及格线', '优秀线', '满分线'] },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category',
    data: ['门槛项', '跳绳', '跳远', '实心球']
  },
  yAxis: { type: 'value', max: 20 },
  series: [
    {
      name: '平均分',
      type: 'bar',
      data: [11.2, 15.8, 11.6, 10.2],
      itemStyle: { color: '#409eff' },
      label: {
        show: true,
        position: 'top',
        formatter: '{c}分'
      },
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

const classRateOptions = reactive({
  title: { text: '班级分层率图', textStyle: { fontSize: 15, fontWeight: 'normal' } },
  tooltip: { trigger: 'axis' },
  legend: { data: ['及格率', '优秀率', '满分率'] },
  xAxis: { type: 'category', data: ['1班', '2班', '3班', '4班', '5班'] },
  yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
  series: [
    {
      name: '及格率',
      type: 'bar',
      data: [89, 83, 86, 78, 85],
      itemStyle: { color: '#E6A23C' },
      label: { show: true, position: 'top', formatter: '{c}%' }
    },
    {
      name: '优秀率',
      type: 'line',
      data: [31, 24, 28, 20, 26],
      smooth: true,
      itemStyle: { color: '#67C23A' }
    },
    {
      name: '满分率',
      type: 'line',
      data: [8, 5, 7, 3, 6],
      smooth: true,
      itemStyle: { color: '#000000' }
    }
  ]
})

const trendOptions = reactive({
  title: { text: '批次趋势图', textStyle: { fontSize: 15, fontWeight: 'normal' } },
  tooltip: { trigger: 'axis' },
  legend: { data: ['总均分', '及格线', '优秀线', '满分线'] },
  xAxis: { type: 'category', data: ['2025春', '2025秋', '2026春'] },
  yAxis: { type: 'value', max: 50 },
  series: [
    {
      name: '总均分',
      type: 'line',
      smooth: true,
      data: [37.8, 39.5, 42.3],
      itemStyle: { color: '#409eff' }
    },
    {
      name: '及格线',
      type: 'line',
      symbol: 'none',
      lineStyle: { type: 'dashed', color: '#E6A23C' },
      data: [30, 30, 30]
    },
    {
      name: '优秀线',
      type: 'line',
      symbol: 'none',
      lineStyle: { type: 'dashed', color: '#67C23A' },
      data: [40, 40, 40]
    },
    {
      name: '满分线',
      type: 'line',
      symbol: 'none',
      lineStyle: { type: 'dashed', color: '#000000' },
      data: [50, 50, 50]
    }
  ]
})

const classData = ref([
  {
    school_name: '第一中学',
    class_name: '3年1班',
    gate_score: '3分56秒',
    gate_point: 11.2,
    rope_score: '178次',
    rope_point: 18.1,
    jump_score: '2.23m',
    jump_point: 11.4,
    ball_score: '8.4m',
    ball_point: 10.5,
    avg_total: 42.8,
    pass_rate: 88.2,
    excellent_rate: 32.3,
    full_rate: 7.1
  },
  {
    school_name: '第一中学',
    class_name: '3年2班',
    gate_score: '4分01秒',
    gate_point: 10.7,
    rope_score: '174次',
    rope_point: 17.3,
    jump_score: '2.20m',
    jump_point: 10.9,
    ball_score: '8.1m',
    ball_point: 10.1,
    avg_total: 40.5,
    pass_rate: 83.6,
    excellent_rate: 27.2,
    full_rate: 5.4
  },
  {
    school_name: '实验中学',
    class_name: '3年1班',
    gate_score: '3分59秒',
    gate_point: 10.9,
    rope_score: '176次',
    rope_point: 17.8,
    jump_score: '2.22m',
    jump_point: 11.1,
    ball_score: '8.3m',
    ball_point: 10.2,
    avg_total: 41.9,
    pass_rate: 85.3,
    excellent_rate: 28.9,
    full_rate: 6.0
  }
])

const renderScorePoint = (score: string, point: number) => (
  <div class="leading-5">
    <div>{score}</div>
    <div class="text-12px text-gray-500">{point}分</div>
  </div>
)

const tableColumns = reactive<TableColumn[]>([
  { field: 'school_name', label: '学校', width: '120px' },
  { field: 'class_name', label: '班级', width: '100px' },
  {
    field: 'gate_item',
    label: '门槛项(成绩/分)',
    minWidth: '140px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.gate_score, data.row.gate_point)
    }
  },
  {
    field: 'rope_item',
    label: '跳绳(成绩/分)',
    minWidth: '130px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.rope_score, data.row.rope_point)
    }
  },
  {
    field: 'jump_item',
    label: '跳远(成绩/分)',
    minWidth: '130px',
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
  { field: 'avg_total', label: '班均分', width: '90px' },
  {
    field: 'pass_rate',
    label: '及格率',
    width: '90px',
    slots: {
      default: (data: any) => <span class="text-pass-yellow">{data.row.pass_rate}%</span>
    }
  },
  {
    field: 'excellent_rate',
    label: '优秀率',
    width: '90px',
    slots: {
      default: (data: any) => <span class="text-excellent-green">{data.row.excellent_rate}%</span>
    }
  },
  {
    field: 'full_rate',
    label: '满分率',
    width: '90px',
    slots: {
      default: (data: any) => <span class="text-full-black">{data.row.full_rate}%</span>
    }
  }
])

const tableSpanMethod = ({ rowIndex, column }: any) => {
  if (column.property !== 'school_name') {
    return [1, 1]
  }
  const currentSchool = classData.value[rowIndex]?.school_name
  const prevSchool = classData.value[rowIndex - 1]?.school_name
  if (currentSchool === prevSchool) {
    return [0, 0]
  }
  let spanCount = 1
  for (let i = rowIndex + 1; i < classData.value.length; i++) {
    if (classData.value[i].school_name === currentSchool) {
      spanCount += 1
    } else {
      break
    }
  }
  return [spanCount, 1]
}

const loadData = async () => {
  const res = await getPeOverviewApi({
    ...searchParams.value,
    stage_type: examTypeTab.value
  }).catch(() => null)
  if (!res) return
  const data = res.data || {}
  if (data.kpi) {
    kpiData.value = Object.assign(kpiData.value, data.kpi)
  }
  if (data.item_avg) {
    itemAvgOptions.xAxis.data = data.item_avg.items || []
    itemAvgOptions.series[0].data = data.item_avg.values || []
    const threshold = data.item_avg.threshold || {}
    itemAvgOptions.series[0].markLine.data = [
      { yAxis: threshold.pass || 10, name: '及格线', lineStyle: { color: '#E6A23C' } },
      { yAxis: threshold.excellent || 14, name: '优秀线', lineStyle: { color: '#67C23A' } },
      { yAxis: threshold.full || 20, name: '满分线', lineStyle: { color: '#000000' } }
    ]
  }
  if (data.class_rate) {
    classRateOptions.xAxis.data = data.class_rate.classes || []
    classRateOptions.series[0].data = data.class_rate.pass_rate || []
    classRateOptions.series[1].data = data.class_rate.excellent_rate || []
    classRateOptions.series[2].data = data.class_rate.full_rate || []
  }
  if (data.batch_trend) {
    trendOptions.xAxis.data = data.batch_trend.batches || []
    trendOptions.series[0].data = data.batch_trend.avg_score || []
    trendOptions.series[1].data = data.batch_trend.pass_line || []
    trendOptions.series[2].data = data.batch_trend.excellent_line || []
    trendOptions.series[3].data = data.batch_trend.full_line || []
  }
  if (Array.isArray(data.class_list)) {
    classData.value = data.class_list
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
      <template #header>{{ analysisTitle }}</template>
      <ElRow :gutter="20" class="mb-20px">
        <ElCol :span="4">
          <ElCard shadow="hover" class="text-center">
            <div class="text-gray-400 text-14px mb-10px">参考人数</div>
            <div class="text-24px font-bold">{{ kpiData.total_students }}</div>
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="hover" class="text-center">
            <div class="text-gray-400 text-14px mb-10px">平均分</div>
            <div class="text-24px font-bold text-blue-500">{{ kpiData.avg_score }}</div>
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="hover" class="text-center">
            <div class="text-gray-400 text-14px mb-10px">及格率</div>
            <div class="text-24px font-bold text-pass-yellow">{{ kpiData.pass_rate }}%</div>
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="hover" class="text-center">
            <div class="text-gray-400 text-14px mb-10px">优秀率</div>
            <div class="text-24px font-bold text-excellent-green"
              >{{ kpiData.excellent_rate }}%</div
            >
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="hover" class="text-center">
            <div class="text-gray-400 text-14px mb-10px">满分率</div>
            <div class="text-24px font-bold text-full-black">{{ kpiData.full_rate }}%</div>
          </ElCard>
        </ElCol>
      </ElRow>

      <ElRow :gutter="20" class="mb-20px">
        <ElCol :span="14">
          <ElCard shadow="never" title="项目均分柱状图">
            <Echart :options="itemAvgOptions" height="350px" />
          </ElCard>
        </ElCol>
        <ElCol :span="10">
          <ElCard shadow="never" title="班级分层率图">
            <Echart :options="classRateOptions" height="350px" />
          </ElCard>
        </ElCol>
      </ElRow>

      <ElRow :gutter="20" class="mb-20px">
        <ElCol :span="24">
          <ElCard shadow="never" title="批次趋势图">
            <Echart :options="trendOptions" height="320px" />
          </ElCard>
        </ElCol>
      </ElRow>

      <div class="mb-8px text-15px font-600">学校分组班级成绩列表</div>
      <Table
        :columns="tableColumns"
        :data="classData"
        :pagination="false"
        :border="false"
        :span-method="tableSpanMethod"
      />
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
