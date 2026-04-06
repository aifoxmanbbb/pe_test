<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import type { FormSchema } from '@/components/Form'
import {
  ElCard,
  ElTag,
  ElDescriptions,
  ElDescriptionsItem,
  ElTable,
  ElTableColumn,
  ElInput,
  ElMessage,
  ElAlert,
  ElButton,
  ElEmpty
} from 'element-plus'
import { BaseButton } from '@/components/Button'
import {
  getFitnessEntryTemplateApi,
  getFitnessBatchOptionsApi,
  upsertFitnessScoresApi
} from '@/api/vadmin/fitness'

defineOptions({
  name: 'FitnessEntry'
})

// ─── 搜索区 ──────────────────────────────────────────────
const batchOptions = ref<{ label: string; value: number }[]>([])

const searchSchema = reactive<FormSchema[]>([
  {
    field: 'batch_id',
    label: '批次',
    component: 'Select',
    componentProps: {
      placeholder: '请选择体测批次',
      options: batchOptions,
      filterable: true
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
      placeholder: '输入姓名/学号/联系方式搜索',
      filterable: true,
      clearable: true,
      options: [
        { label: '张三（2023030101）', value: '2023030101' },
        { label: '李四（2023030102）', value: '2023030102' }
      ]
    }
  }
])

const searchParams = ref<Record<string, any>>({})

// ─── 标准配置 ─────────────────────────────────────────────
const templateData = ref({
  items: [] as string[],
  calc_policy: '仅录入成绩可自动计算分值',
  conflict_policy: '就低不就高'
})

// ─── 当前学生档案 ─────────────────────────────────────────
const studentProfile = ref<{
  student_no: string
  student_name: string
  gender: string
  class_name: string
  grade_name: string
  school_name: string
} | null>(null)

// ─── 录入表数据 ───────────────────────────────────────────
interface ItemRow {
  item_code: string
  item_name: string
  raw_score: string
  score_value: string | number
  level: string
  pass_threshold: string
  excellent_threshold: string
  full_threshold: string
  is_gate_item: boolean
}

const itemRows = ref<ItemRow[]>([])

// 根据所选学生与批次加载录入模板
const buildItemRows = (items: string[]) => {
  itemRows.value = items.map((name, idx) => ({
    item_code: `item_${idx + 1}`,
    item_name: name,
    raw_score: '',
    score_value: '-',
    level: '-',
    pass_threshold: idx === 0 ? '合格判定' : '60',
    excellent_threshold: idx === 0 ? '-' : '80',
    full_threshold: idx === 0 ? '-' : '100',
    is_gate_item: idx === 0
  }))
}

// ─── 保存状态 ─────────────────────────────────────────────
const saving = ref(false)
const saveResult = ref<{ show: boolean; success: boolean; msg: string }>({
  show: false,
  success: true,
  msg: ''
})

const hasData = computed(() => itemRows.value.length > 0 && studentProfile.value)

const setSearchParams = (params: Record<string, any>) => {
  searchParams.value = params
  // 选择学生后模拟加载该学生档案
  if (params.student_id) {
    const isZhangSan = params.student_id === '2023030101'
    studentProfile.value = {
      student_no: params.student_id,
      student_name: isZhangSan ? '张三' : '李四',
      gender: isZhangSan ? '男' : '女',
      class_name: '3年1班',
      grade_name: '初三',
      school_name: '第一中学'
    }
  } else {
    studentProfile.value = null
    itemRows.value = []
    return
  }
  if (templateData.value.items.length > 0) {
    buildItemRows(templateData.value.items)
  }
}

// 成绩变化时实时模拟自动算分（实际由后端引擎计算，此处仅做前端回显占位）
const onRawScoreChange = (row: ItemRow) => {
  const val = parseFloat(row.raw_score)
  if (isNaN(val) || row.raw_score === '') {
    row.score_value = '-'
    row.level = '-'
    return
  }
  if (row.is_gate_item) {
    row.score_value = '-'
    row.level = val <= 260 ? '合格' : '不合格'
    return
  }
  // 占位算分：正式由后端 rule_engine 计算
  row.score_value = '待算分'
  row.level = '待算分'
}

