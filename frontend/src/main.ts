import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPersist from 'pinia-plugin-persistedstate'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import 'element-plus/dist/index.css'

import App from './App.vue'
import { router } from './router'
import './styles/index.scss'
import { patchMessage, patchMessageBox } from './utils/messageBox'
import { initTheme } from './utils/theme'

patchMessageBox()
patchMessage()

const app = createApp(App)
const pinia = createPinia()
pinia.use(piniaPersist)

app.use(pinia)
app.use(router)
app.use(ElementPlus, { locale: zhCn })

initTheme()
app.mount('#app')
