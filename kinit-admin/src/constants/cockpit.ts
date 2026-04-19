import bg1 from '@/assets/imgs/bg-1.webp'
import bg2 from '@/assets/imgs/bg-2.webp'
import bg3 from '@/assets/imgs/bg-3.webp'
import bg4 from '@/assets/imgs/bg-4.webp'
import bg5 from '@/assets/imgs/bg-5.webp'
import bg6 from '@/assets/imgs/bg-6.webp'
import bg7 from '@/assets/imgs/bg-7.webp'
import bg8 from '@/assets/imgs/bg-8.webp'
import bgLogin from '@/assets/imgs/bg-login.webp'

export type CockpitRole = 'admin' | 'leader' | 'teacher' | 'student'

export const analysisHeroImages = {
  peOverview: bg1,
  peStudent: bg2,
  peClass: bg3,
  peGrade: bg4,
  fitnessOverview: bg5,
  fitnessStudent: bg6,
  fitnessClass: bg7,
  fitnessGrade: bg8,
  myScores: bgLogin
}

export const cockpitRoleMeta: Record<
  CockpitRole,
  {
    label: string
    headline: string
    desc: string
    image: string
    theme: { bg: string; text: string; hover: string }
  }
> = {
  admin: {
    label: '管理员驾驶舱',
    headline: '全域体育数据运行中枢',
    desc: '统一看批次、覆盖、预警与高水平区间，适合总控、投屏和日常巡检。',
    image: bg5,
    theme: { bg: '#081426', text: '#e6f4ff', hover: 'rgba(45, 212, 191, 0.16)' }
  },
  leader: {
    label: '校长领导驾驶舱',
    headline: '学校体育质量态势总览',
    desc: '聚焦学校层级的达标率、均分、风险项和班级梯队，直接支持决策。',
    image: bg7,
    theme: { bg: '#141c32', text: '#eef6ff', hover: 'rgba(96, 165, 250, 0.16)' }
  },
  teacher: {
    label: '老师教练驾驶舱',
    headline: '训练组织与提分效率面板',
    desc: '把近期批次、班级分层和学生表现放到一屏内，便于训练闭环与复盘。',
    image: bg3,
    theme: { bg: '#1d1225', text: '#fff7ed', hover: 'rgba(251, 146, 60, 0.16)' }
  },
  student: {
    label: '学生与家长驾驶舱',
    headline: '个人体育成长与成绩总览',
    desc: '集中查看个人最新体考体测、趋势变化和关键状态，信息只围绕本人展开。',
    image: bg8,
    theme: { bg: '#10233e', text: '#f0f9ff', hover: 'rgba(56, 189, 248, 0.16)' }
  }
}

export const resolveCockpitRole = (user: Record<string, any> | undefined | null): CockpitRole => {
  const roles = Array.isArray(user?.roles) ? user.roles : []
  const roleTexts = roles
    .map((role) => `${String(role?.role_key || '')}|${String(role?.name || '')}`.toLowerCase())
    .join('||')
  const isStaff = Boolean(user?.is_staff)

  if (!isStaff || /学生|家长|parent|student/.test(roleTexts)) {
    return 'student'
  }
  if (/admin|管理员|super/.test(roleTexts)) {
    return 'admin'
  }
  if (/校长|领导|principal|leader/.test(roleTexts)) {
    return 'leader'
  }
  return 'teacher'
}
