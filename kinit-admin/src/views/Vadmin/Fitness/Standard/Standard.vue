<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import type { FormSchema } from '@/components/Form'
import { ElCard } from 'element-plus'
import { Table, TableColumn } from '@/components/Table'
import { getFitnessStandardListApi } from '@/api/vadmin/fitness'

defineOptions({
  name: 'FitnessStandard'
})

const searchParams = ref<Record<string, any>>({})
const searchSchema = reactive<FormSchema[]>([
  {
    field: 'region',
    label: '地区',
    component: 'Select',
    componentProps: {
      placeholder: '请选择地区',
      options: [
        { label: '重庆市', value: 'CQ' },
        { label: '四川省', value: 'SC' }
      ]
    }
  },
  {
    field: 'year',
    label: '年份',
    component: 'Select',
    componentProps: {
      placeholder: '请选择年份',
      options: [
        { label: '2026', value: 2026 },
        { label: '2025', value: 2025 }
      ]
    }
  },
  {
    field: 'stage',
    label: '学段',
    component: 'Select',
    componentProps: {
      placeholder: '请选择学段',
      options: [
        { label: '初中', value: 'mid' },
        { label: '高中', value: 'high' }
      ]
    }
  }
])

const standardList = ref<any[]>([])

const columns = reactive<TableColumn[]>([
  { field: 'name', label: '标准名称', minWidth: '220px' },
  { field: 'region', label: '地区', width: '110px' },
  { field: 'year', label: '年份', width: '90px' },
  { field: 'stage', label: '学段', width: '90px' },
  { field: 'version', label: '标准版本号', width: '130px' },
  { field: 'status', label: '状态', width: '90px' }
])

const setSearchParams = (params: Record<string, any>) => {
  searchParams.value = params
  loadList()
}

const loadList = async () => {
  const res = await getFitnessStandardListApi(searchParams.value).catch(() => null)
  if (!res) return
  standardList.value = Array.isArray(res.data) ? res.data : []
}

onMounted(() => {
  loadList()
})
</script>

<template>
  <ContentWrap>
    <Search :schema="searchSchema" @search="setSearchParams" @reset="setSearchParams" />

    <ElCard shadow="never" class="mt-10px" header="体测标准中心">
      <p>支持导入 PDF、导入表格、手工录入；识别结果必须人工确认后发布。</p>
      <p>标准详情弹窗显示：项目、性别、分值段（成绩->分值）、及格/优秀/满分阈值、计分模式。</p>
      <Table :columns="columns" :data="standardList" :pagination="false" class="mt-10px" />
      <div class="text-12px text-gray-500 mt-8px">当前筛选：{{ searchParams }}</div>
    </ElCard>
  </ContentWrap>
</template>
