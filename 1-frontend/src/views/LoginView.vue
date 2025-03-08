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
                    <h2>登录</h2>
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
                <el-form-item style="padding: 10px 0 0 0;">
                    <el-button type="primary" @click="login" style="width: 400px">登录</el-button>
                </el-form-item>
                </el-form>
                <el-button link type="primary" @click="this.$router.push('/recovery')" style="float: left; margin-left: 80px; margin-bottom: 10px">忘记了密码？</el-button>
                <el-card
                    style="width: 400px; margin: 0 auto; display: flex; justify-content: center;"
                    shadow="never"
                >
                    <span style="text-align: center;">初次使用？</span>
                    <span style="text-align: center;" class="register-link" @click="this.$router.push('/register')">点此注册</span>
                </el-card>
            </el-card>
        </div>
    </el-main>
    </div>

</template>

<script>
import axios from 'axios'
import { passwordEncrypt } from '@/utils/xl_encrypt';
import { ElMessage } from 'element-plus'; // 顶部提示
import { get_csrf_token } from '@/utils/helpers';

export default {
    data() {
        return {
            form: {
                xl_email: '',
                xl_password: ''
            },
            backgroundPic: '', // base64 encoded image
            openDialog: false,
            rules: {
            xl_email: [
                { required: true, message: '请输入邮箱地址', trigger: 'blur' },
                { pattern: /^[a-zA-Z0-9_.-]+$/, message: '邮箱地址不合法', trigger: 'blur' }
            ],
            xl_password: [
                { required: true, message: '请输入密码', trigger: 'blur'},
                { min: 8, max: 20 , message: '密码长度在8-20个字符之间', trigger: 'blur' }
            ],
            },
        }
    },
    methods: {
        async login() {
            const formEl = this.$refs.ruleFormRef;
            if (!formEl) return;
            
            const valid = await formEl.validate();
            if (!valid) return;

            try {
                await axios({
                    method: 'post',
                    url: '/api/login',
                    data: {
                        xl_email: this.form.xl_email + '@tongji.edu.cn',
                        xl_password: passwordEncrypt(this.form.xl_password)
                    }
                })

                await this.getUserInfo()

                this.$store.commit('login')
                ElMessage({
                    message: '登录成功',
                    type: 'success'
                })
                this.$router.push('/')
            } catch (error) {
                console.log(error)
                ElMessage({
                    message: error.response.data.msg,
                    type: 'error'
                })
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
    },
    mounted() {
        if (1) {
            axios.get('/api/getBackgroundImg')
            .then(response => {
                this.backgroundPic = response.data.data
            })
            .catch(error => {
                console.log(error)
            })
        }
    },
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
    cursor: pointer;
}

.background-mobile {
    background-size: contain;
    background-position: center;
    background-color: #f0f0f0;
    height: 200px;
    width: 100%;
}
</style>