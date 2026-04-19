import request from '@/config/axios'

// ─── 选项接口 ─────────────────────────────────────────────
export const getSchoolOptionsApi = (params?: any): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/sport/options/schools', params })
}

export const getGradeOptionsApi = (params?: any): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/sport/options/grades', params })
}

export const getClassOptionsApi = (params?: any): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/sport/options/classes', params })
}

export const getSchoolLeaderOptionsApi = (): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/sport/options/users/leaders' })
}

export const getTeacherCoachOptionsApi = (): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/sport/options/users/coaches' })
}

export const getStandardItemOptionsApi = (params: { standard_id: number }): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/sport/options/standard/items', params })
}

// ─── 学校管理 ─────────────────────────────────────────────
export const getSchoolListApi = (params?: any): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/sport/school/list', params })
}

export const createSchoolApi = (data: any): Promise<IResponse<any>> => {
  return request.post({ url: '/vadmin/sport/school', data })
}

export const updateSchoolApi = (id: number, data: any): Promise<IResponse<any>> => {
  return request.put({ url: `/vadmin/sport/school/${id}`, data })
}

// ─── 年级管理 ─────────────────────────────────────────────
export const getGradeListApi = (params?: any): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/sport/grade/list', params })
}

export const createGradeApi = (data: any): Promise<IResponse<any>> => {
  return request.post({ url: '/vadmin/sport/grade', data })
}

export const updateGradeApi = (id: number, data: any): Promise<IResponse<any>> => {
  return request.put({ url: `/vadmin/sport/grade/${id}`, data })
}

// ─── 班级管理 ─────────────────────────────────────────────
export const getClassListApi = (params?: any): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/sport/class/list', params })
}

export const createClassApi = (data: any): Promise<IResponse<any>> => {
  return request.post({ url: '/vadmin/sport/class', data })
}

export const updateClassApi = (id: number, data: any): Promise<IResponse<any>> => {
  return request.put({ url: `/vadmin/sport/class/${id}`, data })
}

// ─── 学生管理 ─────────────────────────────────────────────
export const getStudentListApi = (params?: any): Promise<IResponse<any>> => {
  return request.get({ url: '/vadmin/sport/student/list', params })
}

export const createStudentApi = (data: any): Promise<IResponse<any>> => {
  return request.post({ url: '/vadmin/sport/student', data })
}

export const updateStudentApi = (id: number, data: any): Promise<IResponse<any>> => {
  return request.put({ url: `/vadmin/sport/student/${id}`, data })
}
