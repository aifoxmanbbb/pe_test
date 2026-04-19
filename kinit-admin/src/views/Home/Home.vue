<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElEmpty, ElProgress } from 'element-plus'
import type { EChartsOption } from 'echarts'
import { ContentWrap } from '@/components/ContentWrap'
import { Echart } from '@/components/Echart'
import { useAuthStore } from '@/store/modules/auth'
import { useHeaderTheme } from '@/hooks/web/useHeaderTheme'
import { getPeBatchOptionsApi, getPeOverviewApi, getPeStudentAnalysisSelfApi } from '@/api/vadmin/pe'
import {
  getFitnessBatchOptionsApi,
  getFitnessOverviewApi,
  getFitnessStudentAnalysisSelfApi
} from '@/api/vadmin/fitness'
import { cockpitRoleMeta, resolveCockpitRole, type CockpitRole } from '@/constants/cockpit'

defineOptions({ name: 'HomeCockpit' })

const authStore = useAuthStore()
const loading = ref(true)
const peSnapshot = ref<any>(null)
const fitnessSnapshot = ref<any>(null)
const peSelfSnapshot = ref<any>(null)
const fitnessSelfSnapshot = ref<any>(null)
const latestPeBatch = ref<{ label: string; stageType: string } | null>(null)
const latestFitnessBatch = ref<{ label: string; stageType: string } | null>(null)
const loadingProgress = ref(18)

const user = computed(() => authStore.getUser as Record<string, any>)
const roleType = computed<CockpitRole>(() => resolveCockpitRole(user.value))
const roleMeta = computed(() => cockpitRoleMeta[roleType.value])
const currentDateText = computed(() =>
  new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  }).format(new Date())
)
const fullDateText = computed(() =>
  new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).format(new Date())
)

const headerThemeMap = Object.fromEntries(
  Object.entries(cockpitRoleMeta).map(([key, value]) => [key, value.theme])
) as Record<string, { bg: string; text: string; hover: string }>
useHeaderTheme(() => roleType.value, headerThemeMap, 'admin')

const accentMap: Record<
  CockpitRole,
  {
    accent: string
    accentSoft: string
    accentStrong: string
    accentWarn: string
  }
> = {
  admin: {
    accent: '#10b981',
    accentSoft: 'rgba(16, 185, 129, 0.18)',
    accentStrong: '#34d399',
    accentWarn: '#f59e0b'
  },
  leader: {
    accent: '#22c55e',
    accentSoft: 'rgba(34, 197, 94, 0.18)',
    accentStrong: '#4ade80',
    accentWarn: '#38bdf8'
  },
  teacher: {
    accent: '#f97316',
    accentSoft: 'rgba(249, 115, 22, 0.18)',
    accentStrong: '#fb923c',
    accentWarn: '#facc15'
  },
  student: {
    accent: '#38bdf8',
    accentSoft: 'rgba(56, 189, 248, 0.18)',
    accentStrong: '#7dd3fc',
    accentWarn: '#34d399'
  }
}

const accentPalette = computed(() => accentMap[roleType.value])

const safeNum = (value: any, digits = 0) => {
  const parsed = Number(value || 0)
  return Number.isFinite(parsed) ? Number(parsed.toFixed(digits)) : 0
}

const formatValue = (value: number, digits = 1) => {
  if (!Number.isFinite(value)) return '0'
  return value.toLocaleString('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits
  })
}

const getBatchValue = (batch: any) => batch?.value ?? batch?.id ?? null

const loadLatestBatch = async (
  fetcher: (params?: Record<string, any>) => Promise<IResponse<any>>,
  stages: string[]
) => {
  for (const stageType of stages) {
    const res = await fetcher({ stage_type: stageType }).catch(() => null)
    const options = res?.data || []
    if (options.length) {
      return {
        stageType,
        batch: options[0]
      }
    }
  }
  return null
}

const peKpi = computed(() => peSnapshot.value?.kpi || {})
const fitnessKpi = computed(() => fitnessSnapshot.value?.kpi || {})
const studentPeStats = computed(() => peSelfSnapshot.value?.stats || {})
const studentFitnessRows = computed(() => fitnessSelfSnapshot.value?.detail_list || [])

const studentFitnessAverage = computed(() => {
  const latest = studentFitnessRows.value[0]
  const values = (latest?.items || []).map((item: any) => Number(item.score_value) || 0)
  return values.length ? values.reduce((sum: number, item: number) => sum + item, 0) / values.length : 0
})

const studentFitnessFullCount = computed(
  () =>
    Number(
      (studentFitnessRows.value[0]?.items || []).filter((item: any) => Number(item.score_value) >= 100)
        .length || 0
    )
)

