import request from '@/config/axios'

export const getPeOverviewApi = (params?: Record<string, any>): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/pe/overview', params })
}

export const getPeStudentAnalysisApi = (params?: Record<string, any>): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/pe/analysis/student', params })
}

export const getPeClassAnalysisApi = (params?: Record<string, any>): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/pe/analysis/class', params })
}

export const getPeGradeAnalysisApi = (params?: Record<string, any>): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/pe/analysis/grade', params })
}

export const getPeEntryTemplateApi = (): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/pe/entry/template' })
}

export const getPeReportConfigApi = (): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/pe/report/config' })
}

export const getPeStandardListApi = (params?: Record<string, any>): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/pe/standard/list', params })
}

export const getPeBatchOptionsApi = (params?: Record<string, any>): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/pe/batch/options', params })
}

export const createPeBatchApi = (data: Record<string, any>): Promise<IResponse<any>> => {
  return request.post({ url: '/vadmin/pe/batch', data })
}

export const upsertPeScoresApi = (data: Record<string, any>): Promise<IResponse<any>> => {
  return request.post({ url: '/vadmin/pe/score/upsert', data })
}

export const createPeStandardApi = (data: Record<string, any>): Promise<IResponse<any>> => {
  return request.post({ url: '/vadmin/pe/standard', data })
}

export const getPeBatchListApi = (params: Record<string, any>): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/pe/batch/list', params })
}

export const updatePeBatchApi = (id: number, data: Record<string, any>): Promise<IResponse<any>> => {
  return request.put({ url: `/vadmin/pe/batch/${id}`, data })
}

export const deletePeBatchApi = (id: number): Promise<IResponse<any>> => {
  return request.delete({ url: `/vadmin/pe/batch/${id}` })
}

export const getPeStudentOptionsApi = (params?: Record<string, any>): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/pe/students/options', params })
}

export const exportPeReportApi = (params: Record<string, any>): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/pe/report/export', params })
}

export const importPeStandardApi = (data: FormData): Promise<IResponse<any>> => {
  return request.post({
    url: '/vadmin/pe/standard/import',
    data,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const confirmPeStandardApi = (data: Record<string, any>): Promise<IResponse<any>> => {
  return request.post({ url: '/vadmin/pe/standard/confirm', data })
}

export const importPeScoresApi = (data: FormData): Promise<IResponse<any>> => {
  return request.post({
    url: '/vadmin/pe/score/import',
    data,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const confirmPeScoresApi = (data: Record<string, any>): Promise<IResponse<any>> => {
  return request.post({ url: '/vadmin/pe/score/confirm', data })
}

export const getPeBatchItemScoresApi = (params: {
  batch_id: number
  item_code: string
}): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/pe/score/batch/students', params })
}

export const downloadPeScoreTemplateApi = (): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/pe/score/template' })
}
