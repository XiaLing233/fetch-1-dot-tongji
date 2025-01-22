<template>
    <!-- 手机端 -->
    <div v-if="$store.state.isMobile" style="width: 100%; display: flex; justify-content: center; margin: 0 auto 0 auto">
        <el-main style="margin: 0; padding: 0; width: 100%">
            <div 
            class="background-mobile" 
                :style="{ 
                    background: 'url(data:image/png;base64,' + backgroundPic + ')', 
                    backgroundSize: 'cover',
                    backgroundPosition: 'center',
                    width: '100%'
                    }">
            </div>
            <el-card style="margin: 0; padding: 0 " shadow="never">
                <template #header>
                    <div style="text-align: center;">
                        <h2>找回密码</h2>
                    </div>
                </template>
                <el-form
                    ref="ruleFormRef"
                    label-position="top"
                    label-width="auto"
                    :model="form"
                    :rules="rules"
                    style="width: 100%; margin: 0; padding: 0;"
                >

                    <el-form-item label="注册的邮箱" prop="xl_username">
                        <el-input v-model="form.xl_username">
                            <template #append>@tongji.edu.cn</template>
                        </el-input>
                    </el-form-item>
                    <el-form-item label="验证码" prop="xl_veri_code">
                        <el-input v-model="form.xl_veri_code">
                        <template #append>
                            <el-button type="primary" id="veribtn">发送验证码</el-button>
                        </template>
                        </el-input>
                    </el-form-item>
                    <el-form-item style="padding: 10px 0 0 0;">
                        <el-button type="primary" @click="recovery" style="width: 100%">发送验证码</el-button>
                    </el-form-item>
                    </el-form>
                    <el-button link type="primary" @click="this.$router.push('/login')" style="float: left; margin-left: 5px; margin-bottom: 10px">返回登录界面</el-button>
                </el-card>
        </el-main>
    </div>

    <!-- 电脑端 -->
    <div v-else style="width: 100%">
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
                        <h2>找回密码</h2>
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

                    <el-form-item label="注册的邮箱" prop="xl_username">
                        <el-input v-model="form.xl_username">
                            <template #append>@tongji.edu.cn</template>
                        </el-input>
                    </el-form-item>
                    <el-form-item label="验证码" prop="xl_veri_code">
                        <el-input v-model="form.xl_veri_code">
                        <template #append>
                            <el-button type="primary" id="veribtn">发送验证码</el-button>
                        </template>
                        </el-input>
                    </el-form-item>
                    <el-form-item style="padding: 10px 0 0 0;">
                        <el-button type="primary" @click="recovery" style="width: 400px">发送验证码</el-button>
                    </el-form-item>
                    </el-form>
                    <el-button link type="primary" @click="this.$router.push('/login')" style="float: left; margin-left: 80px; margin-bottom: 20px">返回登录界面</el-button>
                </el-card>
            </div>
        </el-main>
    </div>
</template>

<script>
import axios from 'axios'
import { passwordEncrypt } from '@/utils/xl_encrypt';

export default {
    data() {
        return {
            form: {
                xl_username: '',
                xl_veri_code: ''
            },
            backgroundPic: '', // base64 encoded image
            rules: {
            xl_username: [
                { required: true, message: '请输入邮箱地址', trigger: 'blur' },
                { pattern: /^[a-zA-Z0-9_.-]+$/, message: '邮箱地址不合法', trigger: 'blur' }
            ],
            xl_veri_code: [
                { required: true, message: '请输入验证码', trigger: 'blur' },
                { pattern: /^[0-9]{6}$/, message: '验证码格式错误', trigger: 'blur' }
            ],
    },
        }
    },
    methods: {
        recovery() {
            const formEl = this.$refs.ruleFormRef
            if (!formEl) return
            formEl.validate((valid) => {
                if (valid) {
                    axios({
                        method: 'post',
                        url: '/api/recovery',
                        data: {
                            xl_username: this.form.xl_username,
                            xl_password: passwordEncrypt(this.form.xl_password)
                        }
                    })
                    .then(response => { 
                        console.log(response)
                    })
                    .catch(error => {
                        console.log(error)
                    })
                }
            })
        }
    },
    mounted() {
        // if (!this.$store.state.backgroundRequested) {
        if (1) {
            axios.get('/api/getBackgroundImg')
            .then(response => {
                this.backgroundPic = response.data.data
                console.log(response)
                console.log(this.backgroundPic)
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

.background-mobile {
    background-size: contain;
    background-position: center;
    background-color: #f0f0f0;
    height: 200px;
    width: 100%;
}
</style>