const overviewMetric = computed(() => {
  if (roleType.value === 'student') {
    return {
      title: '个人综合总览值',
      subtitle: peSelfSnapshot.value?.detail_list?.[0]?.batch_name || '最新个人成绩',
      value: safeNum(studentPeStats.value.latest_total, 1),
      max: 200,
      unit: '分',
      status: '当前成绩概览'
    }
  }
  return {
    title: '体考综合总览值',
    subtitle: latestPeBatch.value?.label || '最新体考批次',
    value: safeNum(peKpi.value.avg_score, 1),
    max: 200,
    unit: '分',
    status: '当前成绩概览'
  }
})

const completionRate = computed(() => {
  if (roleType.value === 'student') {
    return safeNum((overviewMetric.value.value / Math.max(overviewMetric.value.max, 1)) * 100, 1)
  }
  const total = Number(fitnessKpi.value.item_records || 0)
  const fail = Number(fitnessKpi.value.fail_item_records || 0)
  return safeNum(total ? ((total - fail) / total) * 100 : 0, 1)
})

const commandCards = computed(() => {
  if (roleType.value === 'student') {
    return [
      {
        title: '体考总分',
        short: '总分',
        value: safeNum(studentPeStats.value.latest_total, 1),
        unit: '分',
        max: 200,
        tone: accentPalette.value.accent,
        note: peSelfSnapshot.value?.detail_list?.[0]?.batch_name || '暂无体考批次'
      },
      {
        title: '体考批次',
        short: '批次',
        value: Number(peSelfSnapshot.value?.detail_list?.length || 0),
        unit: '次',
        max: Math.max(Number(peSelfSnapshot.value?.detail_list?.length || 0), 5),
        tone: accentPalette.value.accentWarn,
        note: '个人体考记录数'
      },
      {
        title: '体测综合',
        short: '体测',
        value: safeNum(studentFitnessAverage.value, 1),
        unit: '分',
        max: 100,
        tone: '#38bdf8',
        note: studentFitnessRows.value[0]?.batch_name || '暂无体测批次'
      },
      {
        title: '体测批次',
        short: '记录',
        value: Number(studentFitnessRows.value.length || 0),
        unit: '次',
        max: Math.max(Number(studentFitnessRows.value.length || 0), 5),
        tone: '#34d399',
        note: '个人体测记录数'
      },
      {
        title: '满分单项',
        short: '满分',
        value: studentFitnessFullCount.value,
        unit: '项',
        max: Math.max(studentFitnessFullCount.value, 5),
        tone: '#facc15',
        note: '最新体测批次表现'
      }
    ]
  }

  return [
    {
      title: '体考参考',
      short: '参考',
      value: Number(peKpi.value.total_students || 0),
      unit: '人',
      max: Math.max(Number(peKpi.value.total_students || 0), 10),
      tone: accentPalette.value.accent,
      note: latestPeBatch.value?.label || '最新体考批次'
    },
    {
      title: '体考及格率',
      short: '及格',
      value: safeNum(peKpi.value.pass_rate, 1),
      unit: '%',
      max: 100,
      tone: accentPalette.value.accentWarn,
      note: '体考整体达标水平'
    },
    {
      title: '体测记录',
      short: '记录',
      value: Number(fitnessKpi.value.item_records || 0),
      unit: '条',
      max: Math.max(Number(fitnessKpi.value.item_records || 0), 10),
      tone: '#38bdf8',
      note: latestFitnessBatch.value?.label || '最新体测批次'
    },
    {
      title: '预警项目',
      short: '预警',
      value: Number(fitnessKpi.value.fail_item_records || 0),
      unit: '项',
      max: Math.max(Number(fitnessKpi.value.fail_item_records || 0), 10),
      tone: '#ef4444',
      note: '体测未达标项目总量'
    },
    {
      title: '达成面',
      short: '达成',
      value: completionRate.value,
      unit: '%',
      max: 100,
      tone: '#34d399',
      note: '体考体测综合完成面'
    }
  ]
})

const leftCards = computed(() => commandCards.value.slice(0, 2))
const rightCards = computed(() => commandCards.value.slice(2))

const buildMiniDonutOption = (
  value: number,
  max: number,
  color: string,
  unit: string,
  title: string
): EChartsOption => {
  const percent = max > 0 ? Math.min(value / max, 1) : 0
  return {
    animationDuration: 800,
    title: [
      {
        text: formatValue(value, unit === '人' || unit === '条' || unit === '次' || unit === '项' ? 0 : 1),
        left: 'center',
        top: '36%',
        textStyle: { color: '#f8fafc', fontSize: 28, fontWeight: 800, fontFamily: 'Plus Jakarta Sans' }
      },
      {
        text: unit,
        left: 'center',
        top: '60%',
        textStyle: { color, fontSize: 14, fontWeight: 700 }
      },
      {
        text: title,
        left: 'center',
        top: 6,
        textStyle: { color: 'rgba(203,213,225,0.82)', fontSize: 12, fontWeight: 700 }
      }
    ],
    series: [
      {
        type: 'pie',
        radius: ['70%', '84%'],
        center: ['50%', '52%'],
        silent: true,
        label: { show: false },
        data: [
          { value: percent, itemStyle: { color } },
          { value: 1 - percent, itemStyle: { color: 'rgba(148,163,184,0.14)' } }
        ]
      }
    ]
  }
}

