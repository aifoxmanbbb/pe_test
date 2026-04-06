import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import type { App } from 'vue'
import { Layout } from '@/utils/routerHelper'
import { useI18n } from '@/hooks/web/useI18n'

const { t } = useI18n()

export const constantRouterMap: AppRouteRecordRaw[] = [
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard/analysis',
    name: 'Root',
    meta: {
      hidden: true
    },
    children: [
      {
        path: 'home',
        name: 'Home',
        component: () => import('@/views/Home/Home.vue'),
        meta: {
          affix: false,
          alwaysShow: true,
          breadcrumb: true,
          canTo: true,
          hidden: true,
          noCache: true,
          noTagsView: false,
          title: '个人主页'
        }
      }
    ]
  },
  {
    path: '/redirect',
    component: Layout,
    name: 'Redirect',
    children: [
      {
        path: '/redirect/:path(.*)',
        name: 'Redirect',
        component: () => import('@/views/Redirect/Redirect.vue'),
        meta: {}
      }
    ],
    meta: {
      hidden: true,
      noTagsView: true
    }
  },
  {
    path: '/login',
    component: () => import('@/views/Login/Login.vue'),
    name: 'Login',
    meta: {
      hidden: true,
      title: t('router.login'),
      noTagsView: true
    }
  },
  {
    path: '/reset/password',
    component: () => import('@/views/Reset/Reset.vue'),
    name: 'ResetPassword',
    meta: {
      hidden: true,
      title: '重置密码',
      noTagsView: true
    }
  },
  {
    path: '/docs',
    name: 'Docs',
    meta: {
      hidden: true,
      title: '在线文档',
      noTagsView: true
    },
    children: [
      {
        path: 'privacy',
        name: 'Privacy',
        component: () => import('@/views/Vadmin/Docs/Privacy.vue'),
        meta: {
          hidden: true,
          title: '隐私政策',
          noTagsView: true
        }
      },
      {
        path: 'agreement',
        name: 'Agreement',
        component: () => import('@/views/Vadmin/Docs/Agreement.vue'),
        meta: {
          hidden: true,
          title: '用户协议',
          noTagsView: true
        }
      }
    ]
  },
  {
    path: '/404',
    component: () => import('@/views/Error/404.vue'),
    name: 'NoFind',
    meta: {
      hidden: true,
      title: '404',
      noTagsView: true
    }
  }
]

