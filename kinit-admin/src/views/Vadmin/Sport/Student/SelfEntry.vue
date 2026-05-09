<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import {
  ElButton,
  ElCard,
  ElDialog,
  ElEmpty,
  ElIcon,
  ElInput,
  ElMessage,
  ElOption,
  ElSelect,
  ElTag
} from 'element-plus'
import { QuestionFilled } from '@element-plus/icons-vue'
import {
  getStudentSelfEntryOptionsApi,
  submitStudentSelfEntryApi
} from '@/api/vadmin/sport'
import { getScoreInputPlaceholder } from '@/utils/scoreInputPlaceholder'

defineOptions({ name: 'StudentSelfEntry' })

type EntryItem = {
  label: string
  value: string
  item_name?: string
  calc_mode?: string
  help_lines?: string[]
}

type EntryBatch = {
  label: string
  value: number
  batch_id: number
  biz_type: 'pe' | 'fitness'
  biz_name: string
  items: EntryItem[]
}

const loading = ref(false)
const submitting = ref(false)
const profile = ref<Record<string, any>>({})
const batches = ref<EntryBatch[]>([])
const selectedBatchId = ref<number | undefined>(undefined)
const rawScores = ref<Record<string, string>>({})
const ruleDialogVisible = ref(false)
const ruleDialogTitle = ref('')
const ruleDialogLines = ref<string[]>([])

const currentBatch = computed(() => {
  return batches.value.find((item) => item.value === selectedBatchId.value) || null
})

const batchItems = computed(() => currentBatch.value?.items || [])

const resetScoreInputs = () => {
  rawScores.value = {}
  batchItems.value.forEach((item) => {
    rawScores.value[item.value] = ''
  })
}

const openRuleDialog = (item: EntryItem) => {
  ruleDialogTitle.value = item.label
  ruleDialogLines.value = (item.help_lines || []).filter(Boolean)
  ruleDialogVisible.value = true
}

const loadData = async () => {
  loading.value = true
  const res = await getStudentSelfEntryOptionsApi().catch(() => null)
  if (res?.data) {
    profile.value = res.data.profile || {}
    batches.value = res.data.batches || []
    selectedBatchId.value = batches.value[0]?.value
    resetScoreInputs()
  }
  loading.value = false
}

const handleBatchChange = () => {
  resetScoreInputs()
}

const submit = async () => {
  if (!currentBatch.value) {
    ElMessage.warning('请选择要录入的批次')
    return
  }
  const scores = batchItems.value
    .map((item) => ({
      item_code: item.value,
      item_name: item.item_name || item.label,
      raw_score: String(rawScores.value[item.value] ?? '').trim()
    }))
    .filter((item) => item.raw_score)

  if (!scores.length) {
    ElMessage.warning('请至少填写一项成绩')
    return
  }

  submitting.value = true
  const res = await submitStudentSelfEntryApi({
    batch_id: currentBatch.value.batch_id,
    scores
  }).catch(() => null)
  submitting.value = false
  if (res) {
    ElMessage.success(res.message || '成绩已提交，评分计算中')
  }
}

onMounted(loadData)
</script>

