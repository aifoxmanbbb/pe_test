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

export const getPeBatchOptionsApi = (): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/pe/batch/options' })
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
