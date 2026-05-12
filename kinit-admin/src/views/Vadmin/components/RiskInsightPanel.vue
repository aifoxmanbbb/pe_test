<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElButton, ElCard, ElCol, ElDialog, ElEmpty, ElRow, ElTable, ElTableColumn, ElTag } from 'element-plus'

const props = defineProps({
  data: {
    type: Object,
    default: () => ({})
  },
  mode: {
    type: String,
    default: 'overview'
  }
})

const riskKpi = computed(() => props.data?.risk_kpi || {})
const gradeRisks = computed(() => props.data?.grade_risks || [])
const classRisks = computed(() => props.data?.class_risks || [])
const itemRisks = computed(() => props.data?.item_risks || [])
const studentRisks = computed(() => props.data?.student_risks || [])
const failRecords = computed(() => props.data?.fail_records || [])
const hasRisk = computed(() => Number(riskKpi.value.fail_record_count || 0) > 0)
const detailVisible = ref(false)
const detailTitle = ref('不及格人员与项目明细')
const detailFilters = ref<Record<string, any>>({})

const showGrade = computed(() => ['overview'].includes(props.mode))
const showClass = computed(() => ['overview', 'grade'].includes(props.mode))
const showItem = computed(() => ['overview', 'grade', 'class', 'student'].includes(props.mode))
const showStudent = computed(() => ['class', 'student'].includes(props.mode))
const filteredFailRecords = computed(() => {
  const filters = detailFilters.value
  return failRecords.value.filter((row: any) => {
    if (filters.grade_name && row.grade_name !== filters.grade_name) return false
    if (filters.class_name && row.class_name !== filters.class_name) return false
    if (filters.item_code && row.item_code !== filters.item_code) return false
    if (filters.student_no && row.student_no !== filters.student_no) return false
    return true
  })
})

const openDetails = (title: string, filters: Record<string, any> = {}) => {
  detailTitle.value = title
  detailFilters.value = filters
  detailVisible.value = true
}
</script>

