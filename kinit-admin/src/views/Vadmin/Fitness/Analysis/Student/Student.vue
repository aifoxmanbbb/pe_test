<script setup lang="tsx">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import {
  ElRow,
  ElCol,
  ElCard,
  ElTabs,
  ElTabPane,
  ElDescriptions,
  ElDescriptionsItem
} from 'element-plus'
import { Echart } from '@/components/Echart'
import { Table, TableColumn } from '@/components/Table'
import { Icon } from '@/components/Icon'
import { BaseButton } from '@/components/Button'
import { getFitnessStudentAnalysisApi } from '@/api/vadmin/fitness'

defineOptions({
  name: 'FitnessStudentAnalysis'
})

const stageTab = ref('mid')

const searchSchema = reactive<FormSchema[]>([
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
  },
  {
    field: 'student_id',
    label: '学生',
    component: 'Select',
    componentProps: {
      placeholder: '请输入姓名/学号/联系方式搜索学生',
      filterable: true,
      clearable: true,
      options: [
        { label: '张三', value: 1 },
        { label: '李四', value: 2 }
      ]
    }
  }
])

const searchParams = ref<Record<string, any>>({})
const setSearchParams = (data: Record<string, any>) => {
  searchParams.value = data
  loadData()
}

const profileData = ref({
  student_name: '张三',
  gender: '男',
  mobile: '13800001111',
  school: '第一中学',
  enrollment_year: 2023,
  grade: '初三',
  class_name: '3年1班',
  student_no: '2023030101',
  stage_type: '初中'
})

const panelTitle = computed(() => {
  return `${profileData.value.school}-${profileData.value.student_no}-${profileData.value.student_name} 体质测试情况分析`
})

const statsData = ref({
  tested_item_count: 8,
  pass_items: 6,
  fail_items: 2,
  excellent_item_count: 3,
  full_item_count: 1,
  fail_items_text: '50米、耐力跑',
  excellent_items: '肺活量、跳绳、跳远',
  full_items: '肺活量'
})

const formatItemAxisLabel = (value: string) => {
  if (!value) return ''
  if (value.includes('\n') || value.length <= 3) return value
  return value.match(/.{1,2}/g)?.join('\n') || value
}

const itemScoreTrendOptions = reactive({
  title: { text: '单项分值变化趋势', textStyle: { fontSize: 15, fontWeight: 'normal' } },
  tooltip: { trigger: 'axis' },
  legend: { data: ['BMI', '肺活量', '50米', '坐位体前屈'] },
  grid: { left: '3%', right: '4%', bottom: '23%', containLabel: true },
  xAxis: {
    type: 'category',
    data: ['2025春', '2025秋', '2026春'],
    axisLabel: { interval: 0, formatter: formatItemAxisLabel }
  },
  yAxis: { type: 'value', max: 100 },
  series: [
    {
      name: 'BMI',
      type: 'bar',
      data: [70, 74, 76],
      itemStyle: { color: '#E6A23C' },
      label: { show: true, position: 'top' }
    },
    {
      name: '肺活量',
      type: 'bar',
      data: [79, 84, 88],
      itemStyle: { color: '#67C23A' },
      label: { show: true, position: 'top' }
    },
    {
      name: '50米',
      type: 'bar',
      data: [62, 68, 71],
      itemStyle: { color: '#409eff' },
      label: { show: true, position: 'top' }
    },
    {
      name: '坐位体前屈',
      type: 'bar',
      data: [70, 77, 80],
      itemStyle: { color: '#000000' },
      label: { show: true, position: 'top' }
    }
  ]
})

const itemStateTrendOptions = reactive({
  title: { text: '单项状态数量变化', textStyle: { fontSize: 15, fontWeight: 'normal' } },
  tooltip: { trigger: 'axis' },
  legend: { data: ['不及格项目数', '及格项目数', '优秀项目数', '满分项目数'] },
  xAxis: { type: 'category', data: ['2025春', '2025秋', '2026春'] },
  yAxis: { type: 'value', max: 8 },
  series: [
    {
      name: '不及格项目数',
      type: 'bar',
      data: [3, 2, 2],
      itemStyle: { color: '#F56C6C' },
      label: { show: true, position: 'top' }
    },
    {
      name: '及格项目数',
      type: 'bar',
      data: [5, 6, 6],
      itemStyle: { color: '#E6A23C' },
      label: { show: true, position: 'top' }
    },
    {
      name: '优秀项目数',
      type: 'bar',
      data: [2, 3, 3],
      itemStyle: { color: '#67C23A' },
      label: { show: true, position: 'top' }
    },
    {
      name: '满分项目数',
      type: 'bar',
      data: [0, 1, 1],
      itemStyle: { color: '#000000' },
      label: { show: true, position: 'top' }
    }
  ]
})

