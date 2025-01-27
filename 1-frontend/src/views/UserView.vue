<template>
    <div style="display: flex; flex-direction: column; width: 100%;">
        <el-page-header @back= "() => $router.push('/')" style="padding: 20px 0 20px 0">
            <template #content>
                <span>个人信息维护</span>
                <!-- <h1> {{ this.$store.state.isLoggedin }}</h1> -->
            </template>
        </el-page-header>

        <div class="userContainer">
            <el-card
            shadow="never"
            style="margin: 20px 0 20px 0; width: 800px; padding: 10px 30px 0 30px"
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
            <p>下方开关可以控制是否接收提醒</p>
            <el-switch
                v-model= "now_option"
                active-color="#13ce66"
                inactive-color="#ff4949"
                active-text="接收"
                inactive-text="不接收"
                :before-change="handleSwitch"
            ></el-switch>
            <el-divider />
            <h4>密码修改</h4>
            <el-form
                :model="password"
                :rules="rules"
                ref="password"
                label-width="80px"
            >
                <el-form-item label="新密码" prop="new">
                    <el-input v-model="password.new" show-password></el-input>
                </el-form-item>
                <el-form-item label="确认密码" prop="confirm">
                    <el-input v-model="password.confirm" show-password></el-input>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="changePassword">确认修改</el-button>
                </el-form-item>
            </el-form>
            <el-divider />
            <h4>最近的 [{{ this.$store.state.userInfo.xl_login_log.length }}] 次登录记录</h4>
            <el-table
                :data="this.$store.state.userInfo.xl_login_log"
                style="width: 100%"
                stripe
                border
            >
                <el-table-column
                    prop="login_at"
                    label="登录时间"
                ></el-table-column>
                <el-table-column
                    prop="ip_address"
                    label="登录 IP"
                ></el-table-column>
            </el-table>
        </el-card>
        </div>

    </div>
</template>

<script>
import axios from 'axios'
import { ElMessage } from 'element-plus';
import { passwordEncrypt } from '@/utils/xl_encrypt';

export default {
    data() {
        return {
            now_option: this.$store.state.userInfo.xl_receive_noti,
            password: {
                new: '',
                confirm: ''
            },
            rules: {
                new: [
                    { required: true, message: '请输入新密码', trigger: 'blur' },
                    { min: 8, max: 20 , message: '密码长度在8-20个字符之间', trigger: 'blur' }
                ],
                confirm: [
                    { required: true, message: '请再次输入密码', trigger: 'blur' },
                    { validator: (rule, value, callback) => {
                        if (value === this.password.new) {
                            callback()
                        } else {
                            callback(new Error('两次输入的密码不一致'))
                        }
                    }, trigger: 'blur' }
                ]
            }
        }
    },
    methods: {
        handleSwitch() {
            return new Promise((resolve) => {
                // 如果 cookie 为空，说明在另一个窗口退出了，这时候需要重新登录
                if (!document.cookie) {
                this.isLoading = false
                ElMessage({
                    title: '提示',
                    message: '您还未登录，请先登录',
                    type: 'warning',
                    grouping: true
                })
                this.$store.commit('logout')
                return
                }
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
                        // console.log(response)
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
                        // 如果返回的状态码是 401，说明 token 过期了，需要重新登录
                        if (err.response.status === 401) {
                            this.$store.commit('logout')
                            this.$router.push('/login')
                            ElMessage({
                            message: '登录已过期',
                            grouping: true,
                            type: 'error'
                        })
                        }
                        else{
                            ElMessage({
                                message: '网络错误，请稍后再试',
                                grouping: true,
                                type: 'error'
                            })
                        }
                        resolve(false)
                    })
            })
        },
        changePassword() {
            this.$refs.password.validate((valid) => {
                if (valid) {
                    // 如果 cookie 为空，说明在另一个窗口退出了，这时候需要重新登录
                    if (!document.cookie) {
                        this.isLoading = false
                        ElMessage({
                            title: '提示',
                            message: '您还未登录，请先登录',
                            type: 'warning',
                            grouping: true
                        })
                        this.$store.commit('logout')
                        return
                    }
                    axios({
                        url: '/api/changePassword',
                        method: 'post',
                        headers: {
                            'X-CSRF-TOKEN': document.cookie.split('; ').find(row => row.startsWith('csrf_access_token=')).split('=')[1]
                        },
                        data: {
                            xl_email: this.$store.state.userInfo.xl_email,
                            xl_newpassword: passwordEncrypt(this.password.new)
                        }
                    })
                        .then(response => {
                            // console.log(response)
                            ElMessage({
                                message: '修改成功',
                                grouping: true,
                                type: 'success'
                            })
                        })
                        .catch(error => {
                            console.log(error)
                            if (err.response.status === 401) {
                                this.$store.commit('logout')
                                this.$router.push('/login')
                                ElMessage({
                                message: '登录已过期',
                                grouping: true,
                                type: 'error'
                            })
                            }
                            else{
                                ElMessage({
                                    message: '网络错误，请稍后再试',
                                    grouping: true,
                                    type: 'error'
                                })
                            }
                        })
                } else {
                    return false
                }
            })
        },
        getUserInfo() {
            if (!document.cookie) {
                this.isLoading = false
                ElMessage({
                    title: '提示',
                    message: '您还未登录，请先登录',
                    type: 'warning',
                    grouping: true
                })
                this.$store.commit('logout')
                return
            }
            axios({
                method: 'post',
                url: '/api/getUserInfo',
                credentials: 'same-origin',
                headers: {
                    'X-CSRF-TOKEN': document.cookie.split('; ').find(row => row.startsWith('csrf_access_token=')).split('=')[1]
                },
                data: {
                    xl_email: this.$store.state.userInfo.xl_email // 这里不用再加 @tongji.edu.cn 了
                }
            })
            .then(response => {
                    this.$store.commit('setUserInfo', response.data.data)
            })
            .catch(error => {
                console.log(error)
                if (err.response.status === 401) {
                    this.$store.commit('logout')
                    this.$router.push('/login')
                    ElMessage({
                    message: '登录已过期',
                    grouping: true,
                    type: 'error'
                })
                }
                else{
                    ElMessage({
                        message: '网络错误，请稍后再试',
                        grouping: true,
                        type: 'error'
                    })
                }
            })
        },
    },
    created() {
        this.getUserInfo()
    }
}
</script>

<style>
.userContainer {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    background: url('@/assets/user-bg.png');
    background-size: cover;
    background-position: center;
    min-height: 800px
}
</style>