<template>
  <section class="risk-panel">
    <div class="risk-panel__head">
      <div>
        <div class="risk-panel__eyebrow">风险定位</div>
        <h3>不及格短板排查</h3>
      </div>
      <ElTag :type="hasRisk ? 'danger' : 'success'" effect="dark">
        {{ hasRisk ? '存在短板' : '暂无不及格' }}
      </ElTag>
    </div>

    <ElRow :gutter="12" class="risk-panel__kpis">
      <ElCol :xs="12" :sm="12" :md="6">
        <div class="risk-kpi">
          <span>不及格学生</span>
          <strong>{{ riskKpi.fail_student_count || 0 }}</strong>
        </div>
      </ElCol>
      <ElCol :xs="12" :sm="12" :md="6">
        <div class="risk-kpi">
          <span>不及格记录</span>
          <strong>{{ riskKpi.fail_record_count || 0 }}</strong>
        </div>
      </ElCol>
      <ElCol :xs="12" :sm="12" :md="6">
        <div class="risk-kpi">
          <span>主要班级</span>
          <strong>{{ riskKpi.top_class || '-' }}</strong>
        </div>
      </ElCol>
      <ElCol :xs="12" :sm="12" :md="6">
        <div class="risk-kpi">
          <span>主要项目</span>
          <strong>{{ riskKpi.top_item || '-' }}</strong>
        </div>
      </ElCol>
    </ElRow>

    <ElEmpty v-if="!hasRisk" description="当前范围内没有单项不及格记录" />

    <template v-else>
      <ElRow :gutter="12" class="risk-panel__tables">
        <ElCol v-if="showGrade" :xs="24" :md="12">
          <ElCard shadow="never" class="risk-table-card">
            <div class="risk-table-title">哪些年级拉低水平</div>
            <ElTable :data="gradeRisks.slice(0, 8)" size="small" stripe @row-click="(row: any) => openDetails(`${row.grade_name} 不及格明细`, { grade_name: row.grade_name })">
              <ElTableColumn prop="grade_name" label="年级" min-width="100" />
              <ElTableColumn prop="fail_student_count" label="不及格人数" width="105" align="center" />
              <ElTableColumn prop="fail_record_count" label="不及格项" width="90" align="center" />
              <ElTableColumn prop="top_fail_item" label="主要项目" min-width="120" />
            </ElTable>
          </ElCard>
        </ElCol>

        <ElCol v-if="showClass" :xs="24" :md="12">
          <ElCard shadow="never" class="risk-table-card">
            <div class="risk-table-title">哪些班级拉低水平</div>
            <ElTable :data="classRisks.slice(0, 8)" size="small" stripe @row-click="(row: any) => openDetails(`${row.class_name} 不及格明细`, { class_name: row.class_name })">
              <ElTableColumn prop="class_name" label="班级" min-width="100" />
              <ElTableColumn prop="fail_student_count" label="不及格人数" width="105" align="center" />
              <ElTableColumn prop="fail_record_count" label="不及格项" width="90" align="center" />
              <ElTableColumn prop="top_fail_item" label="主要项目" min-width="120" />
            </ElTable>
          </ElCard>
        </ElCol>

        <ElCol v-if="showItem" :xs="24" :md="12">
          <ElCard shadow="never" class="risk-table-card">
            <div class="risk-table-title">哪些项目拉低水平</div>
            <ElTable :data="itemRisks.filter((i: any) => i.fail_record_count > 0).slice(0, 8)" size="small" stripe @row-click="(row: any) => openDetails(`${row.item_name} 不及格明细`, { item_code: row.item_code })">
              <ElTableColumn prop="item_name" label="项目" min-width="120" />
              <ElTableColumn prop="fail_student_count" label="不及格人数" width="105" align="center" />
              <ElTableColumn prop="avg_score" label="平均分" width="90" align="center" />
              <ElTableColumn prop="min_score" label="最低分" width="90" align="center" />
            </ElTable>
          </ElCard>
        </ElCol>

        <ElCol v-if="showStudent" :xs="24" :md="12">
          <ElCard shadow="never" class="risk-table-card">
            <div class="risk-table-title">哪些学生拉低水平</div>
            <ElTable :data="studentRisks.slice(0, 8)" size="small" stripe @row-click="(row: any) => openDetails(`${row.student_name} 不及格项目`, { student_no: row.student_no })">
              <ElTableColumn prop="student_name" label="学生" min-width="90" />
              <ElTableColumn prop="class_name" label="班级" min-width="90" />
              <ElTableColumn prop="fail_item_count" label="不及格项" width="90" align="center" />
              <ElTableColumn prop="lowest_item" label="最低项目" min-width="120" />
            </ElTable>
          </ElCard>
        </ElCol>
      </ElRow>

      <div class="risk-panel__actions">
        <ElButton type="danger" plain @click="openDetails('全部不及格人员与项目明细')">
          查看全部不及格明细
        </ElButton>
      </div>

      <ElDialog v-model="detailVisible" :title="detailTitle" width="960px" class="risk-detail-dialog">
        <ElTable :data="filteredFailRecords" size="small" stripe max-height="560">
          <ElTableColumn prop="grade_name" label="年级" min-width="90" />
          <ElTableColumn prop="class_name" label="班级" min-width="90" />
          <ElTableColumn prop="student_name" label="学生" min-width="90" />
          <ElTableColumn prop="student_no" label="学号" min-width="110" />
          <ElTableColumn prop="item_name" label="不及格项目" min-width="130" />
          <ElTableColumn prop="raw_score" label="成绩" width="90" align="center" />
          <ElTableColumn prop="score_value" label="分值" width="90" align="center" />
        </ElTable>
      </ElDialog>
    </template>
  </section>
</template>

<style scoped>
.risk-panel {
  margin-bottom: 14px;
  padding: 14px;
  border: 1px solid rgba(245, 108, 108, 0.18);
  border-radius: 8px;
  background: linear-gradient(180deg, rgba(255, 247, 247, 0.96), rgba(255, 255, 255, 0.98));
}

.risk-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.risk-panel__eyebrow {
  color: #f56c6c;
  font-size: 12px;
  font-weight: 700;
}

.risk-panel h3 {
  margin: 2px 0 0;
  color: #1f2937;
  font-size: 18px;
}

.risk-panel__kpis,
.risk-panel__tables {
  row-gap: 12px;
  margin-bottom: 12px;
}

.risk-panel__tables :deep(.el-table__row) {
  cursor: pointer;
}

.risk-kpi {
  min-height: 68px;
  padding: 12px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid rgba(148, 163, 184, 0.22);
}

.risk-kpi span {
  display: block;
  color: #6b7280;
  font-size: 12px;
}

.risk-kpi strong {
  display: block;
  margin-top: 6px;
  color: #f56c6c;
  font-size: 20px;
}

.risk-table-card {
  border-radius: 8px;
}

.risk-table-title {
  margin-bottom: 10px;
  color: #111827;
  font-size: 15px;
  font-weight: 700;
}

.risk-panel__actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 4px;
}

.risk-detail-dialog :deep(.el-dialog__body) {
  padding-top: 8px;
}
</style>