const cardChartOptions = computed(() =>
  commandCards.value.map((item) =>
    buildMiniDonutOption(item.value, item.max, item.tone, item.unit, item.title)
  )
)

const overviewRingOption = computed<EChartsOption>(() => {
  const percent = Math.min(overviewMetric.value.value / Math.max(overviewMetric.value.max, 1), 1)
  return {
    animationDuration: 1200,
    title: [
      {
        text: overviewMetric.value.status,
        left: 'center',
        top: '19%',
        textStyle: {
          color: 'rgba(148,163,184,0.72)',
          fontSize: 12,
          fontWeight: 600,
          letterSpacing: 1
        }
      },
      {
        text: formatValue(overviewMetric.value.value, 1),
        left: 'center',
        top: '34%',
        textStyle: {
          color: '#ffffff',
          fontSize: 72,
          fontWeight: 900,
          fontStyle: 'italic',
          fontFamily: 'Plus Jakarta Sans'
        }
      },
      {
        text: overviewMetric.value.unit,
        left: '67%',
        top: '53%',
        textStyle: {
          color: accentPalette.value.accentStrong,
          fontSize: 24,
          fontWeight: 700
        }
      },
      {
        text: overviewMetric.value.title,
        left: 'center',
        top: '66%',
        textStyle: {
          color: '#f8fafc',
          fontSize: 20,
          fontWeight: 700
        }
      }
    ],
    series: [
      {
        type: 'pie',
        radius: ['78%', '86%'],
        center: ['50%', '50%'],
        startAngle: 90,
        clockwise: true,
        silent: true,
        label: { show: false },
        data: [
          {
            value: percent,
            itemStyle: {
              color: accentPalette.value.accent,
              shadowBlur: 26,
              shadowColor: accentPalette.value.accentSoft
            }
          },
          { value: 1 - percent, itemStyle: { color: 'rgba(255,255,255,0.06)' } }
        ]
      }
    ]
  }
})

const combinedTrendOption = computed<EChartsOption>(() => {
  const axisLabelStyle = { color: 'rgba(226,232,240,0.72)' }
  if (roleType.value === 'student') {
    const peTrend = peSelfSnapshot.value?.total_trend || {}
    const fitTrend = fitnessSelfSnapshot.value?.item_state_trend || {}
    return {
      tooltip: { trigger: 'axis' },
      legend: { bottom: 0, textStyle: { color: '#cbd5e1' } },
      grid: { left: 14, right: 12, top: 36, bottom: 34, containLabel: true },
      xAxis: {
        type: 'category',
        data: peTrend.batches || fitTrend.batches || [],
        axisLabel: axisLabelStyle,
        axisLine: { lineStyle: { color: 'rgba(148,163,184,0.16)' } }
      },
      yAxis: {
        type: 'value',
        axisLabel: axisLabelStyle,
        splitLine: { lineStyle: { color: 'rgba(148,163,184,0.08)' } }
      },
      series: [
        {
          name: '体考总分',
          type: 'line',
          smooth: true,
          symbol: 'none',
          data: peTrend.total || [],
          lineStyle: { color: accentPalette.value.accent, width: 4 },
          areaStyle: { color: accentPalette.value.accentSoft }
        },
        {
          name: '体测不达标项',
          type: 'line',
          smooth: true,
          symbol: 'none',
          data: fitTrend.fail_items || [],
          lineStyle: { color: '#38bdf8', width: 3 },
          areaStyle: { color: 'rgba(56,189,248,0.12)' }
        }
      ]
    }
  }

  const peTrend = peSnapshot.value?.batch_trend || {}
  const fitTrend = fitnessSnapshot.value?.item_trend || {}
  const fitnessLine =
    (fitTrend.series || []).reduce(
      (longest: any, item: any) =>
        (item?.values || []).length > (longest?.values || []).length ? item : longest,
      null
    ) || null

  return {
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0, textStyle: { color: '#cbd5e1' } },
    grid: { left: 14, right: 12, top: 36, bottom: 34, containLabel: true },
    xAxis: {
      type: 'category',
      data: peTrend.batches || fitTrend.batches || [],
      axisLabel: axisLabelStyle,
      axisLine: { lineStyle: { color: 'rgba(148,163,184,0.16)' } }
    },
    yAxis: {
      type: 'value',
      axisLabel: axisLabelStyle,
      splitLine: { lineStyle: { color: 'rgba(148,163,184,0.08)' } }
    },
    series: [
      {
        name: '体考均分',
        type: 'line',
        smooth: true,
        symbol: 'none',
        data: peTrend.avg_score || [],
        lineStyle: { color: accentPalette.value.accent, width: 4 },
        areaStyle: { color: accentPalette.value.accentSoft }
      },
      {
        name: fitnessLine?.name || '体测重点项',
        type: 'line',
        smooth: true,
        symbol: 'none',
        data: fitnessLine?.values || [],
        lineStyle: { color: '#38bdf8', width: 3 },
        areaStyle: { color: 'rgba(56,189,248,0.12)' }
      }
    ]
  }
})

