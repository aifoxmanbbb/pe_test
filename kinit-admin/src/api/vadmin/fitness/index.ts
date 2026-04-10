import request from '@/config/axios'

export const getFitnessOverviewApi = (params?: Record<string, any>): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/fitness/overview', params })
}

export const getFitnessStudentAnalysisApi = (
  params?: Record<string, any>
): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/fitness/analysis/student', params })
}

export const getFitnessStudentAnalysisSelfApi = (
  params?: Record<string, any>
): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/fitness/analysis/student/self', params })
}

export const getFitnessClassAnalysisApi = (
  params?: Record<string, any>
): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/fitness/analysis/class', params })
}

export const getFitnessGradeAnalysisApi = (
  params?: Record<string, any>
): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/fitness/analysis/grade', params })
}

export const getFitnessEntryTemplateApi = (): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/fitness/entry/template' })
}

export const getFitnessReportConfigApi = (): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/fitness/report/config' })
}

export const getFitnessStandardListApi = (
  params?: Record<string, any>
): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/fitness/standard/list', params })
}

export const getFitnessBatchOptionsApi = (params?: Record<string, any>): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/fitness/batch/options', params })
}

export const createFitnessBatchApi = (data: Record<string, any>): Promise<IResponse<any>> => {
  return request.post({ url: '/vadmin/fitness/batch', data })
}

export const upsertFitnessScoresApi = (data: Record<string, any>): Promise<IResponse<any>> => {
  return request.post({ url: '/vadmin/fitness/score/upsert', data })
}

export const createFitnessStandardApi = (data: Record<string, any>): Promise<IResponse<any>> => {
  return request.post({ url: '/vadmin/fitness/standard', data })
}

export const getFitnessBatchListApi = (params: Record<string, any>): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/fitness/batch/list', params })
}

export const updateFitnessBatchApi = (
  id: number,
  data: Record<string, any>
): Promise<IResponse<any>> => {
  return request.put({ url: `/vadmin/fitness/batch/${id}`, data })
}

export const deleteFitnessBatchApi = (id: number): Promise<IResponse<any>> => {
  return request.delete({ url: `/vadmin/fitness/batch/${id}` })
}

export const getFitnessStudentOptionsApi = (
  params?: Record<string, any>
): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/fitness/students/options', params })
}

export const exportFitnessReportApi = (params: Record<string, any>): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/fitness/report/export', params })
}

export const importFitnessStandardApi = (data: FormData): Promise<IResponse<any>> => {
  return request.post({
    url: '/vadmin/fitness/standard/import',
    data,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const confirmFitnessStandardApi = (data: Record<string, any>): Promise<IResponse<any>> => {
  return request.post({ url: '/vadmin/fitness/standard/confirm', data })
}

export const importFitnessScoresApi = (data: FormData): Promise<IResponse<any>> => {
  return request.post({
    url: '/vadmin/fitness/score/import',
    data,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const confirmFitnessScoresApi = (data: Record<string, any>): Promise<IResponse<any>> => {
  return request.post({ url: '/vadmin/fitness/score/confirm', data })
}

export const getFitnessBatchItemScoresApi = (params: {
  batch_id: number
  item_code: string
}): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/fitness/score/batch/students', params })
}

export const downloadFitnessScoreTemplateApi = (): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/fitness/score/template' })
}
