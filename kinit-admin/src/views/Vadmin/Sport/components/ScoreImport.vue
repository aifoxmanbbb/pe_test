<script setup lang="ts">
import { computed, ref, type PropType } from 'vue'
import {
  ElAlert,
  ElButton,
  ElCol,
  ElLink,
  ElMessage,
  ElPopconfirm,
  ElRow,
  ElTable,
  ElTableColumn,
  ElTooltip,
  ElUpload,
  type UploadProps
} from 'element-plus'

type ApiResult = Promise<IResponse<any>>
type DownloadTemplateResult = Promise<any>

const props = defineProps({
  batchId: {
    type: [Number, String] as PropType<number | string | null | undefined>,
    default: undefined
  },
  batchLabel: {
    type: String,
    default: ''
  },
  bizName: {
    type: String,
    required: true
  },
  downloadTemplateApi: {
    type: Function as PropType<(params?: Record<string, any>) => DownloadTemplateResult>,
    required: true
  },
  importScoresApi: {
    type: Function as PropType<(data: FormData) => ApiResult>,
    required: true
  },
  confirmScoresApi: {
    type: Function as PropType<(data: Record<string, any>) => ApiResult>,
    required: true
  }
})

const emit = defineEmits(['success'])

const importFile = ref<File | null>(null)
const uploadRows = ref<Recordable[]>([])
const previewRows = ref<Recordable[]>([])
const resultRows = ref<Recordable[]>([])
const parsing = ref(false)
const confirming = ref(false)

const selectedBatchText = computed(() => props.batchLabel || String(props.batchId || ''))

const beforeFileUpload: UploadProps['beforeUpload'] = (rawFile) => {
  const isExcel =
    rawFile.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
    rawFile.name.toLowerCase().endsWith('.xlsx')
  const isLtSize = rawFile.size / 1024 / 1024 < 10

  if (!isExcel) ElMessage.error('上传文件必须是 XLSX 格式')
  if (!isLtSize) ElMessage.error('上传文件大小不能超过 10MB')
  return isExcel && isLtSize
}

const resetUpload = () => {
  importFile.value = null
  uploadRows.value = []
  previewRows.value = []
}

const handleUpload = async (file: any) => {
  if (!props.batchId) {
    ElMessage.warning('请先选择批次')
    return
  }
  importFile.value = file.file
  uploadRows.value = [
    {
      filename: file.file.name,
      filesize: `${(file.file.size / 1024).toFixed(1)}KB`,
      status: '已选择'
    }
  ]

  parsing.value = true
  const formData = new FormData()
  formData.append('batch_id', String(props.batchId))
  formData.append('file', file.file)
  try {
    const res = await props.importScoresApi(formData)
    if (!res) {
      resetUpload()
      return
    }
    previewRows.value = Array.isArray(res?.data) ? res.data : []
    ElMessage.success(`解析完成，共 ${previewRows.value.length} 条成绩`)
  } finally {
    parsing.value = false
  }
}