const summaryOption = computed<EChartsOption>(() => {
  const peScore =
    roleType.value === 'student'
      ? safeNum(studentPeStats.value.latest_total, 1)
      : safeNum(peKpi.value.avg_score, 1)
  const fitScore =
    roleType.value === 'student'
      ? safeNum(studentFitnessAverage.value, 1)
      : safeNum(completionRate.value, 1)
  const pePass =
    roleType.value === 'student'
      ? safeNum(studentPeStats.value.pass_rate, 1)
      : safeNum(peKpi.value.pass_rate, 1)
  const fitFull =
    roleType.value === 'student'
      ? studentFitnessFullCount.value
      : Number(fitnessKpi.value.full_item_records || 0)

  return {
    radar: {
      indicator: [
        { name: '体考分值', max: 200 },
        { name: '体测达成', max: 100 },
        { name: '体考及格', max: 100 },
        { name: '体测高分', max: Math.max(fitFull || 1, 10) }
      ],
      radius: '58%',
      splitLine: { lineStyle: { color: 'rgba(148,163,184,0.16)' } },
      splitArea: { areaStyle: { color: ['rgba(15,23,42,0.18)', 'rgba(15,23,42,0.04)'] } },
      axisName: { color: '#cbd5e1' }
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: [peScore, fitScore, pePass, fitFull],
            areaStyle: { color: accentPalette.value.accentSoft },
            lineStyle: { color: accentPalette.value.accent, width: 2.5 },
            itemStyle: { color: accentPalette.value.accentStrong }
          }
        ]
      }
    ]
  }
})

const structureOption = computed<EChartsOption>(() => {
  if (roleType.value === 'student') {
    const trend = fitnessSelfSnapshot.value?.item_score_trend || {}
    return {
      tooltip: { trigger: 'axis' },
      legend: { bottom: 0, textStyle: { color: '#cbd5e1' } },
      grid: { left: 10, right: 10, top: 34, bottom: 34, containLabel: true },
      xAxis: {
        type: 'category',
        data: trend.batches || [],
        axisLabel: { color: 'rgba(226,232,240,0.72)' },
        axisLine: { lineStyle: { color: 'rgba(148,163,184,0.16)' } }
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: 'rgba(226,232,240,0.72)' },
        splitLine: { lineStyle: { color: 'rgba(148,163,184,0.08)' } }
      },
      series: (trend.series || []).slice(0, 3).map((item: any, index: number) => ({
        name: item.name,
        type: 'line',
        smooth: true,
        symbol: 'none',
        data: item.values || [],
        lineStyle: {
          width: 2.5,
          color: [accentPalette.value.accent, '#38bdf8', '#facc15'][index % 3]
        }
      }))
    }
  }

  const itemRate = fitnessSnapshot.value?.item_rate || {}
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { bottom: 0, textStyle: { color: '#cbd5e1' } },
    grid: { left: 10, right: 10, top: 34, bottom: 34, containLabel: true },
    xAxis: {
      type: 'category',
      data: itemRate.items || [],
      axisLabel: { color: 'rgba(226,232,240,0.72)', interval: 0, rotate: 18 },
      axisLine: { lineStyle: { color: 'rgba(148,163,184,0.16)' } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: 'rgba(226,232,240,0.72)' },
      splitLine: { lineStyle: { color: 'rgba(148,163,184,0.08)' } }
    },
    series: [
      {
        name: '及格率',
        type: 'bar',
        barWidth: 12,
        data: itemRate.pass_rate || [],
        itemStyle: { color: accentPalette.value.accent, borderRadius: [8, 8, 0, 0] }
      },
      {
        name: '优秀率',
        type: 'bar',
        barWidth: 12,
        data: itemRate.excellent_rate || [],
        itemStyle: { color: '#38bdf8', borderRadius: [8, 8, 0, 0] }
      }
    ]
  }
})

const railHeadline = computed(() => {
  if (roleType.value === 'student') return '个人体育成长监测中枢'
  if (roleType.value === 'admin') return '全域体育考试实时指挥中心'
  if (roleType.value === 'leader') return '学校体育质量决策驾驶舱'
  return '班级训练组织与提分指挥面板'
})

const railDescription = computed(() => {
  if (roleType.value === 'student') return '只围绕本人最新成绩、趋势变化与关键状态自动聚合。'
  if (roleType.value === 'admin') return '集中查看学校体考体测整体表现，快速掌握成绩分布、达标情况和变化趋势。'
  if (roleType.value === 'leader') return '聚焦本校批次、达标率与风险项，帮助领导快速看清学校体育质量变化。'
  return '围绕关联班级训练成效、进步趋势和风险学生进行集中监测。'
})

const statusChips = computed(() => {
  if (roleType.value === 'student') {
    return ['个人成绩总览', roleMeta.value.label, '同步更新']
  }
  return ['全局成绩总览', roleMeta.value.label, '同步更新']
})

