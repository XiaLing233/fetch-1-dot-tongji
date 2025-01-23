<template>
    <div style="background-color: #f0f0f0; width: 100%; ; margin-top: 20px;">
        <el-card
        style="margin: 20px auto; min-height: 800px;"
        shadow="never"
    >
        <h4>通知公告</h4>
        <el-table
            :data="tableData"
            style="width: 100%"
            :row-class-name="defRowLevel"
            height="600"
            stripe
            @row-click="findMyCommonMsgPublishById"
            >
            <el-table-column
                prop="title"
                label="标题"
                >
            </el-table-column>
            <el-table-column
                prop="publish_time"
                label="发布时间">
            </el-table-column>
            <el-table-column
                prop="end_time"
                label="结束时间">
            </el-table-column
        >

        </el-table>
    </el-card>
    </div>
    <el-dialog
        v-model="openAlertDialog"
        title="提示"
        width="500"
    >
        <p>您还未登录，请先登录</p>
        <template #footer>
            <el-button @click="openAlertDialog = false">取消</el-button>
            <el-button type="primary" @click="this.$router.push('/login')">确定</el-button>
        </template>
    </el-dialog>

    <el-dialog
    v-model="openNotiDialog"
    width="1000"
    draggable
    >
    <template #header>
        <div style="display: flex; align-items: center">
            <img src="/src/assets/icon_title.png" style="width: 30px; height: 30px; margin-right: 10px"/>
            <h3>{{ noti.title }}</h3>
        </div>

    </template>
    <el-scrollbar style="height: 60vh">
        <div>
            <h4> 发布日期：{{ new Date(noti.publish_time).toLocaleDateString() }}</h4>
        </div>
        <span v-html="noti.content"></span>
        <div v-if="noti.attachments.length > 0">
            <el-divider />
            <p>附件下载：</p>
            <ol>
                <li v-for="attachment in noti.attachments">
                    <span>{{ attachment.filename }}</span>
                </li>
            </ol>
        </div>
    </el-scrollbar>
    </el-dialog>
   
</template>

<script>
    import axios from 'axios'

    export default {
        data() {
            return {
                tableData: [],
                openAlertDialog: false,
                openNotiDialog: false,
                noti: {
                    title: '',
                    content: '',
                    publish_time: '',
                    attachments: {
                        fileName: '',
                        fileType: '',
                    }
                },
            }
        },
        mounted() {
            axios({
                url: '/api/findMyCommonMsgPublish',
                method: 'get',
            })
            .then(res => {
                console.log(res)
                this.tableData = res.data.data
                console.log(this.tableData)
            })
        },
        methods:
        {
            defRowLevel(row) {
                const invalid_top_time = new Date(row.row.invalid_top_time).getTime()
                if (invalid_top_time > new Date().getTime()) {
                    return 'top-row'
                }
                else {
                    return ''
                }
        },
        findMyCommonMsgPublishById(row) {
            if (this.$store.state.isLoggedin) {
            axios({
                url: '/api/findMyCommonMsgPublishById',
                method: 'post',
                headers: {
                    'X-CSRF-TOKEN': document.cookie.split('; ').find(row => row.startsWith('csrf_access_token=')).split('=')[1]
                },
                data: {
                    id: row.id
                }
            })
            .then(res => {
                this.noti.title = res.data.data.title
                this.noti.content = res.data.data.content
                this.noti.publish_time = res.data.data.publish_time
                this.noti.attachments = res.data.data.attachments
                this.openNotiDialog = true
            })
            .catch(err => {
                // 一般出现这种情况，是因为 token 过期了
                this.$store.commit('logout')
                this.$router.push('/login')
            })
        }
            else
            {
                this.openAlertDialog = true
            }
    }
}
}

</script>

<style>
.el-table .top-row {
  --el-table-tr-bg-color: var(--el-color-danger-light-9);
}
</style>