import request from '@/config/axios'

export const getFitnessOverviewApi = (params?: Record<string, any>): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/fitness/overview', params })
}

export const getFitnessStudentAnalysisApi = (
  params?: Record<string, any>
): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/fitness/analysis/student', params })
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
