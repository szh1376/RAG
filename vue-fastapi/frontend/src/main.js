import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'

const app = createApp(App)
//调用 createApp，传入根组件 App，生成 Vue 应用实例 app。

app.use(ElementPlus)

// 注册所有图标（组件里用了 Loading 图标）
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')
//将应用实例挂载到 HTML 中 id="app" 的元素上，替换该元素内部的内容，启动 Vue 应用。