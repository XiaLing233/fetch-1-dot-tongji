<template>
    <!-- 电脑端 -->
    <div style="width: 100%">
        <el-main style="display: flex; justify-content: center; padding: 5px 0 0 0">
        <div 
            class="background" 
            :style="{ 
                background: 'url(data:image/png;base64,' + backgroundPic + ')', 
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                width: '100%'
                }">
            <el-card style="margin: 100px auto; width: 600px;" shadow="never">
            <template #header>
                <div style="text-align: center;">
                    <h2>注册</h2>
                </div>
            </template>
            <el-form
                ref="ruleFormRef"
                label-position="top"
                label-width="auto"
                :model="form"
                :rules="rules"
                style="width: 400px; margin: 0 auto;"
            >

                <el-form-item label="邮箱" prop="xl_email">
                    <el-input v-model="form.xl_email">
                        <template #append>@tongji.edu.cn</template>
                    </el-input>
                </el-form-item>
                <el-form-item label="密码" prop="xl_password">
                    <el-input type="password" v-model="form.xl_password" show-password></el-input>
                </el-form-item>
                <el-form-item label="确认密码" prop="xl_password_confirm">
                    <el-input type="password" v-model="form.xl_password_confirm" show-password></el-input>
                </el-form-item>
                <el-form-item label="验证码" prop="xl_veri_code">
                    <el-input v-model="form.xl_veri_code">
                    <template #append>
                        <el-button type="primary" :id="emailCounter === 0 ? 'veribtn' : ''" @click="sendVerificationEmail" :disabled="emailCounter !== 0" :loading="sendingEmail">{{ emailCounter === 0 ? '发送验证码' : `已发送(${emailCounter}s)` }}</el-button>
                    </template>
                    </el-input>
                </el-form-item>
                <el-form-item style="padding: 10px 0 0 0;">
                    <el-button type="primary" @click="register" style="width: 400px" :loading="registering">注册</el-button>
                </el-form-item>
                </el-form>
                <el-button link type="primary" @click="this.$router.push('/login')" style="float: left; margin-left: 80px; margin-bottom: 20px">已有账号？</el-button>
            </el-card>
        </div>
    </el-main>
</div>
</template>

<script>
import axios from 'axios'
import { passwordEncrypt } from '@/utils/xl_encrypt';
import { ElMessage } from 'element-plus';
import { get_csrf_token } from '@/utils/helpers';

