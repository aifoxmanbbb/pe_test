<script setup lang="tsx">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import { ElRow, ElCol, ElCard, ElTabs, ElTabPane } from 'element-plus'
import { Echart } from '@/components/Echart'
import { Table, TableColumn } from '@/components/Table'
import { getFitnessClassAnalysisApi } from '@/api/vadmin/fitness'

defineOptions({
  name: 'FitnessClassAnalysis'
})

const stageTab = ref('mid')

const searchSchema = reactive<FormSchema[]>([
  {
    field: 'batch_id',
    label: '批次',
    component: 'Select',
    componentProps: {
      placeholder: '请选择批次',
      options: [{ label: '2026春季体测', value: 1 }]
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

const panelTitle = computed(() => '某批次-某学校-年级-班级 体质测试情况分析')

const kpiData = ref({
  student_count: 53,
  item_count: 8,
  item_records: 424,
  fail_item_records: 39,
  full_item_records: 21
})

const formatItemAxisLabel = (value: string) => {
  if (!value) return ''
  if (value.includes('\n') || value.length <= 3) return value
  return value.match(/.{1,2}/g)?.join('\n') || value
}

const historyAvgTrendOptions = reactive({
  title: { text: '批次单项均分趋势', textStyle: { fontSize: 15, fontWeight: 'normal' } },
  tooltip: { trigger: 'axis' },
  legend: { data: ['BMI均分', '肺活量均分', '50米均分', '坐位体前屈均分'] },
  xAxis: { type: 'category', data: ['2025春', '2025秋', '2026春', '2026秋'] },
  yAxis: { type: 'value', max: 100 },
  series: [
    { name: 'BMI均分', type: 'line', smooth: true, data: [68, 72, 75, 77] },
    { name: '肺活量均分', type: 'line', smooth: true, data: [75, 79, 82, 84] },
    { name: '50米均分', type: 'line', smooth: true, data: [61, 65, 70, 72] },
    { name: '坐位体前屈均分', type: 'line', smooth: true, data: [70, 73, 76, 78] }
  ]
})

const historyItemRateOptions = reactive({
  title: { text: '当前批次单项率', textStyle: { fontSize: 15, fontWeight: 'normal' } },
  tooltip: { trigger: 'axis' },
  legend: { data: ['及格率', '优秀率', '满分率'] },
  grid: { left: '3%', right: '4%', bottom: '23%', containLabel: true },
  xAxis: {
    type: 'category',
    data: ['BMI', '肺活量', '50米', '坐位体前屈', '跳绳'],
    axisLabel: { interval: 0, rotate: 20, lineHeight: 16, formatter: formatItemAxisLabel }
  },
  yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
  series: [
    {
      name: '及格率',
      type: 'bar',
      data: [91, 95, 83, 88, 96],
      itemStyle: { color: '#E6A23C' },
      label: { show: true, position: 'top', formatter: '{c}%' }
    },
    {
      name: '优秀率',
      type: 'line',
      smooth: true,
      data: [34, 43, 24, 32, 47],
      itemStyle: { color: '#67C23A' }
    },
    {
      name: '满分率',
      type: 'line',
      smooth: true,
      data: [7, 12, 3, 5, 14],
      itemStyle: { color: '#000000' }
    }
  ]
})

const rankData = ref([
  {
    rank: 1,
    student_name: '张三',
    gender: '男',
    student_no: '2023030101',
    bmi_score: '22.0',
    bmi_point: 76,
    lung_score: '4300ml',
    lung_point: 88,
    sprint_score: '7.7秒',
    sprint_point: 71,
    sit_score: '18.5cm',
    sit_point: 80,
    rope_score: '182次',
    rope_point: 86,
    teacher_comment: '肺活量与柔韧项优势明显。'
  },
  {
    rank: 2,
    student_name: '李四',
    gender: '女',
    student_no: '2023030102',
    bmi_score: '21.4',
    bmi_point: 80,
    lung_score: '3600ml',
    lung_point: 81,
    sprint_score: '8.2秒',
    sprint_point: 66,
    sit_score: '19.4cm',
    sit_point: 84,
    rope_score: '176次',
    rope_point: 82,
    teacher_comment: '50米偏弱，建议速度专项。'
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
    field: 'bmi_item',
    label: 'BMI(成绩/分)',
    minWidth: '120px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.bmi_score, data.row.bmi_point)
    }
  },
  {
    field: 'lung_item',
    label: '肺活量(成绩/分)',
    minWidth: '130px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.lung_score, data.row.lung_point)
    }
  },
  {
    field: 'sprint_item',
    label: '50米(成绩/分)',
    minWidth: '120px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.sprint_score, data.row.sprint_point)
    }
  },
  {
    field: 'sit_item',
    label: '坐位体前屈(成绩/分)',
    minWidth: '150px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.sit_score, data.row.sit_point)
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
  { field: 'teacher_comment', label: '老师评语', minWidth: '170px' }
])

const loadData = async () => {
  const res = await getFitnessClassAnalysisApi({
    ...searchParams.value,
    stage_type: stageTab.value
  }).catch(() => null)
  if (!res) return
  const data = res.data || {}
  if (data.kpi) {
    kpiData.value = Object.assign(kpiData.value, data.kpi)
  }
  if (data.history_item_avg) {
    historyAvgTrendOptions.xAxis.data = data.history_item_avg.batches || []
    const avgSeries = data.history_item_avg.series || []
    historyAvgTrendOptions.legend.data = avgSeries.map((s: any) => s.name)
    historyAvgTrendOptions.series = avgSeries.map((s: any) => ({
      name: s.name,
      type: 'line',
      smooth: true,
      data: s.values || []
    }))
  }
  if (data.current_item_rate) {
    historyItemRateOptions.xAxis.data = data.current_item_rate.items || []
    historyItemRateOptions.series[0].data = data.current_item_rate.pass_rate || []
    historyItemRateOptions.series[1].data = data.current_item_rate.excellent_rate || []
    historyItemRateOptions.series[2].data = data.current_item_rate.full_rate || []
  }
  if (Array.isArray(data.rank_list)) {
    rankData.value = data.rank_list
  }
}

onMounted(() => {
  loadData()
})

watch(stageTab, () => {
  loadData()
})
</script>

<template>
  <ContentWrap>
    <ElTabs v-model="stageTab" class="mb-10px">
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
        <ElCol :span="4">
          <ElCard shadow="hover" class="text-center">
            <div class="text-gray-400 text-14px mb-10px">学生人数</div>
            <div class="text-24px font-bold text-blue-500">{{ kpiData.student_count }}</div>
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="hover" class="text-center">
            <div class="text-gray-400 text-14px mb-10px">项目数</div>
            <div class="text-24px font-bold">{{ kpiData.item_count }}</div>
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="hover" class="text-center">
            <div class="text-gray-400 text-14px mb-10px">单项记录数</div>
            <div class="text-24px font-bold">{{ kpiData.item_records }}</div>
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="hover" class="text-center">
            <div class="text-gray-400 text-14px mb-10px">不及格单项记录</div>
            <div class="text-24px font-bold text-fail-red">{{ kpiData.fail_item_records }}</div>
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="hover" class="text-center">
            <div class="text-gray-400 text-14px mb-10px">满分单项记录</div>
            <div class="text-24px font-bold text-full-black">{{ kpiData.full_item_records }}</div>
          </ElCard>
        </ElCol>
      </ElRow>

      <ElRow :gutter="20" class="mb-20px">
        <ElCol :span="12">
          <ElCard shadow="never" title="批次单项均分趋势">
            <Echart :options="historyAvgTrendOptions" height="340px" />
          </ElCard>
        </ElCol>
        <ElCol :span="12">
          <ElCard shadow="never" title="当前批次单项率">
            <Echart :options="historyItemRateOptions" height="340px" />
          </ElCard>
        </ElCol>
      </ElRow>

      <div class="mb-8px text-15px font-600">班级学生排名列表</div>
      <Table :columns="tableColumns" :data="rankData" :pagination="false" :border="false" />

      <div class="text-12px text-gray-500 mt-8px">当前筛选：{{ searchParams }}</div>
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
