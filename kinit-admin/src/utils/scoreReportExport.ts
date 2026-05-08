import { ElMessage } from 'element-plus'

type ExportApi = (params: Record<string, any>) => Promise<IResponse<any>>

const compactParams = (params: Record<string, any>) => {
  return Object.entries(params || {}).reduce<Record<string, any>>((acc, [key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      acc[key] = value
    }
    return acc
  }, {})
}

export const openScoreReport = async (
  exportApi: ExportApi,
  params: Record<string, any>,
  bizName: string,
  missingBatchMessage?: string
) => {
  const query = compactParams(params)
  if (!query.batch_id) {
    ElMessage.warning(missingBatchMessage || `请先选择${bizName}批次`)
    return
  }

  try {
    const res = await exportApi(query)
    const url = res?.data?.url
    if (!url) {
      ElMessage.error('暂无可导出的成绩数据')
      return
    }
    ElMessage.success('导出文件已生成')
    window.open(url)
  } catch (error: any) {
    ElMessage.error(error?.message || '导出失败')
  }
}
