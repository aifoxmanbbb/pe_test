<script setup lang="tsx">
import { onMounted, ref } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { ElCard, ElDescriptions, ElDescriptionsItem, ElTag, ElTable, ElTableColumn, ElEmpty, ElRow, ElCol } from 'element-plus'
import { getPeStudentAnalysisSelfApi } from '@/api/vadmin/pe'
import { getFitnessStudentAnalysisSelfApi } from '@/api/vadmin/fitness'

defineOptions({
  name: 'MyScores'
})

const peData = ref<any>(null)
const fitnessData = ref<any>(null)
const loading = ref(false)

const loadData = async () => {
  loading.value = true
  const [peRes, fitnessRes] = await Promise.all([
    getPeStudentAnalysisSelfApi().catch(() => null),
    getFitnessStudentAnalysisSelfApi().catch(() => null)
  ])
  if (peRes) peData.value = peRes.data
  if (fitnessRes) fitnessData.value = fitnessRes.data
  loading.value = false
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <ContentWrap>
    <div v-if="loading" class="text-center p-20px text-gray-400">正在加载成绩数据...</div>
    <div v-else-if="!peData && !fitnessData">
      <ElEmpty description="暂无成绩信息，请联系老师或管理员" />
    </div>
    <div v-else>
      <!-- 基本信息 -->
      <ElCard shadow="never" class="mb-20px" header="个人档案">
        <ElDescriptions v-if="peData?.profile" :column="4" border>
          <ElDescriptionsItem label="姓名">{{ peData.profile.student_name }}</ElDescriptionsItem>
          <ElDescriptionsItem label="性别">{{ peData.profile.gender }}</ElDescriptionsItem>
          <ElDescriptionsItem label="学号">{{ peData.profile.student_no }}</ElDescriptionsItem>
          <ElDescriptionsItem label="学段">{{ peData.profile.exam_type }}</ElDescriptionsItem>
          <ElDescriptionsItem label="学校" :span="2">{{ peData.profile.school }}</ElDescriptionsItem>
          <ElDescriptionsItem label="班级" :span="2">{{ peData.profile.grade }} {{ peData.profile.class_name }}</ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>

      <ElRow :gutter="20">
        <!-- 体考成绩 -->
        <ElCol :span="12">
          <ElCard shadow="never" header="体考成绩明细 (PE)">
            <ElTable v-if="peData?.detail_list" :data="peData.detail_list" border stripe>
              <ElTableColumn prop="batch_name" label="测试批次" min-width="150" />
              <ElTableColumn prop="total_score" label="总分" width="80" align="center" />
              <ElTableColumn label="状态" width="100" align="center">
                <template #default="{ row }">
                  <ElTag :type="row.pass_state ? 'success' : 'danger'">
                    {{ row.pass_state ? '及格' : '不及格' }}
                  </ElTag>
                </template>
              </ElTableColumn>
            </ElTable>
            <ElEmpty v-else description="暂无体考成绩" />
          </ElCard>
        </ElCol>

        <!-- 体测成绩 -->
        <ElCol :span="12">
          <ElCard shadow="never" header="体测成绩明细 (Fitness)">
            <ElTable v-if="fitnessData?.detail_list" :data="fitnessData.detail_list" border stripe>
              <ElTableColumn prop="batch_name" label="测试批次" min-width="150" />
              <ElTableColumn prop="bmi_score" label="BMI" width="80" />
              <ElTableColumn prop="lung_score" label="肺活量" width="80" />
              <ElTableColumn prop="rope_score" label="跳绳" width="80" />
            </ElTable>
            <ElEmpty v-else description="暂无体测成绩" />
          </ElCard>
        </ElCol>
      </ElRow>
    </div>
  </ContentWrap>
</template>
