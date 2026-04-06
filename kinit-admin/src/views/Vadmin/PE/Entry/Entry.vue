<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import type { FormSchema } from '@/components/Form'
import { ElCard, ElTag, ElTabs, ElTabPane } from 'element-plus'
import { getPeEntryTemplateApi } from '@/api/vadmin/pe'

defineOptions({
  name: 'PEEntry'
})

const examTypeTab = ref('mid')
const searchParams = ref<Record<string, any>>({})
const searchSchema = reactive<FormSchema[]>([
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
        { label: '张三', value: 1 },
        { label: '李四', value: 2 }
      ]
    }
  }
])

const templateData = ref({
  items: [] as string[],
  calc_policy: '支持仅录入成绩，自动计算分值',
  conflict_policy: '就低不就高'
})

const itemText = computed(() => templateData.value.items.join('、'))

const setSearchParams = (params: Record<string, any>) => {
  searchParams.value = params
}

const loadTemplate = async () => {
  const res = await getPeEntryTemplateApi().catch(() => null)
  if (!res) return
  templateData.value = Object.assign(templateData.value, res.data || {})
}

onMounted(() => {
  loadTemplate()
})
</script>

<template>
  <ContentWrap>
    <ElTabs v-model="examTypeTab" class="mb-10px">
      <ElTabPane label="初中" name="mid" />
      <ElTabPane label="高中" name="high" />
    </ElTabs>

    <Search :schema="searchSchema" @search="setSearchParams" @reset="setSearchParams" />

    <ElCard shadow="never" class="mt-10px" header="体考成绩录入（标准版本驱动）">
      <p>
        录入规则：<ElTag type="warning" class="mx-4px">{{ templateData.calc_policy }}</ElTag>
        <ElTag type="danger" class="mx-4px">冲突策略：{{ templateData.conflict_policy }}</ElTag>
      </p>
      <p>录入区域：{{ itemText }}</p>
      <div class="text-12px text-gray-500">当前筛选：{{ searchParams }}</div>
    </ElCard>
  </ContentWrap>
</template>
