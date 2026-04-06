<script setup lang="tsx">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import { ElRow, ElCol, ElCard, ElTabs, ElTabPane } from 'element-plus'
import { Echart } from '@/components/Echart'
import { Table, TableColumn } from '@/components/Table'
import { getFitnessOverviewApi } from '@/api/vadmin/fitness'

defineOptions({
  name: 'FitnessOverview'
})

const stageTab = ref('mid')

const searchSchema = reactive<FormSchema[]>([
  {
    field: 'batch_id',
    label: '批次',
    component: 'Select',
    componentProps: {
      placeholder: '请选择批次',
      options: [
        { label: '2026春季体测', value: 1 },
        { label: '2025秋季体测', value: 2 }
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
  return '某批次-某学校/所有学校 体质测试情况分析'
})

const kpiData = ref({
  total_students: 1520,
  item_count: 8,
  item_records: 12160,
  fail_item_records: 1320,
  full_item_records: 760
})

const formatItemAxisLabel = (value: string) => {
  if (!value) return ''
  if (value.includes('\n') || value.length <= 3) return value
  return value.match(/.{1,2}/g)?.join('\n') || value
}

const itemAvgOptions = reactive({
  title: { text: '单项平均分对比', textStyle: { fontSize: 15, fontWeight: 'normal' } },
  tooltip: { trigger: 'axis' },
  legend: { data: ['平均分', '及格线', '优秀线', '满分线'] },
  grid: { left: '3%', right: '4%', bottom: '23%', containLabel: true },
  xAxis: {
    type: 'category',
    data: ['BMI', '肺活量', '50米', '坐位体前屈', '跳绳', '跳远', '力量项', '耐力跑'],
    axisLabel: {
      interval: 0,
      rotate: 20,
      lineHeight: 16,
      formatter: formatItemAxisLabel
    }
  },
  yAxis: { type: 'value', max: 100 },
  series: [
    {
      name: '平均分',
      type: 'bar',
      data: [78, 82, 71, 76, 84, 79, 74, 73],
      itemStyle: { color: '#409eff' },
      label: {
        show: true,
        position: 'top',
        formatter: '{c}分'
      },
      markLine: {
        symbol: 'none',
        data: [
          { yAxis: 60, name: '及格线', lineStyle: { color: '#E6A23C' } },
          { yAxis: 80, name: '优秀线', lineStyle: { color: '#67C23A' } },
          { yAxis: 100, name: '满分线', lineStyle: { color: '#000000' } }
        ]
      }
    }
  ]
})

const itemRateOptions = reactive({
  title: { text: '单项及格/优秀/满分率对比', textStyle: { fontSize: 15, fontWeight: 'normal' } },
  tooltip: { trigger: 'axis' },
  legend: { data: ['及格率', '优秀率', '满分率'] },
  grid: { left: '3%', right: '4%', bottom: '23%', containLabel: true },
  xAxis: {
    type: 'category',
    data: ['BMI', '肺活量', '50米', '坐位体前屈', '跳绳', '跳远', '力量项', '耐力跑'],
    axisLabel: {
      interval: 0,
      rotate: 20,
      lineHeight: 16,
      formatter: formatItemAxisLabel
    }
  },
  yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
  series: [
    {
      name: '及格率',
      type: 'bar',
      data: [91, 94, 82, 88, 96, 90, 86, 84],
      itemStyle: { color: '#E6A23C' },
      label: { show: true, position: 'top', formatter: '{c}%' }
    },
    {
      name: '优秀率',
      type: 'line',
      data: [35, 41, 24, 33, 48, 36, 29, 27],
      smooth: true,
      itemStyle: { color: '#67C23A' }
    },
    {
      name: '满分率',
      type: 'line',
      data: [8, 12, 3, 6, 15, 9, 5, 4],
      smooth: true,
      itemStyle: { color: '#000000' }
    }
  ]
})

const itemTrendOptions = reactive({
  title: { text: '重点单项批次趋势', textStyle: { fontSize: 15, fontWeight: 'normal' } },
  tooltip: { trigger: 'axis' },
  legend: { data: ['肺活量均分', '50米均分', '跳绳均分'] },
  xAxis: { type: 'category', data: ['2025春', '2025秋', '2026春'] },
  yAxis: { type: 'value', max: 100 },
  series: [
    {
      name: '肺活量均分',
      type: 'line',
      smooth: true,
      data: [76, 79, 82],
      itemStyle: { color: '#67C23A' }
    },
    {
      name: '50米均分',
      type: 'line',
      smooth: true,
      data: [66, 69, 71],
      itemStyle: { color: '#409eff' }
    },
    {
      name: '跳绳均分',
      type: 'line',
      smooth: true,
      data: [80, 82, 84],
      itemStyle: { color: '#E6A23C' }
    }
  ]
})

const classData = ref([
  {
    school_name: '第一中学',
    class_name: '3年1班',
    bmi_score: '22.1',
    bmi_point: 79,
    bmi_rate: '及格91% / 优秀34% / 满分7%',
    lung_score: '4200ml',
    lung_point: 83,
    lung_rate: '及格95% / 优秀43% / 满分12%',
    sprint_score: '7.8秒',
    sprint_point: 72,
    sprint_rate: '及格83% / 优秀24% / 满分3%'
  },
  {
    school_name: '第一中学',
    class_name: '3年2班',
    bmi_score: '22.4',
    bmi_point: 76,
    bmi_rate: '及格88% / 优秀31% / 满分6%',
    lung_score: '4050ml',
    lung_point: 80,
    lung_rate: '及格93% / 优秀38% / 满分10%',
    sprint_score: '8.0秒',
    sprint_point: 70,
    sprint_rate: '及格80% / 优秀21% / 满分2%'
  },
  {
    school_name: '实验中学',
    class_name: '3年1班',
    bmi_score: '22.0',
    bmi_point: 80,
    bmi_rate: '及格90% / 优秀33% / 满分8%',
    lung_score: '4180ml',
    lung_point: 82,
    lung_rate: '及格94% / 优秀40% / 满分11%',
    sprint_score: '7.7秒',
    sprint_point: 73,
    sprint_rate: '及格82% / 优秀23% / 满分3%'
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
    minWidth: '150px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.sprint_score, data.row.sprint_point)
    }
  },
  { field: 'sprint_rate', label: '50米情况', minWidth: '180px' }
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
  const res = await getFitnessOverviewApi({
    ...searchParams.value,
    stage_type: stageTab.value
  }).catch(() => null)
  if (!res) return
  const data = res.data || {}
  if (data.kpi) {
    kpiData.value = Object.assign(kpiData.value, data.kpi)
  }
  if (data.item_avg) {
    itemAvgOptions.xAxis.data = data.item_avg.items || []
    itemAvgOptions.series[0].data = data.item_avg.values || []
  }
  if (data.item_rate) {
    itemRateOptions.xAxis.data = data.item_rate.items || []
    itemRateOptions.series[0].data = data.item_rate.pass_rate || []
    itemRateOptions.series[1].data = data.item_rate.excellent_rate || []
    itemRateOptions.series[2].data = data.item_rate.full_rate || []
  }
  if (data.item_trend) {
    itemTrendOptions.xAxis.data = data.item_trend.batches || []
    const trendSeries = data.item_trend.series || []
    itemTrendOptions.legend.data = trendSeries.map((s: any) => s.name)
    itemTrendOptions.series = trendSeries.map((s: any, idx: number) => ({
      name: s.name,
      type: 'line',
      smooth: true,
      data: s.values || [],
      itemStyle: {
        color: idx === 0 ? '#67C23A' : idx === 1 ? '#409eff' : '#E6A23C'
      }
    }))
  }
  if (data.class_list) {
    classData.value = data.class_list
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
            <div class="text-gray-400 text-14px mb-10px">项目数</div>
            <div class="text-24px font-bold text-blue-500">{{ kpiData.item_count }}</div>
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
        <ElCol :span="14">
          <ElCard shadow="never" title="单项平均分对比">
            <Echart :options="itemAvgOptions" height="350px" />
          </ElCard>
        </ElCol>
        <ElCol :span="10">
          <ElCard shadow="never" title="单项及格/优秀/满分率对比">
            <Echart :options="itemRateOptions" height="350px" />
          </ElCard>
        </ElCol>
      </ElRow>

      <ElRow :gutter="20" class="mb-20px">
        <ElCol :span="24">
          <ElCard shadow="never" title="重点单项批次趋势">
            <Echart :options="itemTrendOptions" height="320px" />
          </ElCard>
        </ElCol>
      </ElRow>

      <div class="mb-8px text-15px font-600">学校分组班级体测统计列表</div>
      <Table
        :columns="tableColumns"
        :data="classData"
        :pagination="false"
        :border="false"
        :span-method="tableSpanMethod"
      />

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
