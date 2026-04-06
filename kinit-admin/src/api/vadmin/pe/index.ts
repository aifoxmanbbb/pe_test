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