const footerChips = computed(() => {
  if (roleType.value === 'student') {
    return ['个人成长轨迹', '体考体测联动', '家校共读']
  }
  return ['实时数据稳定', '校园体育指挥中枢', '动态分析持续更新']
})

const latestTicker = computed(() => {
  if (roleType.value === 'student') {
    return [
      `体考：${peSelfSnapshot.value?.detail_list?.[0]?.batch_name || '暂无'}`,
      `体测：${studentFitnessRows.value[0]?.batch_name || '暂无'}`
    ]
  }
  return [`体考：${latestPeBatch.value?.label || '暂无'}`, `体测：${latestFitnessBatch.value?.label || '暂无'}`]
})

const loadStaffSnapshots = async () => {
  const peBatchInfo = await loadLatestBatch(getPeBatchOptionsApi, ['high', 'mid', 'primary', 'university'])
  latestPeBatch.value = peBatchInfo
    ? { label: peBatchInfo.batch?.label || '最新体考批次', stageType: peBatchInfo.stageType }
    : null
  if (peBatchInfo && getBatchValue(peBatchInfo.batch)) {
    const res = await getPeOverviewApi({
      batch_id: getBatchValue(peBatchInfo.batch),
      stage_type: peBatchInfo.stageType
    }).catch(() => null)
    peSnapshot.value = res?.data || null
  }

  const fitnessBatchInfo = await loadLatestBatch(getFitnessBatchOptionsApi, [
    'high',
    'mid',
    'primary',
    'university'
  ])
  latestFitnessBatch.value = fitnessBatchInfo
    ? { label: fitnessBatchInfo.batch?.label || '最新体测批次', stageType: fitnessBatchInfo.stageType }
    : null
  if (fitnessBatchInfo && getBatchValue(fitnessBatchInfo.batch)) {
    const res = await getFitnessOverviewApi({
      batch_id: getBatchValue(fitnessBatchInfo.batch),
      stage_type: fitnessBatchInfo.stageType
    }).catch(() => null)
    fitnessSnapshot.value = res?.data || null
  }
}

const loadStudentSnapshots = async () => {
  const [peRes, fitnessRes] = await Promise.all([
    getPeStudentAnalysisSelfApi().catch(() => null),
    getFitnessStudentAnalysisSelfApi().catch(() => null)
  ])
  peSelfSnapshot.value = peRes?.data || null
  fitnessSelfSnapshot.value = fitnessRes?.data || null
}

const loadCockpit = async () => {
  loading.value = true
  loadingProgress.value = 22
  if (roleType.value === 'student') {
    loadingProgress.value = 48
    await loadStudentSnapshots()
  } else {
    loadingProgress.value = 48
    await loadStaffSnapshots()
  }
  loadingProgress.value = 100
  loading.value = false
}

onMounted(() => {
  loadCockpit()
})
</script>

