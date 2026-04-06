<script setup lang="tsx">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import {
  ElRow,
  ElCol,
  ElCard,
  ElTag,
  ElTabs,
  ElTabPane,
  ElDescriptions,
  ElDescriptionsItem
} from 'element-plus'
import { Echart } from '@/components/Echart'
import { Table, TableColumn } from '@/components/Table'
import { Icon } from '@/components/Icon'
import { BaseButton } from '@/components/Button'
import { getPeStudentAnalysisApi } from '@/api/vadmin/pe'

defineOptions({
  name: 'StudentAnalysis'
})

const examTypeTab = ref('mid')

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
  exam_type: '初中'
})

const panelTitle = computed(() => {
  return `${profileData.value.school}-${profileData.value.student_no}-${profileData.value.student_name} 体育项目情况分析`
})

const statsData = ref({
  latest_total: 44,
  history_max_total: 47,
  pass_items: 3,
  fail_items: 1,
  excellent_item_count: 2,
  full_item_count: 1,
  excellent_items: '跳绳、立定跳远',
  full_items: '1分钟跳绳'
})

const totalTrendOptions = reactive({
  title: { text: '总分变化趋势', textStyle: { fontSize: 15, fontWeight: 'normal' } },
  tooltip: { trigger: 'axis' },
  legend: { data: ['总分', '及格线', '优秀线', '满分线'] },
  xAxis: { type: 'category', data: ['2025春', '2025秋', '2026春'] },
  yAxis: { type: 'value', max: 50 },
  series: [
    {
      name: '总分',
      type: 'line',
      smooth: true,
      data: [39, 42, 44],
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

const itemTrendOptions = reactive({
  title: { text: '各项目变化趋势', textStyle: { fontSize: 15, fontWeight: 'normal' } },
  tooltip: { trigger: 'axis' },
  legend: { data: ['跳绳', '跳远', '实心球'] },
  xAxis: { type: 'category', data: ['2025春', '2025秋', '2026春'] },
  yAxis: { type: 'value', max: 20 },
  series: [
    {
      name: '跳绳',
      type: 'bar',
      data: [16, 18, 18],
      itemStyle: { color: '#67C23A' },
      label: { show: true, position: 'top', formatter: '{c}分' }
    },
    {
      name: '跳远',
      type: 'bar',
      data: [9, 10, 11],
      itemStyle: { color: '#E6A23C' },
      label: { show: true, position: 'top', formatter: '{c}分' }
    },
    {
      name: '实心球',
      type: 'bar',
      data: [8, 10, 11],
      itemStyle: { color: '#F56C6C' },
      label: { show: true, position: 'top', formatter: '{c}分' }
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
    field: 'gate_item',
    label: '门槛项(成绩/分)',
    minWidth: '130px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.gate_score, data.row.gate_point, 10, 14)
    }
  },
  {
    field: 'rope_item',
    label: '跳绳(成绩/分)',
    minWidth: '120px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.rope_score, data.row.rope_point, 14, 18)
    }
  },
  {
    field: 'jump_item',
    label: '跳远(成绩/分)',
    minWidth: '120px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.jump_score, data.row.jump_point, 10, 13)
    }
  },
  {
    field: 'ball_item',
    label: '实心球(成绩/分)',
    minWidth: '130px',
    slots: {
      default: (data: any) => renderScorePoint(data.row.ball_score, data.row.ball_point, 10, 13)
    }
  },
  { field: 'total_score', label: '总分', width: '80px' },
  {
    field: 'pass_state',
    label: '及格状态',
    width: '90px',
    slots: {
      default: (data: any) => {
        if (!data.row.pass_state) {
          return <ElTag type="danger">不及格</ElTag>
        }
        return (
          <ElTag style={{ backgroundColor: '#e6a23c', borderColor: '#e6a23c', color: '#fff' }}>
            及格
          </ElTag>
        )
      }
    }
  },
  {
    field: 'excellent_state',
    label: '优秀状态',
    width: '90px',
    slots: {
      default: (data: any) => {
        if (!data.row.excellent_state) {
          return <ElTag type="info">未优秀</ElTag>
        }
        return (
          <ElTag style={{ backgroundColor: '#67c23a', borderColor: '#67c23a', color: '#fff' }}>
            优秀
          </ElTag>
        )
      }
    }
  },
  { field: 'teacher_comment', label: '老师评语', minWidth: '170px' }
])

const detailList = ref([
  {
    batch_name: '2026春季体考',
    gate_score: '3分52秒',
    gate_point: 12,
    rope_score: '180次',
    rope_point: 18,
    jump_score: '2.30m',
    jump_point: 11,
    ball_score: '8.8m',
    ball_point: 11,
    total_score: 44,
    pass_state: true,
    excellent_state: true,
    teacher_comment: '门槛项和跳绳保持稳定，跳远可继续提升。'
  },
  {
    batch_name: '2025秋季体考',
    gate_score: '3分58秒',
    gate_point: 11,
    rope_score: '176次',
    rope_point: 17,
    jump_score: '2.26m',
    jump_point: 10,
    ball_score: '8.2m',
    ball_point: 10,
    total_score: 42,
    pass_state: true,
    excellent_state: false,
    teacher_comment: '整体稳定，实心球出手动作需要纠正。'
  },
  {
    batch_name: '2025春季体考',
    gate_score: '4分14秒',
    gate_point: 8,
    rope_score: '170次',
    rope_point: 16,
    jump_score: '2.21m',
    jump_point: 9,
    ball_score: '7.9m',
    ball_point: 8,
    total_score: 39,
    pass_state: false,
    excellent_state: false,
    teacher_comment: '门槛项配速不足，需先强化耐力训练。'
  }
])

const handleExport = () => {
  // 导出图表占位
}

const loadData = async () => {
  const res = await getPeStudentAnalysisApi({
    ...searchParams.value,
    stage_type: examTypeTab.value
  }).catch(() => null)
  if (!res) return
  const data = res.data || {}
  if (data.profile) {
    profileData.value = Object.assign(profileData.value, data.profile)
  }
  if (data.stats) {
    statsData.value = Object.assign(statsData.value, data.stats)
  }
  if (data.total_trend) {
    totalTrendOptions.xAxis.data = data.total_trend.batches || []
    totalTrendOptions.series[0].data = data.total_trend.total || []
    totalTrendOptions.series[1].data = data.total_trend.pass_line || []
    totalTrendOptions.series[2].data = data.total_trend.excellent_line || []
    totalTrendOptions.series[3].data = data.total_trend.full_line || []
  }
  if (data.item_trend) {
    itemTrendOptions.xAxis.data = data.item_trend.batches || []
    const itemSeries = data.item_trend.series || []
    const colors = ['#67C23A', '#E6A23C', '#F56C6C', '#409EFF']
    itemTrendOptions.legend.data = itemSeries.map((s: any) => s.name)
    itemTrendOptions.series = itemSeries.map((s: any, idx: number) => ({
      name: s.name,
      type: 'bar',
      data: s.values || [],
      itemStyle: { color: colors[idx % colors.length] },
      label: { show: true, position: 'top', formatter: '{c}分' }
    }))
  }
  if (Array.isArray(data.detail_list)) {
    detailList.value = data.detail_list
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
        <ElDescriptionsItem label="考试类型">{{ profileData.exam_type }}</ElDescriptionsItem>
      </ElDescriptions>

      <ElRow :gutter="20" class="mb-20px">
        <ElCol :span="6">
          <ElCard shadow="hover">
            <template #header>最新总分</template>
            <div class="text-28px font-bold text-blue-500 text-center">{{
              statsData.latest_total
            }}</div>
          </ElCard>
        </ElCol>
        <ElCol :span="6">
          <ElCard shadow="hover">
            <template #header>历史最高总分</template>
            <div class="text-28px font-bold text-full-black text-center">
              {{ statsData.history_max_total }}
            </div>
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
      </ElRow>

      <ElRow :gutter="20" class="mb-20px">
        <ElCol :span="6">
          <ElCard shadow="hover">
            <template #header>优秀项目数</template>
            <div class="text-28px font-bold text-excellent-green text-center">
              {{ statsData.excellent_item_count }}
            </div>
          </ElCard>
        </ElCol>
        <ElCol :span="6">
          <ElCard shadow="hover">
            <template #header>满分项目数</template>
            <div class="text-28px font-bold text-full-black text-center">
              {{ statsData.full_item_count }}
            </div>
          </ElCard>
        </ElCol>
        <ElCol :span="6">
          <ElCard shadow="hover">
            <template #header>优秀项目</template>
            <div class="text-16px font-600 text-excellent-green text-center">
              {{ statsData.excellent_items }}
            </div>
          </ElCard>
        </ElCol>
        <ElCol :span="6">
          <ElCard shadow="hover">
            <template #header>满分项目</template>
            <div class="text-16px font-600 text-full-black text-center">
              {{ statsData.full_items }}
            </div>
          </ElCard>
        </ElCol>
      </ElRow>

      <ElRow :gutter="20" class="mb-20px">
        <ElCol :span="12">
          <ElCard shadow="never" title="总分变化趋势">
            <Echart :options="totalTrendOptions" height="360px" />
          </ElCard>
        </ElCol>
        <ElCol :span="12">
          <ElCard shadow="never" title="各项目变化趋势（不及格红 / 及格黄 / 优秀绿）">
            <Echart :options="itemTrendOptions" height="360px" />
          </ElCard>
        </ElCol>
      </ElRow>

      <div class="mb-8px text-15px font-600">批次成绩列表</div>
      <Table :columns="tableColumns" :data="detailList" :pagination="false" :border="false" />
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
