import { createStore } from 'vuex'

// vuex store
const store = createStore({
    state() {
        return {
        isMobile: false, // 是否为移动端
        isLoggedin: localStorage.getItem('isLoggedin') === 'true', // 是否登录
        // xl_token: '', // 登录后的token // 在 Cookie 中存储，不在这里
        userInfo: localStorage.getItem('userInfo') ? JSON.parse(localStorage.getItem('userInfo')) : {
            xl_nickname: '', // 昵称
            xl_email: '', // 邮箱
            xl_created_at: '', // 注册时间
            xl_receive_noti: false, // 是否接收通知
        }, // 用户信息
        }
    },
    mutations: {
        setIsMobile(state, isMobile) {
            state.isMobile = isMobile
        },
        login(state) {
            state.isLoggedin = true
            localStorage.setItem('isLoggedin', 'true')
        },
        logout(state) {
            state.isLoggedin = false
            localStorage.clear()
        },
        setUserInfo(state, userInfo) {
            console.log('setUserInfo', userInfo)
            state.userInfo = userInfo
            localStorage.setItem('userInfo', JSON.stringify(userInfo))
        },
        toggleNoti(state) {
            state.userInfo.xl_receive_noti = !state.userInfo.xl_receive_noti
            localStorage.setItem('userInfo', JSON.stringify(state.userInfo))
        }
    },
})

export default store