const scoreTextClass = (score: number, passLine: number, excellentLine: number) => {
  if (score < passLine) return 'text-fail-red'
  if (score < excellentLine) return 'text-pass-yellow'
  return 'text-excellent-green'
}

const renderScorePoint = (
  score: string,
  point: number,
  passLine: number,
  excellentLine: number
) => {
  const cls = scoreTextClass(point, passLine, excellentLine)
  return (
    <div class="leading-5">
      <div>{score}</div>
      <div class={['text-12px', cls]}>{point}分</div>
    </div>
  )
}

const tableColumns = reactive<TableColumn[]>([
  { field: 'batch_name', label: '批次', width: '130px' },
  {
    field: 'bmi_item',
    label: 'BMI(成绩/分)',
    minWidth: '120px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.bmi_score, data.row.bmi_point, 60, 80)
    }
  },
  {
    field: 'lung_item',
    label: '肺活量(成绩/分)',
    minWidth: '130px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.lung_score, data.row.lung_point, 60, 80)
    }
  },
  {
    field: 'sprint_item',
    label: '50米(成绩/分)',
    minWidth: '120px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.sprint_score, data.row.sprint_point, 60, 80)
    }
  },
  {
    field: 'sit_item',
    label: '坐位体前屈(成绩/分)',
    minWidth: '150px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.sit_score, data.row.sit_point, 60, 80)
    }
  },
  {
    field: 'rope_item',
    label: '跳绳(成绩/分)',
    minWidth: '120px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.rope_score, data.row.rope_point, 60, 80)
    }
  },
  { field: 'teacher_comment', label: '老师评语', minWidth: '170px' }
])

const detailList = ref([
  {
    batch_name: '2026春季体测',
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
    teacher_comment: '整体稳定，50米和耐力跑仍需继续提升。'
  },
  {
    batch_name: '2025秋季体测',
    bmi_score: '22.3',
    bmi_point: 74,
    lung_score: '4180ml',
    lung_point: 84,
    sprint_score: '7.9秒',
    sprint_point: 68,
    sit_score: '17.8cm',
    sit_point: 77,
    rope_score: '176次',
    rope_point: 82,
    teacher_comment: '柔韧项和肺活量进步明显。'
  },
  {
    batch_name: '2025春季体测',
    bmi_score: '23.0',
    bmi_point: 70,
    lung_score: '3960ml',
    lung_point: 79,
    sprint_score: '8.2秒',
    sprint_point: 62,
    sit_score: '16.4cm',
    sit_point: 70,
    rope_score: '168次',
    rope_point: 77,
    teacher_comment: '速度项和耐力项基础薄弱，建议专项补训。'
  }
])

const handleExport = () => {
  // 导出图表占位
}

