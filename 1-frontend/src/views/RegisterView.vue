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
                <el-form-item label="图形验证码" prop="xl_captcha_code">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <el-input v-model="form.xl_captcha_code" placeholder="请输入验证码" style="flex: 1;"></el-input>
                        <div style="position: relative; cursor: pointer;" @click="refreshCaptcha">
                            <img v-if="captchaImage && !captchaLoading" :src="'data:image/png;base64,' + captchaImage" alt="验证码" style="width: 120px; height: 50px; border: 1px solid #dcdfe6; border-radius: 4px; display: block;" />
                            <div v-if="captchaLoading" style="width: 120px; height: 50px; border: 1px solid #dcdfe6; border-radius: 4px; display: flex; align-items: center; justify-content: center; background: #f5f7fa; color: #909399;">
                                <i class="el-icon-loading" style="font-size: 20px;"></i>
                            </div>
                            <div v-else-if="!captchaImage" style="width: 120px; height: 50px; border: 1px solid #dcdfe6; border-radius: 4px; display: flex; align-items: center; justify-content: center; background: #f5f7fa; color: #909399;">
                                点击加载
                            </div>
                        </div>
                    </div>
                    <div style="margin-top: 5px;">
                        <el-link type="primary" @click="refreshCaptcha" :underline="false" style="font-size: 12px;">看不清，再换一张</el-link>
                    </div>
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
                xl_captcha_code: '',
                xl_veri_code: ''
            },
            backgroundPic: '', // base64 encoded image
            captchaImage: '', // 图形验证码图片
            captchaLoading: false, // 验证码加载状态
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
            xl_captcha_code: [
                { required: true, message: '请输入图形验证码', trigger: 'blur' },
                { pattern: /^[a-zA-Z0-9]{4}$/, message: '验证码为4位数字或字母', trigger: 'blur' }
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

            formEl.validateField(["xl_email", "xl_password", "xl_password_confirm", "xl_captcha_code"], (valid) => {
                if (valid) {
                    // 直接发送邮件验证码
                    this.sendEmailWithCaptcha();
                }
            })
        },
        // 发送邮件验证码
        sendEmailWithCaptcha() {
            this.sendingEmail = true;
            axios({
                method: 'post',
                url: '/api/sendVerificationEmail',
                data: {
                    xl_email: this.form.xl_email + '@tongji.edu.cn',
                    captcha_code: this.form.xl_captcha_code
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
        // 获取图形验证码
        async getCaptcha() {
            if (this.captchaLoading) return; // 防止重复请求
            
            this.captchaLoading = true;
            try {
                const response = await axios.get('/api/getCaptcha');
                this.captchaImage = response.data.data;
            } catch (error) {
                console.log(error);
                ElMessage({
                    message: error.response?.data?.msg || '获取验证码失败',
                    type: 'error'
                });
            } finally {
                this.captchaLoading = false;
            }
        },
        // 刷新验证码
        refreshCaptcha() {
            if (this.captchaLoading) return; // 防止重复请求
            this.form.xl_captcha_code = '';  // 清空输入
            this.getCaptcha();
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
        // 加载验证码
        this.getCaptcha();
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