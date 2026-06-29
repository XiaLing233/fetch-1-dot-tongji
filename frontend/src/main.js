import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'

// element-plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

// dayjs
import 'dayjs/locale/zh-cn'

const app = createApp(App)

app.use(router)
app.use(store)
app.use(ElementPlus, {
    locale: zhCn,
})

app.mount('#app')