const downloadTemplate = async () => {
  if (!props.batchId) {
    ElMessage.warning('请先选择批次')
    return
  }
  ElMessage.info('正在下载模板')
  const res = await props.downloadTemplateApi({ batch_id: Number(props.batchId) })
  const blob = res?.data
  if (!blob) return
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.style.display = 'none'
  a.href = url
  a.download = `${props.bizName}成绩导入模板.xlsx`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const handleConfirm = async () => {
  if (!props.batchId) {
    ElMessage.warning('请先选择批次')
    return
  }
  if (!previewRows.value.length) {
    ElMessage.warning('请先上传并解析成绩文件')
    return
  }

  confirming.value = true
  try {
    const res = await props.confirmScoresApi({
      batch_id: Number(props.batchId),
      validate_import: true,
      scores: previewRows.value
    })
    if (!res) return
    const count = Number(res?.data?.upsert_count ?? previewRows.value.length)
    resultRows.value.unshift({
      filename: importFile.value?.name || '-',
      batch: selectedBatchText.value,
      count
    })
    ElMessage.success(`成功导入 ${count} 条成绩`)
    resetUpload()
    emit('success')
  } finally {
    confirming.value = false
  }
}
</script>

<template>
  <div class="score-import">
    <ElAlert
      type="info"
      :closable="false"
      show-icon
      class="score-import__batch"
      :title="`当前导入批次：${selectedBatchText || '未选择批次'}`"
    />

    <div class="score-import__steps">
      <span>导入步骤：</span>
      <ol>
        <li>
          <ElLink type="primary" @click="downloadTemplate">下载最新成绩导入模板</ElLink>
        </li>
        <li>按模板填写学生、项目和成绩数据。</li>
        <li>上传 XLSX 文件，系统会先解析并展示预览。</li>
        <li>确认无误后点击“确认导入”。</li>
      </ol>
    </div>

    <ElRow :gutter="10" class="score-import__actions">
      <ElCol :span="1.5">
        <ElUpload
          action=""
          :http-request="handleUpload"
          :show-file-list="false"
          :before-upload="beforeFileUpload"
          accept=".xlsx"
          :disabled="uploadRows.length > 0 || parsing"
        >
          <ElTooltip effect="dark" content="只支持上传 XLSX 文件" placement="top">
            <ElButton type="primary" :disabled="uploadRows.length > 0 || parsing" :loading="parsing">
              上传文件
            </ElButton>
          </ElTooltip>
        </ElUpload>
      </ElCol>
      <ElCol :span="1.5">
        <ElButton
          type="primary"
          :disabled="!previewRows.length"
          :loading="confirming"
          @click="handleConfirm"
        >
          确认导入
        </ElButton>
      </ElCol>
    </ElRow>

    <ElTable :data="uploadRows" border class="score-import__table">
      <ElTableColumn prop="filename" label="文件名称" min-width="180" />
      <ElTableColumn prop="filesize" label="文件大小" width="120" align="center" />
      <ElTableColumn prop="status" label="状态" width="120" align="center" />
      <ElTableColumn fixed="right" label="操作" width="110" align="center">
        <template #default>
          <ElPopconfirm title="确认删除当前文件？" @confirm="resetUpload">
            <template #reference>
              <ElButton link type="primary">删除</ElButton>
            </template>
          </ElPopconfirm>
        </template>
      </ElTableColumn>
    </ElTable>

    <div class="score-import__section-title">解析预览（{{ previewRows.length }} 条）</div>
    <ElTable :data="previewRows" border height="260" class="score-import__table">
      <ElTableColumn prop="student_no" label="学号" width="120" />
      <ElTableColumn prop="student_name" label="姓名" width="100" />
      <ElTableColumn prop="gender" label="性别" width="80" />
      <ElTableColumn prop="school_name" label="学校" min-width="140" />
      <ElTableColumn prop="grade_name" label="年级" width="100" />
      <ElTableColumn prop="class_name" label="班级" width="110" />
      <ElTableColumn prop="item_name" label="项目名称" min-width="140" />
      <ElTableColumn prop="raw_score" label="成绩" width="100" />
    </ElTable>

    <div class="score-import__section-title">导入结果</div>
    <ElTable :data="resultRows" border class="score-import__table">
      <ElTableColumn prop="filename" label="文件名称" min-width="180" />
      <ElTableColumn prop="batch" label="导入批次" min-width="180" />
      <ElTableColumn prop="count" label="成功数量" width="120" align="center" />
    </ElTable>
  </div>
</template>

<style scoped>
.score-import__batch {
  margin-bottom: 12px;
}

.score-import__steps {
  margin-bottom: 14px;
  color: var(--el-text-color-regular);
}

.score-import__steps ol {
  margin: 8px 0 0;
  padding-left: 22px;
}

.score-import__steps li + li {
  margin-top: 6px;
}

.score-import__actions {
  margin-bottom: 12px;
}

.score-import__table {
  width: 100%;
  margin-top: 10px;
}

.score-import__section-title {
  margin-top: 14px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}
</style>