<template>
  <ContentWrap class="command-center-wrap">
    <div
      class="command-center"
      :style="{
        '--hero-image': `url(${roleMeta.image}) center/cover no-repeat`,
        '--accent': accentPalette.accent,
        '--accent-soft': accentPalette.accentSoft,
        '--accent-strong': accentPalette.accentStrong
      }"
    >
      <div class="command-center__scanline"></div>
      <div class="command-center__backdrop"></div>

      <div class="command-center__inner">
        <header class="command-header">
          <div class="command-header__status">
            <span class="command-header__status-top">系统在线</span>
            <strong>{{ roleMeta.label }}</strong>
          </div>

          <div class="command-header__headline">
            <h1>{{ railHeadline }}</h1>
            <div class="command-header__chips">
              <span v-for="chip in statusChips" :key="chip">{{ chip }}</span>
            </div>
          </div>

          <div class="command-header__clock">
            <strong>{{ currentDateText }}</strong>
            <span>{{ fullDateText }}</span>
          </div>
        </header>

        <div v-if="loading" class="command-loading">
          <div class="command-loading__halo"></div>
          <div class="command-loading__panel">
            <div class="command-loading__title">驾驶舱数据加载中</div>
            <div class="command-loading__desc">正在汇聚体考、体测与综合分析数据</div>
            <ElProgress
              :percentage="loadingProgress"
              :show-text="false"
              :stroke-width="10"
              color="var(--accent)"
              class="command-loading__progress"
            />
            <div class="command-loading__meta">{{ loadingProgress }}%</div>
          </div>
        </div>

        <template v-else>
          <section class="command-stage">
            <aside class="command-rail command-rail--left">
              <article v-for="(card, index) in leftCards" :key="card.title" class="metric-card">
                <div class="metric-card__header">
                  <div>
                    <div class="metric-card__label">{{ card.title }}</div>
                    <div class="metric-card__short">{{ card.short }}</div>
                  </div>
                  <div class="metric-card__badge">0{{ index + 1 }}</div>
                </div>
                <Echart :options="cardChartOptions[index]" :height="160" />
                <div class="metric-card__note">{{ card.note }}</div>
              </article>
            </aside>

            <section class="command-core">
              <div class="command-core__glow"></div>
              <div class="command-core__image"></div>
              <div class="command-core__frame command-core__frame--outer"></div>
              <div class="command-core__frame command-core__frame--inner"></div>
              <div class="command-core__ring">
                <Echart :options="overviewRingOption" :height="450" />
              </div>
              <div class="command-core__panel">
                <div class="command-core__eyebrow">{{ overviewMetric.status }}</div>
                <p class="command-core__desc">{{ railDescription }}</p>
                <div class="command-core__focus">
                  <strong>核心看点</strong>
                  <span>
                    {{
                      roleType === 'student'
                        ? '集中展示本人最新体考、体测和关键表现，进入页面就能直接看到最重要的信息。'
                        : '页面集中展示体考体测总览、结构对比和项目表现，方便快速看清整体情况。'
                    }}
                  </span>
                </div>
                <div class="command-core__ticker">
                  <span v-for="item in latestTicker" :key="item">{{ item }}</span>
                </div>
                <div class="command-core__batch">{{ overviewMetric.subtitle }}</div>
              </div>
            </section>

            <aside class="command-rail command-rail--right">
              <article
                v-for="(card, index) in rightCards"
                :key="card.title"
                class="metric-card metric-card--compact"
              >
                <div class="metric-card__header">
                  <div>
                    <div class="metric-card__label">{{ card.title }}</div>
                    <div class="metric-card__short">{{ card.short }}</div>
                  </div>
                  <div class="metric-card__badge">0{{ index + leftCards.length + 1 }}</div>
                </div>
                <Echart :options="cardChartOptions[index + leftCards.length]" :height="148" />
                <div class="metric-card__note">{{ card.note }}</div>
              </article>
            </aside>
          </section>

          <section class="command-bottom">
            <article class="trend-board is-focus">
              <div class="trend-board__head">
                <div>
                  <div class="panel-eyebrow">趋势总览</div>
                  <h2>体考体测实时趋势看板</h2>
                </div>
                <div class="trend-board__legend">
                  <span>自动聚合</span>
                  <span>实时读数</span>
                </div>
              </div>
              <Echart :options="combinedTrendOption" :height="288" />
            </article>

            <section class="insight-stack">
              <article class="insight-panel is-focus">
                <div class="panel-eyebrow">结构矩阵</div>
                <h3>综合结构矩阵</h3>
                <Echart :options="summaryOption" :height="210" />
              </article>

              <article class="insight-panel is-focus">
                <div class="panel-eyebrow">项目流</div>
                <h3>{{ roleType === 'student' ? '个人体测项目流' : '体测项目达成流' }}</h3>
                <Echart :options="structureOption" :height="210" />
              </article>
            </section>
          </section>

          <footer class="command-footer">
            <span v-for="item in footerChips" :key="item">{{ item }}</span>
          </footer>

          <ElEmpty
            v-if="
              roleType === 'student' &&
              !(peSelfSnapshot?.detail_list?.length || fitnessSelfSnapshot?.detail_list?.length)
            "
            description="暂无可展示的个人成绩数据"
            class="command-empty"
          />
        </template>
      </div>
    </div>
  </ContentWrap>
</template>

<style lang="less" scoped>
.command-center-wrap {
  margin: -20px;
}

.command-center-wrap :deep(.v-content-wrap) {
  background: transparent;
  border-radius: 0;
}

.command-center-wrap :deep(.el-card__body) {
  padding: 0;
}

.command-center {
  position: relative;
  min-height: calc(100vh - 50px);
  background:
    radial-gradient(circle at 50% 18%, rgba(16, 185, 129, 0.08), transparent 18%),
    linear-gradient(180deg, rgba(2, 6, 12, 0.98), rgba(1, 10, 14, 0.98));
  overflow: hidden;
  color: #f8fafc;
}

