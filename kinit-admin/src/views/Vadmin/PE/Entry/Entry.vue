<script setup lang="tsx">
import { onMounted, ref, computed } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import { ElMessage, ElCard, ElTable, ElTableColumn, ElInput, ElButton, ElIcon, ElDialog, ElEmpty } from 'element-plus'
import { QuestionFilled } from '@element-plus/icons-vue'
import {
  confirmPeScoresApi,
  downloadPeScoreTemplateApi,
  getPeBatchOptionsApi,
  importPeScoresApi,
  upsertPeScoresApi
} from '@/api/vadmin/pe'
import { getSchoolOptionsApi, getStandardItemOptionsApi, getStudentListApi } from '@/api/vadmin/sport'
import ScoreImport from '@/views/Vadmin/Sport/components/ScoreImport.vue'

defineOptions({ name: 'PEScoreEntry' })

type StandardItemOption = {
  label: string
  value: string
  help_lines?: string[]
}

const loading = ref(false)
const entryMode = ref<'student' | 'item'>('student')
const batchOptions = ref<any[]>([])
const schoolOptions = ref<any[]>([])
const itemOptions = ref<StandardItemOption[]>([])
const studentList = ref<any[]>([])
const importDialogVisible = ref(false)
const ruleDialogVisible = ref(false)
const ruleDialogTitle = ref('')
const ruleDialogLines = ref<string[]>([])

const currentItemOption = computed(() =>
  itemOptions.value.find((item) => item.value === searchParams.value?.item_code) || null
)

const currentBatchOption = computed(() =>
  batchOptions.value.find((item) => item.value === searchParams.value?.batch_id) || null
)

const itemOptionMap = computed<Record<string, StandardItemOption>>(() => {
  return itemOptions.value.reduce((map, item) => {
    map[item.value] = item
    return map
  }, {} as Record<string, StandardItemOption>)
})

const openRuleDialog = (label: string, helpLines?: string[], event?: Event) => {
  event?.stopPropagation()
  ruleDialogTitle.value = label
  ruleDialogLines.value = (helpLines || []).filter(Boolean)
  ruleDialogVisible.value = true
}

const openImportDialog = () => {
  if (!searchParams.value?.batch_id) {
    ElMessage.warning('请先选择批次并查询')
    return
  }
  importDialogVisible.value = true
}

const handleImportSuccess = () => {
  if (searchParams.value?.batch_id) loadStudents()
}

const loadStandardItems = async (batchId?: number) => {
  const batch = batchOptions.value.find((item) => item.value === batchId)
  if (!batch?.standard_id) {
    itemOptions.value = []
    return
  }
  const res = await getStandardItemOptionsApi({ standard_id: batch.standard_id }).catch(() => null)
  itemOptions.value = res?.data || []
}

const renderHeaderLabel = (label: string, helpLines?: string[]) => {
  const lines = (helpLines || []).filter(Boolean)
  return () => (
    <div class="entry-header">
      <span>{label}</span>
      {lines.length ? (
        <span class="entry-header__icon" onClick={(event: MouseEvent) => openRuleDialog(label, lines, event)}>
          <ElIcon>
            <QuestionFilled />
          </ElIcon>
        </span>
      ) : null}
    </div>
  )
}

const searchSchema = computed<FormSchema[]>(() => {
  const schema: FormSchema[] = [
    {
      field: 'batch_id',
      label: '体考批次',
      component: 'Select',
      componentProps: { 
        options: batchOptions.value,
        filterable: true,
        onChange: async (val: number) => {
          await loadStandardItems(val)
        }
      }
    },
    {
      field: 'school_name',
      label: '学校',
      component: 'Select',
      componentProps: { options: schoolOptions.value }
    }
  ]

  if (entryMode.value === 'item') {
    schema.push({
      field: 'item_code',
      label: '录入项目',
      component: 'Select',
      componentProps: { options: itemOptions.value }
    })
  }

  return schema
})

const searchParams = ref<any>({})

const changeMode = (mode: 'student' | 'item') => {
  entryMode.value = mode
  if (mode === 'item' && !searchParams.value.item_code) {
    studentList.value = []
  } else if (searchParams.value.batch_id) {
    loadStudents()
  }
}

const handleSearch = async (data: any) => {
  searchParams.value = data
  if (!data.batch_id) {
    ElMessage.warning('请选择批次')
    return
  }
  if (entryMode.value === 'item' && !data.item_code) {
    ElMessage.warning('按项目录入模式下，请在搜索栏选择具体的录入项目')
    studentList.value = []
    return
  }
  loadStudents()
}

const loadStudents = async () => {
  loading.value = true
  const res = await getStudentListApi({ 
    school_name: searchParams.value.school_name,
    limit: 100 
  }).catch(() => null)
  
  if (res && res.data) {
    studentList.value = res.data.items.map((s: any) => ({
      student_no: s.student_no,
      student_name: s.name,
      school_name: s.school_name,
      grade_name: s.grade_name,
      class_name: s.class_name,
      gender: s.gender,
      raw_scores: {}, // 用于“按学生”模式录入的所有项目成绩
      raw_score: '',  // 用于“按项目”模式录入的单一成绩
      teacher_comment: ''
    }))
  }
  loading.value = false
}