const handleSave = async () => {
  if (!searchParams.value.batch_id) {
    ElMessage.warning('请先选择体测批次')
    return
  }
  if (!studentProfile.value) {
    ElMessage.warning('请先选择学生')
    return
  }
  const scores = itemRows.value
    .filter((row) => row.raw_score !== '')
    .map((row) => ({
      student_no: studentProfile.value!.student_no,
      student_name: studentProfile.value!.student_name,
      gender: studentProfile.value!.gender,
      school_name: studentProfile.value!.school_name,
      grade_name: studentProfile.value!.grade_name,
      class_name: studentProfile.value!.class_name,
      item_code: row.item_code,
      item_name: row.item_name,
      raw_score: row.raw_score
    }))

  if (scores.length === 0) {
    ElMessage.warning('请至少录入一项成绩')
    return
  }

  saving.value = true
  saveResult.value.show = false
  try {
    const res = await upsertFitnessScoresApi({
      batch_id: searchParams.value.batch_id,
      scores
    })
    if (res && res.data) {
      saveResult.value = { show: true, success: true, msg: `成功保存 ${res.data.upsert_count ?? scores.length} 条成绩，系统已自动计算分值。` }
      ElMessage.success('保存成功')
    }
  } catch (e) {
    saveResult.value = { show: true, success: false, msg: '保存失败，请检查网络后重试。' }
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const handleImport = () => {
  ElMessage.info('批量导入功能待接入（上传 Excel 模板解析后人工确认）')
}

const handleDownloadTemplate = () => {
  ElMessage.info('导出模板功能待接入')
}

const loadBatchOptions = async () => {
  const res = await getFitnessBatchOptionsApi().catch(() => null)
  if (res && Array.isArray(res.data)) {
    batchOptions.value = res.data
    // 同步更新 searchSchema 里的 options
    const batchField = searchSchema.find((s) => s.field === 'batch_id')
    if (batchField && batchField.componentProps) {
      batchField.componentProps.options = res.data
    }
  }
}

const loadTemplate = async () => {
  const res = await getFitnessEntryTemplateApi().catch(() => null)
  if (!res) return
  const data = res.data || {}
  templateData.value = Object.assign(templateData.value, data)
  if (studentProfile.value && templateData.value.items.length > 0) {
    buildItemRows(templateData.value.items)
  }
}

onMounted(async () => {
  await loadBatchOptions()
  await loadTemplate()
})

watch(
  () => searchParams.value.student_id,
  () => {
    saveResult.value.show = false
  }
)
</script>

<template>
  <ContentWrap>
    <Search :schema="searchSchema" @search="setSearchParams" @reset="setSearchParams" />

    <!-- 标准信息栏 -->
    <ElCard shadow="never" class="mt-10px mb-10px">
      <div class="flex items-center gap-12px flex-wrap">
        <span class="text-gray-500 text-13px">录入规则：</span>
        <ElTag type="warning">{{ templateData.calc_policy }}</ElTag>
        <ElTag type="danger">冲突策略：{{ templateData.conflict_policy }}</ElTag>
        <span class="text-gray-400 text-13px ml-8px">
          项目：{{ templateData.items.join('、') || '—' }}
        </span>
      </div>
    </ElCard>

    <!-- 学生档案 -->
    <ElCard v-if="studentProfile" shadow="never" class="mb-10px">
      <ElDescriptions :column="6" size="small">
        <ElDescriptionsItem label="学生">{{ studentProfile.student_name }}</ElDescriptionsItem>
        <ElDescriptionsItem label="性别">{{ studentProfile.gender }}</ElDescriptionsItem>
        <ElDescriptionsItem label="学号">{{ studentProfile.student_no }}</ElDescriptionsItem>
        <ElDescriptionsItem label="学校">{{ studentProfile.school_name }}</ElDescriptionsItem>
        <ElDescriptionsItem label="年级">{{ studentProfile.grade_name }}</ElDescriptionsItem>
        <ElDescriptionsItem label="班级">{{ studentProfile.class_name }}</ElDescriptionsItem>
      </ElDescriptions>
    </ElCard>

    <!-- 录入表 -->
    <ElCard shadow="never" header="项目录入表（仅录入成绩，分值由系统引擎自动计算）">
      <ElEmpty v-if="!hasData" description="请先选择批次和学生以加载录入表" />

      <ElTable v-else :data="itemRows" border stripe>
        <ElTableColumn label="项目" prop="item_name" width="160">
          <template #default="{ row }">
            <span>{{ row.item_name }}</span>
            <ElTag v-if="row.is_gate_item" type="danger" size="small" class="ml-6px">门槛项</ElTag>
          </template>
        </ElTableColumn>

        <ElTableColumn label="成绩" width="200">
          <template #default="{ row }">
            <ElInput
              v-model="row.raw_score"
              placeholder="请输入成绩"
              clearable
              size="small"
              @input="onRawScoreChange(row)"
            />
          </template>
        </ElTableColumn>

        <ElTableColumn label="自动分值" width="110" align="center">
          <template #default="{ row }">
            <span class="text-14px font-600 text-blue-500">{{ row.score_value }}</span>
          </template>
        </ElTableColumn>

        <ElTableColumn label="等级" width="100" align="center">
          <template #default="{ row }">
            <ElTag
              v-if="row.level !== '-' && row.level !== '待算分'"
              :type="
                row.level === '满分'
                  ? 'info'
                  : row.level === '优秀'
                    ? 'success'
                    : row.level === '及格' || row.level === '合格'
                      ? 'warning'
                      : 'danger'
              "
              size="small"
            >
              {{ row.level }}
            </ElTag>
            <span v-else class="text-gray-400">{{ row.level }}</span>
          </template>
        </ElTableColumn>

        <ElTableColumn label="及格阈值" prop="pass_threshold" width="110" align="center" />
        <ElTableColumn label="优秀阈值" prop="excellent_threshold" width="110" align="center" />
        <ElTableColumn label="满分阈值" prop="full_threshold" width="110" align="center" />
      </ElTable>

      <!-- 操作按钮 -->
      <div v-if="hasData" class="mt-16px flex gap-10px">
        <BaseButton type="primary" :loading="saving" @click="handleSave">保存</BaseButton>
        <BaseButton type="success" @click="handleImport">批量导入</BaseButton>
        <BaseButton type="default" @click="handleDownloadTemplate">导出模板</BaseButton>
      </div>

      <!-- 保存结果反馈 -->
      <ElAlert
        v-if="saveResult.show"
        class="mt-12px"
        :type="saveResult.success ? 'success' : 'error'"
        :title="saveResult.msg"
        show-icon
        :closable="true"
        @close="saveResult.show = false"
      />
    </ElCard>
  </ContentWrap>
</template>

<style scoped lang="less">
.text-blue-500 {
  color: #409eff;
}
</style>