.command-center__backdrop,
.command-center__scanline {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.command-center__backdrop {
  background:
    radial-gradient(circle at 50% 16%, var(--accent-soft), transparent 24%),
    linear-gradient(rgba(16, 185, 129, 0.028) 1px, transparent 1px),
    linear-gradient(90deg, rgba(16, 185, 129, 0.028) 1px, transparent 1px);
  background-size: auto, 40px 40px, 40px 40px;
  opacity: 0.85;
}

.command-center__scanline {
  background: linear-gradient(to bottom, transparent 50%, rgba(16, 185, 129, 0.028) 50%);
  background-size: 100% 4px;
  opacity: 0.7;
}

.command-center__inner {
  position: relative;
  z-index: 1;
  padding: 22px 24px 18px;
}

.command-header {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr) 220px;
  align-items: center;
  gap: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.command-header__status {
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: rgba(203, 213, 225, 0.82);
  font-size: 14px;
}

.command-header__status-top {
  font-size: 11px;
  letter-spacing: 0.2em;
  color: var(--accent-strong);
}

.command-header__headline {
  position: relative;
  text-align: center;
}

.command-header__headline::before {
  content: '';
  position: absolute;
  inset: -24px 10% auto;
  height: 120px;
  background: radial-gradient(circle, var(--accent-soft), transparent 66%);
  filter: blur(36px);
}

.command-header__headline h1 {
  position: relative;
  margin: 0;
  font-family: 'Plus Jakarta Sans', 'Microsoft YaHei', sans-serif;
  font-style: italic;
  font-size: clamp(34px, 3vw, 62px);
  font-weight: 900;
  letter-spacing: -0.04em;
  text-shadow: 0 0 24px var(--accent-soft);
}

.command-header__chips {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  margin-top: 8px;
  color: rgba(125, 211, 252, 0.82);
  font-size: 11px;
  letter-spacing: 0.08em;
}

.command-header__chips span {
  position: relative;
}

.command-header__chips span + span::before {
  content: '•';
  position: absolute;
  left: -10px;
  color: rgba(148, 163, 184, 0.4);
}

.command-header__clock {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  padding: 16px 18px;
  background: rgba(10, 19, 31, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(16px);
  border-radius: 24px;
}

.command-header__clock strong {
  color: var(--accent-strong);
  font-size: 32px;
  font-weight: 700;
  font-family: 'Plus Jakarta Sans', sans-serif;
}

.command-header__clock span {
  color: rgba(148, 163, 184, 0.88);
  font-size: 12px;
}

.command-loading {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 620px;
  margin-top: 16px;
  overflow: hidden;
  border-radius: 38px;
  background:
    linear-gradient(180deg, rgba(8, 18, 30, 0.78), rgba(8, 18, 30, 0.56)),
    var(--hero-image);
  background-size: cover;
  background-position: center;
}

.command-loading__halo {
  position: absolute;
  width: 420px;
  height: 420px;
  border-radius: 999px;
  background: radial-gradient(circle, var(--accent-soft), transparent 70%);
  filter: blur(26px);
}

.command-loading__panel {
  position: relative;
  z-index: 1;
  width: min(560px, calc(100% - 48px));
  padding: 34px 32px 30px;
  text-align: center;
  border-radius: 30px;
  background: rgba(6, 14, 24, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow:
    0 0 42px rgba(0, 0, 0, 0.28),
    inset 0 0 18px rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(20px);
}

.command-loading__title {
  color: #f8fafc;
  font-size: 28px;
  font-weight: 800;
  font-style: italic;
  font-family: 'Plus Jakarta Sans', 'Microsoft YaHei', sans-serif;
}

.command-loading__desc {
  margin-top: 10px;
  color: rgba(203, 213, 225, 0.78);
  font-size: 14px;
}

.command-loading__progress {
  margin-top: 24px;
}

.command-loading__progress :deep(.el-progress-bar__outer) {
  background: rgba(255, 255, 255, 0.08);
  border-radius: 999px;
}

.command-loading__meta {
  margin-top: 14px;
  color: var(--accent-strong);
  font-size: 16px;
  font-weight: 700;
}

.command-stage {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr) 280px;
  gap: 20px;
  align-items: stretch;
  min-height: 520px;
  margin-top: 18px;
}

.command-rail {
  display: grid;
  gap: 18px;
}

.command-rail--left {
  grid-template-rows: repeat(2, minmax(0, 1fr));
}

.command-rail--right {
  grid-template-rows: repeat(3, minmax(0, 1fr));
}

.metric-card,
.trend-board,
.insight-panel {
  position: relative;
  background: rgba(8, 18, 30, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow:
    0 0 28px rgba(0, 0, 0, 0.24),
    inset 0 0 16px rgba(255, 255, 255, 0.015);
  backdrop-filter: blur(20px);
  overflow: hidden;
  border-radius: 30px;
}

.metric-card::before,
.trend-board::before,
.insight-panel::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, var(--accent-soft), transparent 38%);
  opacity: 0.5;
  pointer-events: none;
}

.metric-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 16px 16px 14px;
}

.metric-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.metric-card__label {
  color: #f8fafc;
  font-size: 15px;
  font-weight: 700;
}

.metric-card__short,
.panel-eyebrow {
  color: var(--accent-strong);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.metric-card__badge {
  min-width: 36px;
  text-align: center;
  padding: 4px 0;
  color: rgba(203, 213, 225, 0.9);
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-weight: 800;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 999px;
}

.metric-card__note {
  color: rgba(148, 163, 184, 0.86);
  font-size: 12px;
  line-height: 1.5;
}

.metric-card--compact {
  padding-bottom: 12px;
}

.command-core {
  position: relative;
  display: grid;
  grid-template-rows: 1fr auto;
  min-height: 520px;
  background:
    linear-gradient(180deg, rgba(4, 10, 20, 0.7), rgba(4, 10, 20, 0.76)),
    var(--hero-image);
  background-size: cover;
  background-position: center;
  overflow: hidden;
  border-radius: 38px;
}

.command-core__glow {
  position: absolute;
  inset: 18% 22% 32%;
  background: radial-gradient(circle, var(--accent-soft), transparent 62%);
  filter: blur(24px);
}

.command-core__image {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(4, 8, 16, 0.76), rgba(4, 8, 16, 0.88)),
    var(--hero-image);
  mix-blend-mode: lighten;
  opacity: 0.26;
}

