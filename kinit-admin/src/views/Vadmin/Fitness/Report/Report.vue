<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import type { FormSchema } from '@/components/Form'
import { ElCard, ElTag } from 'element-plus'
import { getFitnessReportConfigApi } from '@/api/vadmin/fitness'

defineOptions({
  name: 'FitnessReport'
})

const searchParams = ref<Record<string, any>>({})
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
  }
])

const reportConfig = ref({
  report_types: [] as string[],
  default_fields: [] as string[]
})

const reportTypesText = computed(() => reportConfig.value.report_types.join('、'))

const setSearchParams = (params: Record<string, any>) => {
  searchParams.value = params
}

const loadConfig = async () => {
  const res = await getFitnessReportConfigApi().catch(() => null)
  if (!res) return
  reportConfig.value = Object.assign(reportConfig.value, res.data || {})
}

onMounted(() => {
  loadConfig()
})
</script>

<template>
  <ContentWrap>
    <Search :schema="searchSchema" @search="setSearchParams" @reset="setSearchParams" />

    <ElCard shadow="never" class="mt-10px" header="体测报表中心（同步导出）">
      <p>支持报表类型：{{ reportTypesText }}</p>
      <p>
        默认导出字段：
        <ElTag v-for="field in reportConfig.default_fields" :key="field" class="mr-6px mb-6px">{{
          field
        }}</ElTag>
      </p>
      <p>流程：参数选择 -> 生成报表 -> 同步下载。</p>
      <div class="text-12px text-gray-500">当前筛选：{{ searchParams }}</div>
    </ElCard>
  </ContentWrap>
</template>