export const asyncRouterMap: AppRouteRecordRaw[] = [
  {
    path: '/dashboard',
    component: Layout,
    redirect: '/dashboard/workplace',
    name: 'Dashboard',
    meta: {
      title: t('router.dashboard'),
      icon: 'ant-design:dashboard-filled',
      alwaysShow: true
    },
    children: [
      {
        path: 'workplace',
        component: () => import('@/views/Dashboard/Workplace.vue'),
        name: 'Workplace',
        meta: {
          title: t('router.workplace'),
          noCache: true
        }
      }
    ]
  },
  {
    path: '/pe',
    component: Layout,
    name: 'PE',
    meta: {
      title: '体考管理',
      icon: 'ant-design:dashboard-outlined',
      alwaysShow: true
    },
    children: [
      {
        path: 'overview',
        component: () => import('@/views/Vadmin/PE/Overview/Overview.vue'),
        name: 'PEOverview',
        meta: {
          title: '成绩总览'
        }
      },
      {
        path: 'entry',
        component: () => import('@/views/Vadmin/PE/Entry/Entry.vue'),
        name: 'PEEntry',
        meta: {
          title: '成绩录入'
        }
      },
      {
        path: 'analysis',
        name: 'PEAnalysis',
        meta: {
          title: '统计分析',
          alwaysShow: true
        },
        children: [
          {
            path: 'student',
            component: () => import('@/views/Vadmin/PE/Analysis/Student/Student.vue'),
            name: 'PEStudentAnalysis',
            meta: {
              title: '学生阶段对比'
            }
          },
          {
            path: 'class',
            component: () => import('@/views/Vadmin/PE/Analysis/Class/Class.vue'),
            name: 'PEClassAnalysis',
            meta: {
              title: '班级对比分析'
            }
          },
          {
            path: 'grade',
            component: () => import('@/views/Vadmin/PE/Analysis/Grade/Grade.vue'),
            name: 'PEGradeAnalysis',
            meta: {
              title: '年级对比分析'
            }
          }
        ]
      },
      {
        path: 'report',
        component: () => import('@/views/Vadmin/PE/Report/Report.vue'),
        name: 'PEReport',
        meta: {
          title: '报表中心'
        }
      },
      {
        path: 'standard',
        component: () => import('@/views/Vadmin/PE/Standard/Standard.vue'),
        name: 'PEStandard',
        meta: {
          title: '评分标准'
        }
      },
      {
        path: 'batch',
        component: () => import('@/views/Vadmin/PE/Batch/Batch.vue'),
        name: 'PEBatch',
        meta: {
          title: '批次管理'
        }
      }
    ]
  },
  {
    path: '/fitness',
    component: Layout,
    name: 'Fitness',
    meta: {
      title: '体测管理',
      icon: 'ant-design:line-chart-outlined',
      alwaysShow: true
    },
    children: [
      {
        path: 'overview',
        component: () => import('@/views/Vadmin/Fitness/Overview/Overview.vue'),
        name: 'FitnessOverview',
        meta: {
          title: '体测总览'
        }
      },
      {
        path: 'entry',
        component: () => import('@/views/Vadmin/Fitness/Entry/Entry.vue'),
        name: 'FitnessEntry',
        meta: {
          title: '体测录入'
        }
      },
      {
        path: 'analysis',
        name: 'FitnessAnalysis',
        meta: {
          title: '统计分析',
          alwaysShow: true
        },
        children: [
          {
            path: 'student',
            component: () => import('@/views/Vadmin/Fitness/Analysis/Student/Student.vue'),
            name: 'FitnessStudentAnalysis',
            meta: {
              title: '学生体测分析'
            }
          },
          {
            path: 'class',
            component: () => import('@/views/Vadmin/Fitness/Analysis/Class/Class.vue'),
            name: 'FitnessClassAnalysis',
            meta: {
              title: '班级体测分析'
            }
          },
          {
            path: 'grade',
            component: () => import('@/views/Vadmin/Fitness/Analysis/Grade/Grade.vue'),
            name: 'FitnessGradeAnalysis',
            meta: {
              title: '年级体测分析'
            }
          }
        ]
      },
      {
        path: 'report',
        component: () => import('@/views/Vadmin/Fitness/Report/Report.vue'),
        name: 'FitnessReport',
        meta: {
          title: '体测报表中心'
        }
      },
      {
        path: 'standard',
        component: () => import('@/views/Vadmin/Fitness/Standard/Standard.vue'),
        name: 'FitnessStandard',
        meta: {
          title: '体测标准中心'
        }
      },
      {
        path: 'batch',
        component: () => import('@/views/Vadmin/Fitness/Batch/Batch.vue'),
        name: 'FitnessBatch',
        meta: {
          title: '批次管理'
        }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  strict: true,
  routes: constantRouterMap as RouteRecordRaw[],
  scrollBehavior: () => ({ left: 0, top: 0 })
})

export const resetRouter = (): void => {
  const resetWhiteNameList = [
    'Login',
    'NoFind',
    'Root',
    'ResetPassword',
    'Redirect',
    'Home',
    'Docs',
    'Privacy',
    'Agreement'
  ]
  router.getRoutes().forEach((route) => {
    const { name } = route
    if (name && !resetWhiteNameList.includes(name as string)) {
      router.hasRoute(name) && router.removeRoute(name)
    }
  })
}

// 判断是否已经有某个路径的路由配置
export const hasRoute = (path: string): boolean => {
  const resolvedRoute = router.resolve(path)
  return resolvedRoute.matched.length > 0
}

export const setupRouter = (app: App<Element>) => {
  app.use(router)
}

export default router
