<script setup lang="tsx">
import { onMounted, reactive, ref } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import {
  ElCard,
  ElTag,
  ElCheckboxGroup,
  ElCheckbox,
  ElAlert,
  ElTabs,
  ElTabPane
} from 'element-plus'
import { Table, TableColumn } from '@/components/Table'
import { BaseButton } from '@/components/Button'
import { getPeReportConfigApi } from '@/api/vadmin/pe'

defineOptions({
  name: 'PEReport'
})

const examTypeTab = ref('mid')

const searchSchema = reactive<FormSchema[]>([
  {
    field: 'report_type',
    label: '报表类型',
    component: 'Select',
    componentProps: {
      placeholder: '请选择类型',
      options: [
        { label: '学生报表', value: 'student' },
        { label: '班级报表', value: 'class' },
        { label: '年级报表', value: 'grade' }
      ]
    }
  },
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
      placeholder: '请选择年级'
    }
  },
  {
    field: 'class_id',
    label: '班级',
    component: 'Select',
    componentProps: {
      placeholder: '请选择班级'
    }
  },
  {
    field: 'keyword',
    label: '学生关键词',
    component: 'Input',
    componentProps: {
      placeholder: '姓名/学号/联系方式'
    }
  }
])

const searchParams = ref<Record<string, any>>({})
const setSearchParams = (data: Record<string, any>) => {
  searchParams.value = data
}

const exportFields = ref([
  'student_base',
  'raw_value',
  'score',
  'total_score',
  'threshold_pass',
  'threshold_excellent',
  'threshold_full',
  'status',
  'version'
])

const exportStatus = ref({
  show: false,
  success: true,
  fileName: '2026春季体考-学生成绩报表.xlsx',
  errorMsg: ''
})

const handleExport = () => {
  exportStatus.value.show = true
  exportStatus.value.success = true
}

const historyData = ref([
  {
    id: 1,
    time: '2026-03-20 10:00',
    type: '学生报表',
    status: '成功',
    version: 'V2026.1'
  },
  {
    id: 2,
    time: '2026-03-19 15:30',
    type: '班级报表',
    status: '失败',
    version: 'V2026.1'
  }
])

const tableColumns = reactive<TableColumn[]>([
  { field: 'id', label: '序号', width: '70px' },
  { field: 'time', label: '导出时间', width: '180px' },
  { field: 'type', label: '报表类型', width: '120px' },
  {
    field: 'status',
    label: '状态',
    width: '90px',
    slots: {
      default: (data: any) => {
        const val = data.row.status
        return <ElTag type={val === '成功' ? 'success' : 'danger'}>{val}</ElTag>
      }
    }
  },
  { field: 'version', label: '标准版本号', width: '120px' },
  {
    field: 'action',
    label: '操作',
    minWidth: '140px',
    slots: {
      default: (data: any) => {
        return (
          <>
            <BaseButton type="primary" link size="small">
              下载
            </BaseButton>
            {data.row.status === '失败' && (
              <BaseButton type="danger" link size="small">
                重试
              </BaseButton>
            )}
          </>
        )
      }
    }
  }
])

const loadConfig = async () => {
  const res = await getPeReportConfigApi().catch(() => null)
  if (!res) return
  const data = res.data || {}
  if (Array.isArray(data.default_fields)) {
    const fieldMap: Record<string, string> = {
      学生基础信息: 'student_base',
      项目成绩: 'raw_value',
      项目评分成绩: 'score',
      总分: 'total_score',
      '及格/优秀/满分状态': 'status',
      标准版本号: 'version'
    }
    exportFields.value = data.default_fields.map((item: string) => fieldMap[item]).filter(Boolean)
  }
  if (Array.isArray(data.history)) {
    historyData.value = data.history
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<template>
  <ContentWrap>
    <ElTabs v-model="examTypeTab" class="mb-10px">
      <ElTabPane label="初中" name="mid" />
      <ElTabPane label="高中" name="high" />
    </ElTabs>

    <div class="flex justify-between items-center mb-20px">
      <Search
        :schema="searchSchema"
        @search="setSearchParams"
        @reset="setSearchParams"
        class="flex-grow"
      />
      <div class="ml-10px">
        <BaseButton type="primary" @click="handleExport">生成报表</BaseButton>
      </div>
    </div>

    <ElCard shadow="never" class="mb-20px" title="导出字段选择">
      <ElCheckboxGroup v-model="exportFields">
        <ElCheckbox label="student_base">学生基础信息</ElCheckbox>
        <ElCheckbox label="raw_value">项目成绩</ElCheckbox>
        <ElCheckbox label="score">项目评分成绩</ElCheckbox>
        <ElCheckbox label="total_score">总分</ElCheckbox>
        <ElCheckbox label="threshold_pass">及格阈值</ElCheckbox>
        <ElCheckbox label="threshold_excellent">优秀阈值</ElCheckbox>
        <ElCheckbox label="threshold_full">满分阈值</ElCheckbox>
        <ElCheckbox label="status">及格/优秀/满分状态</ElCheckbox>
        <ElCheckbox label="version">标准版本号</ElCheckbox>
      </ElCheckboxGroup>
    </ElCard>

    <div v-if="exportStatus.show" class="mb-20px">
      <ElAlert
        v-if="exportStatus.success"
        title="本次导出成功"
        type="success"
        show-icon
        :closable="false"
      >
        <p>文件名: {{ exportStatus.fileName }}</p>
        <BaseButton type="primary" link>立即下载</BaseButton>
      </ElAlert>
      <ElAlert v-else title="本次导出失败" type="error" show-icon :closable="false">
        <p>错误原因: {{ exportStatus.errorMsg }}</p>
        <BaseButton type="danger" link>重新生成</BaseButton>
      </ElAlert>
    </div>

    <ElCard shadow="never" title="最近导出记录">
      <Table :columns="tableColumns" :data="historyData" :pagination="false" />
    </ElCard>
  </ContentWrap>
</template>
