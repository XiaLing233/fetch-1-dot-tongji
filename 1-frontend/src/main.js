import { createApp } from 'vue'
import { createStore } from 'vuex'
import App from './App.vue'
import router from './router'

// element-plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

// dayjs
import 'dayjs/locale/zh-cn'

// vuex store
const store = createStore({
    state() {
        return {
        isMobile: false,
        // xl_token: '', // 登录后的token // 在 Cookie 中存储，不在这里
        }
    },
    mutations: {
        setIsMobile(state, isMobile) {
            state.isMobile = isMobile
        },
    },
})

const app = createApp(App)

app.use(router)
app.use(store)
app.use(ElementPlus, {
    locale: zhCn,
})

app.mount('#app')