const loadData = async () => {
  const res = await getFitnessStudentAnalysisApi({
    ...searchParams.value,
    stage_type: stageTab.value
  }).catch(() => null)
  if (!res) return
  const data = res.data || {}
  if (data.profile) {
    profileData.value = Object.assign(profileData.value, data.profile)
  }
  if (data.stats) {
    statsData.value = Object.assign(statsData.value, data.stats)
  }
  if (data.item_score_trend) {
    itemScoreTrendOptions.xAxis.data = data.item_score_trend.batches || []
    const scoreSeries = data.item_score_trend.series || []
    const scoreColors = ['#E6A23C', '#67C23A', '#409EFF', '#000000', '#F56C6C']
    itemScoreTrendOptions.legend.data = scoreSeries.map((s: any) => s.name)
    itemScoreTrendOptions.series = scoreSeries.map((s: any, idx: number) => ({
      name: s.name,
      type: 'bar',
      data: s.values || [],
      itemStyle: { color: scoreColors[idx % scoreColors.length] },
      label: { show: true, position: 'top' }
    }))
  }
  if (data.item_state_trend) {
    itemStateTrendOptions.xAxis.data = data.item_state_trend.batches || []
    itemStateTrendOptions.series[0].data = data.item_state_trend.fail_items || []
    itemStateTrendOptions.series[1].data = data.item_state_trend.pass_items || []
    itemStateTrendOptions.series[2].data = data.item_state_trend.excellent_items || []
    itemStateTrendOptions.series[3].data = data.item_state_trend.full_items || []
  }
  if (Array.isArray(data.detail_list)) {
    detailList.value = data.detail_list
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

    <div class="flex justify-between items-center mb-10px">
      <Search
        :schema="searchSchema"
        @search="setSearchParams"
        @reset="setSearchParams"
        class="flex-grow"
      />
      <div class="ml-10px">
        <BaseButton type="primary" @click="handleExport">
          <Icon icon="ant-design:bar-chart-outlined" class="mr-5px" /> 导出图表
        </BaseButton>
      </div>
    </div>

    <ElCard shadow="never" class="main-card">
      <template #header>{{ panelTitle }}</template>
      <ElDescriptions :column="3" border class="mb-20px">
        <ElDescriptionsItem label="姓名">{{ profileData.student_name }}</ElDescriptionsItem>
        <ElDescriptionsItem label="性别">{{ profileData.gender }}</ElDescriptionsItem>
        <ElDescriptionsItem label="联系方式">{{ profileData.mobile }}</ElDescriptionsItem>
        <ElDescriptionsItem label="学校">{{ profileData.school }}</ElDescriptionsItem>
        <ElDescriptionsItem label="入学年">{{ profileData.enrollment_year }}</ElDescriptionsItem>
        <ElDescriptionsItem label="年级">{{ profileData.grade }}</ElDescriptionsItem>
        <ElDescriptionsItem label="班级">{{ profileData.class_name }}</ElDescriptionsItem>
        <ElDescriptionsItem label="学号">{{ profileData.student_no }}</ElDescriptionsItem>
        <ElDescriptionsItem label="学段">{{ profileData.stage_type }}</ElDescriptionsItem>
      </ElDescriptions>

      <ElRow :gutter="20" class="mb-20px">
        <ElCol :span="6">
          <ElCard shadow="hover">
            <template #header>已测项目数</template>
            <div class="text-28px font-bold text-blue-500 text-center">{{
              statsData.tested_item_count
            }}</div>
          </ElCard>
        </ElCol>
        <ElCol :span="6">
          <ElCard shadow="hover">
            <template #header>及格项目数</template>
            <div class="text-28px font-bold text-pass-yellow text-center">{{
              statsData.pass_items
            }}</div>
          </ElCard>
        </ElCol>
        <ElCol :span="6">
          <ElCard shadow="hover">
            <template #header>不及格项目数</template>
            <div class="text-28px font-bold text-fail-red text-center">{{
              statsData.fail_items
            }}</div>
          </ElCard>
        </ElCol>
        <ElCol :span="6">
          <ElCard shadow="hover">
            <template #header>优秀项目数</template>
            <div class="text-28px font-bold text-excellent-green text-center">
              {{ statsData.excellent_item_count }}
            </div>
          </ElCard>
        </ElCol>
      </ElRow>

      <ElRow :gutter="20" class="mb-20px">
        <ElCol :span="8">
          <ElCard shadow="hover">
            <template #header>满分项目数</template>
            <div class="text-28px font-bold text-full-black text-center">
              {{ statsData.full_item_count }}
            </div>
          </ElCard>
        </ElCol>
        <ElCol :span="8">
          <ElCard shadow="hover">
            <template #header>不及格项目</template>
            <div class="text-16px font-600 text-fail-red text-center">{{
              statsData.fail_items_text
            }}</div>
          </ElCard>
        </ElCol>
        <ElCol :span="8">
          <ElCard shadow="hover">
            <template #header>优秀项目 / 满分项目</template>
            <div class="text-16px font-600 text-excellent-green text-center">{{
              statsData.excellent_items
            }}</div>
            <div class="text-16px font-600 text-full-black text-center mt-4px">{{
              statsData.full_items
            }}</div>
          </ElCard>
        </ElCol>
      </ElRow>

      <ElRow :gutter="20" class="mb-20px">
        <ElCol :span="12">
          <ElCard shadow="never" title="单项分值变化趋势">
            <Echart :options="itemScoreTrendOptions" height="360px" />
          </ElCard>
        </ElCol>
        <ElCol :span="12">
          <ElCard shadow="never" title="单项状态数量变化">
            <Echart :options="itemStateTrendOptions" height="360px" />
          </ElCard>
        </ElCol>
      </ElRow>

      <div class="mb-8px text-15px font-600">批次体测明细列表</div>
      <Table :columns="tableColumns" :data="detailList" :pagination="false" :border="false" />

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