export default {
    data() {
        return {
            form: {
                xl_email: '',
                xl_password: '',
                xl_password_confirm: '',
                xl_veri_code: ''
            },
            backgroundPic: '', // base64 encoded image
            emailCounter: 0,
            openDialog: false,
            sendingEmail: false,
            registering: false,
            rules: {
            xl_email: [
                { required: true, message: '请输入邮箱地址', trigger: 'blur' },
                { pattern: /^[a-zA-Z0-9_.-]+$/, message: '邮箱地址不合法', trigger: 'blur' }
            ],
            xl_password: [
                { required: true, message: '请输入密码', trigger: 'blur'},
                { min: 8, max: 20 , message: '密码长度在8-20个字符之间', trigger: 'blur' }
            ],
            xl_password_confirm: [
                { required: true, message: '请再次输入密码', trigger: 'blur'},
                { validator: (rule, value, callback) => {
                    if (value === this.form.xl_password) {
                        callback()
                    } else {
                        callback(new Error('两次输入的密码不一致'))
                    }
                }, trigger: 'blur' }
            ],
            xl_veri_code: [
                { required: true, message: '请输入验证码', trigger: 'blur' },
                { pattern: /^[0-9]{6}$/, message: '验证码格式错误', trigger: 'blur' }
            ]
    },
        }
    },
    methods: {
        async register() {
            const formEl = this.$refs.ruleFormRef;
            if (!formEl) return;

            const valid = await formEl.validate();
            if (!valid) return;

            this.registering = true;
            try {
                await axios({
                    method: 'post',
                    url: '/api/register',
                    data: {
                        xl_email: this.form.xl_email + '@tongji.edu.cn',
                        xl_password: passwordEncrypt(this.form.xl_password),
                        xl_veri_code: this.form.xl_veri_code
                    }
                })

                await this.getUserInfo()
                this.$store.commit('login')
                ElMessage({
                    message: '注册成功',
                    type: 'success'
                })
                this.$router.push('/')
            } catch (error) {
                console.log(error)
                ElMessage({
                    message: error.response.data.msg,
                    type: 'error'
                })
            } finally {
                this.registering = false;
            }
        },
        async getUserInfo() {
            try {
                const response = await axios({
                    method: 'post',
                    url: '/api/getUserInfo',
                    credentials: 'same-origin',
                    headers: {
                        'X-CSRF-TOKEN': get_csrf_token(document.cookie)
                    },
                    data: {
                        xl_email: this.form.xl_email + '@tongji.edu.cn'
                    }
                })
                this.$store.commit('setUserInfo', response.data.data)
                // console.log("setUserInfo")
            } catch (error) {
                console.log(error)
                throw error
            }
        },
        sendVerificationEmail() {
            let formEl = this.$refs.ruleFormRef;

            console.log(formEl);
            if (!formEl) return;

            formEl.validateField(["xl_email", "xl_password", "xl_password_confirm"], (valid) => {
                if (valid) {
                    // 先调用腾讯验证码
                    this.showCaptcha();
                }
            })
        },
        // 显示腾讯验证码
        showCaptcha() {
            try {
                const captcha = new TencentCaptcha('190271421', (res) => {
                    this.handleCaptchaCallback(res);
                }, {});
                captcha.show();
            } catch (error) {
                console.error('验证码加载失败:', error);
                this.handleCaptchaError();
            }
        },
        // 处理验证码回调
        handleCaptchaCallback(res) {
            // ret: 0-验证成功, 2-用户关闭验证码
            if (res.ret === 0) {
                // 验证成功，发送邮件验证码
                this.sendEmailWithCaptcha(res.ticket, res.randstr);
            } else if (res.ret === 2) {
                ElMessage({
                    message: '已取消验证',
                    type: 'info'
                });
            }
        },
        // 验证码验证成功后，发送邮件
        sendEmailWithCaptcha(ticket, randstr) {
            this.sendingEmail = true;
            axios({
                method: 'post',
                url: '/api/sendVerificationEmail',
                data: {
                    xl_email: this.form.xl_email + '@tongji.edu.cn',
                    captcha_ticket: ticket,
                    captcha_randstr: randstr
                }
            })
            .then(response => {
                // console.log(response)
                this.emailCounter = 60
                const timer = setInterval(() => {
                    this.emailCounter--
                    if (this.emailCounter === 0) {
                        clearInterval(timer)
                    }
                }, 1000)
                ElMessage({
                    message: '验证码已发送',
                    type: 'success'
                });
            })
            .catch(error => {
                console.log(error)
                ElMessage({
                    message: error.response.data.msg,
                    type: 'error'
                })
            })
            .finally(() => {
                this.sendingEmail = false;
            })
        },
        // 处理验证码加载错误
        handleCaptchaError() {
            const appid = '190271421';
            const ticket = 'terror_1001_' + appid + '_' + Math.floor(new Date().getTime() / 1000);
            const randstr = '@' + Math.random().toString(36).substr(2);
            
            ElMessage({
                message: '验证码加载失败，使用容灾票据',
                type: 'warning'
            });
            
            this.sendEmailWithCaptcha(ticket, randstr);
        }
    },
    mounted() {
        // if (!this.$store.state.backgroundRequested) {
        if (1) {
            axios.get('/api/getBackgroundImg')
            .then(response => {
                // this.$store.commit('setBackgroundRequested')
                this.backgroundPic = response.data.data
                // console.log(response)
                // console.log(this.backgroundPic)
            })
            .catch(error => {
                console.log(error)
            })
        }
    }
}
</script>

<style scoped>
.background {
    background-size: contain;
    background-position: center;
    background-color: #f0f0f0;
    height: calc(100vh - 95px);
    width: 100%;
}

.register-link {
    color: #409EFF;
    text-decoration: none;
}

.register-link:hover {
    text-decoration: underline;
}

#veribtn:hover {
    color: #409EFF;
}

.background-mobile {
    background-size: contain;
    background-position: center;
    background-color: #f0f0f0;
    height: 200px;
    width: 100%;
}
</style>