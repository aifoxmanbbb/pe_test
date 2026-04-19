import 'vue/jsx'

// 引入windi css
import '@/plugins/unocss'

// 导入全局的svg图标
import '@/plugins/svgIcon'

// 初始化多语言
import { setupI18n } from '@/plugins/vueI18n'

// 引入状态管理
import { setupStore } from '@/store'

// 全局组件
import { setupGlobCom } from '@/components'

// 引入element-plus
import { setupElementPlus } from '@/plugins/elementPlus'

// 引入全局样式
import '@/styles/index.less'

// 引入动画
import '@/plugins/animate.css'

// 路由
import { setupRouter } from './router'

// 权限
import { setupPermission } from './directives'

import { createApp } from 'vue'

import App from './App.vue'

import './permission'

const BUILD_SENTINEL_KEY = '__kinit_build_id__'
const clearRuntimeCacheOnNewBuild = () => {
  const currentBuildId = __APP_BUILD_ID__
  const previousBuildId = window.localStorage.getItem(BUILD_SENTINEL_KEY)
  if (previousBuildId && previousBuildId !== currentBuildId) {
    window.localStorage.clear()
    window.sessionStorage.clear()
    document.cookie.split(';').forEach((cookie) => {
      const name = cookie.split('=')[0]?.trim()
      if (!name) return
      document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`
    })
    window.localStorage.setItem(BUILD_SENTINEL_KEY, currentBuildId)
    window.location.replace(window.location.pathname + window.location.search + window.location.hash)
    return true
  }
  window.localStorage.setItem(BUILD_SENTINEL_KEY, currentBuildId)
  return false
}

// 创建实例
const setupAll = async () => {
  if (clearRuntimeCacheOnNewBuild()) return

  const app = createApp(App)

  await setupI18n(app)

  setupStore(app)

  setupGlobCom(app)

  setupElementPlus(app)

  setupRouter(app)

  setupPermission(app)

  app.mount('#app')
}

setupAll()