const submit = async () => {
  if (!searchParams.value.batch_id) return
  
  const scores: any[] = []
  
  if (entryMode.value === 'item') {
    if (!searchParams.value.item_code) {
      ElMessage.warning('按项目录入模式下，请在搜索栏选择具体的录入项目')
      return
    }
    studentList.value.forEach(s => {
      if (s.raw_score !== '') {
        scores.push({
          ...s,
          item_code: searchParams.value.item_code,
          item_name: currentItemOption.value?.label,
          raw_score: s.raw_score
        })
      }
    })
  } else {
    studentList.value.forEach(s => {
      Object.keys(s.raw_scores).forEach(code => {
        if (s.raw_scores[code] !== '') {
          scores.push({
            ...s,
            item_code: code,
            item_name: itemOptionMap.value[code]?.label,
            raw_score: s.raw_scores[code]
          })
        }
      })
    })
  }
  
  if (scores.length === 0) {
    ElMessage.warning('没有可提交的有效成绩')
    return
  }

  const payload = {
    batch_id: searchParams.value.batch_id,
    scores
  }
  const res = await upsertPeScoresApi(payload).catch(() => null)
  if (res) ElMessage.success('成绩已成功保存')
}

onMounted(async () => {
  const [bRes, sRes] = await Promise.all([getPeBatchOptionsApi(), getSchoolOptionsApi()])
  if (bRes) batchOptions.value = bRes.data
  if (sRes) schoolOptions.value = sRes.data.map(i => ({ label: i.label, value: i.school_name }))
})
</script>

<template>
  <ContentWrap>
    <div class="mb-10px flex justify-between items-center">
      <div class="text-18px font-bold">体考成绩录入</div>
      <div>
        <ElButton type="success" @click="openImportDialog">批量导入成绩</ElButton>
        <ElButton :type="entryMode === 'student' ? 'primary' : 'default'" @click="changeMode('student')">按学生录入</ElButton>
        <ElButton :type="entryMode === 'item' ? 'primary' : 'default'" @click="changeMode('item')">按项目录入</ElButton>
      </div>
    </div>

    <Search :schema="searchSchema" @search="handleSearch" @reset="handleSearch" class="mb-20px" />

    <ElCard shadow="never">
      <ElTable :data="studentList" border stripe v-loading="loading">
        <ElTableColumn prop="student_no" label="学号" width="120" fixed="left" />
        <ElTableColumn prop="student_name" label="姓名" width="100" fixed="left" />
        <ElTableColumn prop="class_name" label="班级" width="120" />
        
        <!-- 按学生录入模式：动态展示所有项目列 -->
        <template v-if="entryMode === 'student'">
          <ElTableColumn
            v-for="item in itemOptions"
            :key="item.value"
            :label="item.label"
            :render-header="renderHeaderLabel(item.label, item.help_lines)"
            min-width="150"
          >
            <template #default="{ row }">
              <ElInput v-model="row.raw_scores[item.value]" placeholder="输入成绩" />
            </template>
          </ElTableColumn>
        </template>
        
        <!-- 按项目录入模式：仅展示选定项目的单一成绩列 -->
        <template v-else>
          <ElTableColumn
            label="当前单项录入成绩"
            :render-header="renderHeaderLabel(currentItemOption?.label || '当前单项录入成绩', currentItemOption?.help_lines)"
            min-width="180"
          >
            <template #default="{ row }">
              <ElInput v-model="row.raw_score" placeholder="请输入成绩，如 3'20 或 50" />
            </template>
          </ElTableColumn>
        </template>

        <ElTableColumn label="老师评语" min-width="150">
          <template #default="{ row }">
            <ElInput v-model="row.teacher_comment" placeholder="选填评语" />
          </template>
        </ElTableColumn>
      </ElTable>
      
      <div class="mt-20px text-center">
        <ElButton type="primary" size="large" @click="submit" class="w-200px">提交并保存成绩</ElButton>
      </div>
    </ElCard>

    <ElDialog v-model="ruleDialogVisible" :title="`${ruleDialogTitle}得分计算规则`" width="760px">
      <div v-if="ruleDialogLines.length" class="entry-rule-list">
        <div v-for="line in ruleDialogLines" :key="line" class="entry-rule-list__item">{{ line }}</div>
      </div>
      <ElEmpty v-else description="暂无规则说明" />
    </ElDialog>

    <ElDialog v-model="importDialogVisible" title="批量导入体考成绩" width="920px">
      <ScoreImport
        biz-name="体考"
        :batch-id="searchParams.batch_id"
        :batch-label="currentBatchOption?.label || ''"
        :download-template-api="downloadPeScoreTemplateApi"
        :import-scores-api="importPeScoresApi"
        :confirm-scores-api="confirmPeScoresApi"
        @success="handleImportSuccess"
      />
    </ElDialog>
  </ContentWrap>
</template>

<style scoped>
.entry-header {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.entry-header__icon {
  color: var(--el-color-primary);
  cursor: pointer;
  font-size: 14px;
}

.entry-rule-list {
  display: grid;
  gap: 8px;
  max-height: 62vh;
  overflow: auto;
}

.entry-rule-list__item {
  padding: 10px 12px;
  border-radius: 12px;
  background: #f8fafc;
  color: #334155;
  line-height: 1.6;
}
</style>