.command-core__frame {
  position: absolute;
  left: 50%;
  top: 50%;
  pointer-events: none;
  transform: translate(-50%, -50%) rotate(-8deg);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.command-core__frame--outer {
  width: 72%;
  height: 66%;
}

.command-core__frame--inner {
  width: 54%;
  height: 50%;
  transform: translate(-50%, -50%) rotate(7deg);
  border-style: dashed;
  opacity: 0.45;
}

.command-core__ring {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding-top: 16px;
}

.command-core__panel {
  position: relative;
  z-index: 1;
  padding: 0 36px 28px;
  text-align: center;
}

.command-core__eyebrow {
  color: rgba(226, 232, 240, 0.7);
  font-size: 12px;
  letter-spacing: 0.08em;
}

.command-core__desc {
  max-width: 720px;
  margin: 8px auto 0;
  color: rgba(226, 232, 240, 0.84);
  font-size: 15px;
  line-height: 1.8;
}

.command-core__focus {
  display: inline-flex;
  flex-direction: column;
  gap: 6px;
  max-width: 560px;
  margin-top: 16px;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 22px;
}

.command-core__focus strong {
  color: #fff;
  font-size: 18px;
}

.command-core__focus span {
  color: rgba(226, 232, 240, 0.78);
  font-size: 13px;
  line-height: 1.6;
}

.command-core__ticker {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
  color: var(--accent-strong);
  font-size: 12px;
  letter-spacing: 0.04em;
}

.command-core__ticker span {
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 999px;
}

.command-core__batch {
  display: inline-block;
  margin-top: 16px;
  padding: 10px 22px;
  color: var(--accent-strong);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.04em;
  background: rgba(4, 10, 20, 0.68);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 999px;
}

.command-bottom {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) 360px;
  gap: 20px;
  margin-top: 20px;
}

.trend-board,
.insight-panel {
  padding: 18px 18px 14px;
}

.trend-board__head,
.insight-panel h3 {
  position: relative;
  z-index: 1;
}

.trend-board__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 8px;
}

.trend-board__head h2,
.insight-panel h3 {
  margin: 6px 0 0;
  color: #f8fafc;
  font-size: 24px;
  font-weight: 800;
  font-style: italic;
  letter-spacing: -0.02em;
}

.trend-board__legend {
  display: flex;
  align-items: center;
  gap: 10px;
  color: rgba(203, 213, 225, 0.72);
  font-size: 11px;
}

.trend-board__legend span {
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 999px;
}

.insight-stack {
  display: grid;
  gap: 18px;
}

.trend-board.is-focus,
.insight-panel.is-focus {
  border-color: rgba(255, 255, 255, 0.16);
  box-shadow:
    0 0 38px var(--accent-soft),
    inset 0 0 16px rgba(255, 255, 255, 0.02);
}

.command-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 32px;
  margin-top: 16px;
  padding-top: 12px;
  color: rgba(148, 163, 184, 0.56);
  font-size: 11px;
  letter-spacing: 0.08em;
}

.command-footer span {
  position: relative;
}

.command-footer span + span::before {
  content: '';
  position: absolute;
  left: -16px;
  top: 50%;
  width: 1px;
  height: 12px;
  background: rgba(148, 163, 184, 0.18);
  transform: translateY(-50%);
}

.command-empty {
  margin-top: 22px;
}

@media (max-width: 1480px) {
  .command-stage {
    grid-template-columns: 240px minmax(0, 1fr) 240px;
  }

  .command-bottom {
    grid-template-columns: minmax(0, 1.25fr) 320px;
  }
}

@media (max-width: 1200px) {
  .command-center-wrap {
    margin: -12px;
  }

  .command-center__inner {
    padding: 14px;
  }

  .command-header {
    grid-template-columns: 1fr;
    text-align: center;
  }

  .command-header__status,
  .command-header__clock {
    align-items: center;
  }

  .command-toolbar {
    justify-content: center;
  }

  .command-stage,
  .command-bottom {
    grid-template-columns: 1fr;
  }

  .command-rail--left,
  .command-rail--right {
    grid-template-rows: none;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }
}

@media (max-width: 768px) {
  .command-header__headline h1 {
    font-size: 34px;
  }

  .command-header__chips,
  .command-core__ticker,
  .command-footer {
    flex-wrap: wrap;
    gap: 10px;
    letter-spacing: 0.04em;
  }

  .command-core {
    min-height: 460px;
  }

  .command-core__panel {
    padding: 0 18px 18px;
  }

  .trend-board__head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
