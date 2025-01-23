<template>
    <div style="display: flex; flex-direction: column; width: 100%;">
        <el-page-header @back= "() => $router.push('/')" style="padding: 20px 0 20px 0">
            <template #content>
                <span>个人信息维护</span>
                <!-- <h1> {{ this.$store.state.isLoggedin }}</h1> -->
            </template>
        </el-page-header>

        <div style="display: flex; flex-direction: column; align-items: center; gap: 10px; background-color: #f0f0f0; height: 800px">
            <el-card
            shadow="never"
            style="margin-top: 20px; width: 800px; padding: 10px 30px 0 30px"
        >
            <el-descriptions title="基本信息">
                <el-descriptions-item label="昵称">{{ this.$store.state.userInfo.xl_nickname }}</el-descriptions-item>
                <el-descriptions-item label="邮箱">{{ this.$store.state.userInfo.xl_email }}</el-descriptions-item>
                <el-descriptions-item label="注册时间">{{ this.$store.state.userInfo.xl_created_at }}</el-descriptions-item>
            </el-descriptions>

            <el-divider />

            <h4>通知控制</h4>
            <div v-if="this.$store.state.userInfo.xl_receive_noti">
                <p>您当前选择：<el-text type="success" size="large">接收</el-text>通知更新的提醒</p>
                <p>也就是说，每当 1 系统更新消息通知时，您<el-text type="success" size="large">会</el-text>接收到邮件提醒</p>
            </div>
            <div v-else>
                <p>您当前选择：<el-text type="danger" size="large">不接收</el-text>通知更新的提醒</p>
                <p>也就是说，每当 1 系统更新消息通知时，您<el-text type="danger" size="large">不会</el-text>接收到邮件提醒</p>
            </div>
            <el-divider />
            <p>下方开关可以控制是否接收提醒</p>
            <el-switch
                v-model= "now_option"
                active-color="#13ce66"
                inactive-color="#ff4949"
                active-text="接收"
                inactive-text="不接收"
                :before-change="handleSwitch"
            ></el-switch>
        </el-card>
        </div>

    </div>
</template>

<script>
import axios from 'axios'
import { ElMessage } from 'element-plus';

export default {
    data() {
        return {
            now_option: this.$store.state.userInfo.xl_receive_noti,
        }
    },
    methods: {
        handleSwitch() {
            return new Promise((resolve) => {
                axios({
                    url: '/api/toggleReceiveNoti',
                    method: 'post',
                    headers: {
                        'X-CSRF-TOKEN': document.cookie.split('; ').find(row => row.startsWith('csrf_access_token=')).split('=')[1]
                    },
                    data: {
                        xl_email: this.$store.state.userInfo.xl_email,
                        expect_option: !this.now_option
                    }
                })
                    .then(response => {
                        console.log(response)
                        this.$store.commit('toggleNoti')
                        ElMessage({
                            message: '切换成功',
                            grouping: true,
                            type: 'success'
                        })
                        resolve(true)
                    })
                    .catch(error => {
                        console.log(error)
                        ElMessage({
                            message: '网络错误，请稍后再试',
                            grouping: true,
                            type: 'error'
                        })
                        resolve(false)
                    })
            })
        }
    }
}
</script>