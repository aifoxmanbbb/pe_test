<script setup lang="tsx">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import { ElRow, ElCol, ElCard, ElTabs, ElTabPane } from 'element-plus'
import { Echart } from '@/components/Echart'
import { Table, TableColumn } from '@/components/Table'
import { getFitnessGradeAnalysisApi } from '@/api/vadmin/fitness'

defineOptions({
  name: 'FitnessGradeAnalysis'
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

const panelTitle = computed(() => '某批次-某学校-年级 体质测试情况分析')

const kpiData = ref({
  class_count: 12,
  student_count: 638,
  item_records: 5104,
  fail_item_records: 512,
  full_item_records: 304
})

const classItemAvgOptions = reactive({
  title: { text: '各班单项均分对比', textStyle: { fontSize: 15, fontWeight: 'normal' } },
  tooltip: { trigger: 'axis' },
  legend: { data: ['BMI均分', '肺活量均分', '50米均分', '坐位体前屈均分'] },
  xAxis: { type: 'category', data: ['1班', '2班', '3班', '4班', '5班'] },
  yAxis: { type: 'value', max: 100 },
  series: [
    { name: 'BMI均分', type: 'bar', data: [76, 70, 74, 68, 72] },
    { name: '肺活量均分', type: 'bar', data: [84, 78, 81, 75, 79] },
    { name: '50米均分', type: 'bar', data: [72, 66, 70, 63, 68] },
    { name: '坐位体前屈均分', type: 'bar', data: [78, 72, 76, 69, 74] }
  ]
})

const classItemRateOptions = reactive({
  title: { text: '各班单项率对比(50米)', textStyle: { fontSize: 15, fontWeight: 'normal' } },
  tooltip: { trigger: 'axis' },
  legend: { data: ['及格率', '优秀率', '满分率'] },
  xAxis: { type: 'category', data: ['1班', '2班', '3班', '4班', '5班'] },
  yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
  series: [
    { name: '及格率', type: 'bar', data: [89, 81, 86, 77, 84], itemStyle: { color: '#E6A23C' } },
    {
      name: '优秀率',
      type: 'line',
      smooth: true,
      data: [28, 21, 26, 18, 24],
      itemStyle: { color: '#67C23A' }
    },
    {
      name: '满分率',
      type: 'line',
      smooth: true,
      data: [5, 2, 4, 1, 3],
      itemStyle: { color: '#000000' }
    }
  ]
})

const classHistoryItemTrendOptions = reactive({
  title: {
    text: '各班批次单项均分趋势(肺活量)',
    textStyle: { fontSize: 15, fontWeight: 'normal' }
  },
  tooltip: { trigger: 'axis' },
  legend: { data: ['1班', '2班', '3班', '4班'] },
  xAxis: { type: 'category', data: ['2025春', '2025秋', '2026春', '2026秋'] },
  yAxis: { type: 'value', max: 100 },
  series: [
    { name: '1班', type: 'line', smooth: true, data: [76, 80, 84, 86] },
    { name: '2班', type: 'line', smooth: true, data: [71, 74, 78, 80] },
    { name: '3班', type: 'line', smooth: true, data: [73, 77, 81, 83] },
    { name: '4班', type: 'line', smooth: true, data: [69, 72, 75, 78] }
  ]
})

const classTableData = ref([
  {
    class_name: '1班',
    bmi_score: '22.1',
    bmi_point: 76,
    bmi_rate: '及格90% / 优秀33% / 满分8%',
    lung_score: '4200ml',
    lung_point: 84,
    lung_rate: '及格95% / 优秀42% / 满分12%',
    sprint_score: '7.8秒',
    sprint_point: 72,
    sprint_rate: '及格89% / 优秀28% / 满分5%'
  },
  {
    class_name: '2班',
    bmi_score: '22.8',
    bmi_point: 70,
    bmi_rate: '及格83% / 优秀26% / 满分5%',
    lung_score: '3950ml',
    lung_point: 78,
    lung_rate: '及格91% / 优秀36% / 满分9%',
    sprint_score: '8.3秒',
    sprint_point: 66,
    sprint_rate: '及格81% / 优秀21% / 满分2%'
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
    field: 'bmi_item',
    label: 'BMI(均成绩/均分)',
    minWidth: '140px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.bmi_score, data.row.bmi_point)
    }
  },
  { field: 'bmi_rate', label: 'BMI情况', minWidth: '180px' },
  {
    field: 'lung_item',
    label: '肺活量(均成绩/均分)',
    minWidth: '150px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.lung_score, data.row.lung_point)
    }
  },
  { field: 'lung_rate', label: '肺活量情况', minWidth: '180px' },
  {
    field: 'sprint_item',
    label: '50米(均成绩/均分)',
    minWidth: '140px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.sprint_score, data.row.sprint_point)
    }
  },
  { field: 'sprint_rate', label: '50米情况', minWidth: '180px' }
])

const loadData = async () => {
  const res = await getFitnessGradeAnalysisApi({
    ...searchParams.value,
    stage_type: stageTab.value
  }).catch(() => null)
  if (!res) return
  const data = res.data || {}
  if (data.kpi) {
    kpiData.value = Object.assign(kpiData.value, data.kpi)
  }
  if (data.class_item_avg) {
    classItemAvgOptions.xAxis.data = data.class_item_avg.classes || []
    const avgSeries = data.class_item_avg.series || []
    classItemAvgOptions.legend.data = avgSeries.map((s: any) => s.name)
    classItemAvgOptions.series = avgSeries.map((s: any) => ({
      name: s.name,
      type: 'bar',
      data: s.values || []
    }))
  }
  if (data.class_item_rate) {
    classItemRateOptions.xAxis.data = data.class_item_rate.classes || []
    classItemRateOptions.series[0].data = data.class_item_rate.pass_rate || []
    classItemRateOptions.series[1].data = data.class_item_rate.excellent_rate || []
    classItemRateOptions.series[2].data = data.class_item_rate.full_rate || []
  }
  if (data.class_item_history) {
    classHistoryItemTrendOptions.xAxis.data = data.class_item_history.batches || []
    const historySeries = data.class_item_history.series || []
    classHistoryItemTrendOptions.legend.data = historySeries.map((s: any) => s.name)
    classHistoryItemTrendOptions.series = historySeries.map((s: any) => ({
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
            <div class="text-gray-400 text-14px mb-10px">班级数</div>
            <div class="text-24px font-bold text-blue-500">{{ kpiData.class_count }}</div>
          </ElCard>
        </ElCol>
        <ElCol :span="4">
          <ElCard shadow="hover" class="text-center">
            <div class="text-gray-400 text-14px mb-10px">学生人数</div>
            <div class="text-24px font-bold">{{ kpiData.student_count }}</div>
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
          <ElCard shadow="never" title="各班单项均分对比">
            <Echart :options="classItemAvgOptions" height="330px" />
          </ElCard>
        </ElCol>
        <ElCol :span="12">
          <ElCard shadow="never" title="各班单项率对比(50米)">
            <Echart :options="classItemRateOptions" height="330px" />
          </ElCard>
        </ElCol>
      </ElRow>

      <ElRow :gutter="20" class="mb-20px">
        <ElCol :span="24">
          <ElCard shadow="never" title="各班批次单项均分趋势(肺活量)">
            <Echart :options="classHistoryItemTrendOptions" height="320px" />
          </ElCard>
        </ElCol>
      </ElRow>

      <div class="mb-8px text-15px font-600">班级体测统计列表</div>
      <Table :columns="tableColumns" :data="classTableData" :pagination="false" :border="false" />

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