<template>
  <ContentWrap>
    <div class="self-entry" v-loading="loading">
      <section class="self-entry__hero">
        <div>
          <ElTag effect="dark" class="self-entry__tag">学生自主录入</ElTag>
          <h1>提交体考体测成绩</h1>
          <p>按当前适用批次填写原始成绩，提交后由系统进行评分处理，本页面不展示分值和排名。</p>
        </div>
        <div class="self-entry__profile">
          <span>{{ profile.school_name || '-' }}</span>
          <strong>{{ profile.student_name || '-' }}</strong>
          <em>{{ profile.grade_name || '-' }} / {{ profile.class_name || '-' }} / {{ profile.student_no || '-' }}</em>
        </div>
      </section>

      <ElCard shadow="never" class="self-entry__panel">
        <div class="self-entry__toolbar">
          <div>
            <div class="self-entry__label">录入批次</div>
            <ElSelect
              v-model="selectedBatchId"
              placeholder="请选择批次"
              filterable
              class="self-entry__select"
              @change="handleBatchChange"
            >
              <ElOption
                v-for="batch in batches"
                :key="batch.value"
                :label="`${batch.biz_name} / ${batch.label}`"
                :value="batch.value"
              />
            </ElSelect>
          </div>
          <ElTag v-if="currentBatch" effect="plain">{{ currentBatch.biz_name }}</ElTag>
        </div>

        <ElEmpty v-if="!currentBatch" description="暂无可录入批次，请联系老师或管理员" />
        <div v-else-if="!batchItems.length" class="py-24px">
          <ElEmpty description="当前批次暂无可录入项目" />
        </div>
        <div v-else class="self-entry__grid">
          <div v-for="item in batchItems" :key="item.value" class="self-entry__item">
            <div class="self-entry__item-head">
              <span>{{ item.label }}</span>
              <ElIcon
                v-if="item.help_lines?.length"
                class="self-entry__question"
                @click="openRuleDialog(item)"
              >
                <QuestionFilled />
              </ElIcon>
            </div>
            <ElInput v-model="rawScores[item.value]" :placeholder="getScoreInputPlaceholder(item)" clearable />
          </div>
        </div>

        <div class="self-entry__footer">
          <ElButton type="primary" size="large" :loading="submitting" @click="submit">
            提交成绩
          </ElButton>
        </div>
      </ElCard>
    </div>

    <ElDialog v-model="ruleDialogVisible" :title="`${ruleDialogTitle}得分计算规则`" width="720px">
      <div v-if="ruleDialogLines.length" class="self-entry__rules">
        <div v-for="line in ruleDialogLines" :key="line" class="self-entry__rule-line">{{ line }}</div>
      </div>
      <ElEmpty v-else description="该项目暂无规则说明" />
    </ElDialog>
  </ContentWrap>
</template>

<style scoped>
.self-entry {
  min-height: 100%;
  padding: 2px;
}

.self-entry__hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 24px;
  align-items: end;
  padding: 34px;
  border-radius: 30px;
  color: #f8fafc;
  background:
    radial-gradient(circle at 18% 0%, rgba(45, 212, 191, 0.38), transparent 34%),
    linear-gradient(135deg, #061526 0%, #0b2a3f 52%, #102d24 100%);
  box-shadow: 0 28px 64px rgba(8, 20, 38, 0.18);
}

.self-entry__tag {
  border: 0;
  background: rgba(45, 212, 191, 0.22);
}

.self-entry__hero h1 {
  margin: 16px 0 12px;
  font-size: clamp(30px, 4vw, 54px);
  line-height: 1.05;
  font-weight: 900;
}

.self-entry__hero p {
  max-width: 720px;
  margin: 0;
  color: rgba(226, 232, 240, 0.86);
  font-size: 16px;
  line-height: 1.8;
}

.self-entry__profile {
  display: grid;
  gap: 8px;
  padding: 20px;
  border: 1px solid rgba(226, 232, 240, 0.16);
  border-radius: 24px;
  background: rgba(15, 23, 42, 0.36);
  backdrop-filter: blur(16px);
}

.self-entry__profile span,
.self-entry__profile em {
  color: rgba(226, 232, 240, 0.72);
  font-style: normal;
}

.self-entry__profile strong {
  color: #fff;
  font-size: 26px;
}

.self-entry__panel {
  margin-top: 18px;
  border: 0;
  border-radius: 24px;
}

.self-entry__toolbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 22px;
}

.self-entry__label {
  margin-bottom: 8px;
  color: #64748b;
  font-size: 13px;
}

.self-entry__select {
  width: min(520px, 72vw);
}

.self-entry__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.self-entry__item {
  padding: 16px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff, #f8fafc);
}

.self-entry__item-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
  font-weight: 700;
  color: #0f172a;
}

.self-entry__question {
  color: var(--el-color-primary);
  cursor: pointer;
}

.self-entry__footer {
  margin-top: 24px;
  text-align: center;
}

.self-entry__footer .el-button {
  width: 180px;
  border: 0;
  border-radius: 999px;
  background: linear-gradient(135deg, #14b8a6, #2563eb);
}

.self-entry__rules {
  display: grid;
  gap: 8px;
  max-height: 60vh;
  overflow: auto;
}

.self-entry__rule-line {
  padding: 10px 12px;
  border-radius: 12px;
  background: #f8fafc;
  color: #334155;
}

@media (max-width: 900px) {
  .self-entry__hero {
    grid-template-columns: 1fr;
    padding: 24px;
  }

  .self-entry__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .self-entry__hero {
    border-radius: 22px;
  }

  .self-entry__toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .self-entry__select {
    width: 100%;
  }

  .self-entry__grid {
    grid-template-columns: 1fr;
  }
}
</style>
