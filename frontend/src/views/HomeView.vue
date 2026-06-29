<template>
    <div style="background-color: #f0f0f0; width: 100%; height: auto; margin-top: 20px;">
        <div v-if="this.$store.state.isLoggedin">
        <el-alert
            title="初次使用? 点此开始新手引导"
            type="success"
            style="margin-top: 20px"
            @click="beginTour = true"
            @close.stop="handleClose"
            v-if="wantBeginTour()"
            closable
            :show-icon="true" />
        </div>
        <el-card
        style="margin: 20px auto; height: calc(100vh - 140px); display: flex; flex-direction: column;"
        shadow="never"
    >
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <h4>通知公告</h4>
        <div id="searchTitle">
            <el-input
            v-model="search"
            placeholder="检索标题"
            style="max-width: 300px"
            @input="handleSearch"
        >
        <template #prepend>
            <el-icon><Search /></el-icon>
        </template>
        </el-input>
        </div>
    </div>
        <el-table
            :data="tableData"
            style="width: 100%; flex: 1;"
            :max-height="600"
            stripe
            border
            @row-click="findMyCommonMsgPublishById"
            @filter-change="handleFilter"
            >
            <el-table-column
                prop="title"
                label="标题"
                align="center"
                >
            </el-table-column>
            <el-table-column
                prop="publish_time"
                label="发布时间"
                align="center"
                >
            </el-table-column>
            <el-table-column
                prop="end_time"
                label="结束时间"
                align="center"
                >
            </el-table-column>
            <el-table-column
                prop="status"
                label="状态"
                column-key="statusColumn"
                :filters="[
                    { text: '置顶', value: '置顶' },
                    { text: '发布中', value: '发布中' },
                    { text: '已过期', value: '已过期' }
                ]"
                align="center"
                >
                <template #default="scope">
                    <el-tag
                        :type="scope.row.status === '置顶' ? 'danger' : scope.row.status === '发布中' ? 'success' : 'info'"
                    >
                        {{ scope.row.status }}
                    </el-tag>
                </template>
            </el-table-column>
        </el-table>
        <div style="display: flex; justify-content: flex-end; margin-top: 20px; max-width: 100vw">
            <el-pagination
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
            :current-page="pagi.currentPage"
            :page-sizes="[20, 50, 100, 500, 1000]"
            :page-size="pagi.pageSize"
            layout="total, sizes, prev, pager, next, jumper"
            :total="pagi.total"
        />
        </div>

    </el-card>
    </div>
    <!-- 提示区 -->
    <el-dialog
        v-model="openAlertDialog"
        :title="alert.title"
        width="500"
    >
        <p v-html="alert.content"></p>
        <template #footer>
            <el-button @click="openAlertDialog = false">取消</el-button>
            <el-button type="primary" @click=alert.callback>确定</el-button>
        </template>
    </el-dialog>

    <el-dialog
    v-model="openNotiDialog"
    width="1000"
    draggable
    >
    <template #header>
        <div style="display: flex; align-items: center">
            <img src="@/assets/icon_title.png" style="width: 30px; height: 30px; margin-right: 10px"/>
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
                    <!-- 根据附件的类型在前方插入图标 -->
                     <div style="display: flex; align-items: baseline;">
                        <div :class="attachment.fileType"></div>
                        <div style="margin-bottom: 2px;">
                            <span class="notiAttachment" @click="downloadAttachmentByFileName(attachment.file_location_local)">{{ attachment.filename }}</span>
                        </div>
                     </div>

                </li>
            </ol>
        </div>
    </el-scrollbar>
    </el-dialog>
    <div
        v-loading.fullscreen.lock="isLoading"
        element-loading-text="Loading"></div>
    <!-- 导览区 -->
     <el-tour v-model="beginTour">
        <el-tour-step target="#personalInfo" title="个人信息维护">
            <el-text>点击这里可以管理个人信息、控制通知邮件的发送等</el-text>
        </el-tour-step>
        <el-tour-step target="#searchTitle" title="检索标题">
            <el-text>在这里输入标题的关键字，可以检索到相关的通知公告</el-text>
        </el-tour-step>
        <el-tour-step target=".el-table__column-filter-trigger" title="状态筛选">
            <el-text>点击下箭头，可以筛选通知公告的状态</el-text>
        </el-tour-step>
        <el-tour-step target=".top-row" title="查看通知公告">
            <el-text>点击通知公告的所在行，可以查看通知公告的详细内容</el-text>
        </el-tour-step>
     </el-tour>
</template>

<script>
    import axios from 'axios'
    import { urlEncrypt } from '@/utils/xl_encrypt';
    import { ElMessage } from 'element-plus';
    import { Search } from '@element-plus/icons-vue'
    import { get_csrf_token } from '@/utils/helpers';

    export default {
        data() {
            return {
                tableData: [],
                openAlertDialog: false,
                openNotiDialog: false,
                search: '',
                statusFilter: [],
                noti: {
                    title: '',
                    content: '',
                    publish_time: '',
                    attachments: {
                        fileName: '',
                        fileType: '',
                    }
                },
                alert: {
                    title: '错误提示',
                    content: '',
                    callback: () => this.$router.push('/login')
                },
                pagi: {
                    currentPage: 1,
                    pageSize: 20,
                    total: 0
                },
                isLoading: false,
                beginTour: false
            }
        },
        mounted() {
            this.fetchNotices()
        },
        methods:
        {
            fetchNotices() {
                this.isLoading = true
                const params = {
                    page: this.pagi.currentPage,
                    pageSize: this.pagi.pageSize,
                }
                if (this.statusFilter.length > 0) {
                    params.status = this.statusFilter[0]
                }
                if (this.search) {
                    params.search = this.search
                }
                axios({
                    url: '/api/notices',
                    method: 'get',
                    params,
                })
                .then(res => {
                    this.isLoading = false
                    const payload = res.data.data
                    this.tableData = payload.items
                    this.pagi.total = payload.totalCount
                    this.tableData.forEach(row => {
                        row.publish_time = new Date(row.publish_time).toLocaleDateString()
                        row.end_time = new Date(row.end_time).toLocaleDateString()
                    })
                })
                .catch(err => {
                    this.isLoading = false
                    console.log(err)
                })
            },
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
                    this.isLoading = true
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
                        url: `/api/notices/${row.id}`,
                        method: 'get',
                    })
                    .then(res => {
                        this.noti.title = res.data.data.title
                        this.noti.content = res.data.data.content
                        this.noti.publish_time = res.data.data.publish_time
                        this.noti.attachments = res.data.data.attachments
                        this.openNotiDialog = true
                        this.isLoading = false
                    })
                    .catch(err => {
                        ElMessage({
                            message: err.response.data.msg,
                            type: 'error'
                        })

                        if (err.response.status === 401) {
                            this.$store.commit('logout')
                            this.$router.push('/login')
                        }

                        this.isLoading = false
                    })
                }
                else
                {
                    this.alert.content = "您还未登录，请先登录"
                    this.alert.callback = () => this.$router.push('/login')
                    this.openAlertDialog = true
                }
            },
            downloadAttachmentByFileName(filename) {
                if (!document.cookie) {
                    this.isLoading = false
                    ElMessage({
                        title: '提示',
                        message: '您还未登录，请先登录',
                        type: 'warning',
                        grouping: true
                    })
                    return
                }
                let encryptedFilename = urlEncrypt(filename);
                axios({
                    url: `/api/attachments/${encodeURIComponent(encryptedFilename)}/download`,
                    method: 'get',
                })
                .then(res => {
                    const url = res.data.data.location;
                    window.open(url, '_blank');
                })
                .catch(err => {
                    console.log(err)
                    if (err.response.status === 401) {
                        this.$store.commit('logout')
                        this.$router.push('/login')
                    }
                    else if (err.response.status === 400) {
                        console.log(err)
                        this.alert.content = err.response.data.content;
                        this.alert.callback = () => this.openAlertDialog = false;
                        this.openAlertDialog = true;
                    }
                })
                },
            handleSizeChange(val) {
                this.pagi.pageSize = val
                this.pagi.currentPage = 1
                this.fetchNotices()
            },
            handleCurrentChange(val) {
                this.pagi.currentPage = val
                this.fetchNotices()
            },
            handleFilter(filters) {
                const status = filters['statusColumn'] || []
                this.statusFilter = status
                this.pagi.currentPage = 1
                this.fetchNotices()
            },
            handleClose() {
                localStorage.setItem('hadTourBefore', 'true')
            },
            wantBeginTour() {
                return this.$store.state.isLoggedin && localStorage.getItem('hadTourBefore') !== 'true'
            },
            handleSearch() {
                this.pagi.currentPage = 1
                this.fetchNotices()
            },
        },
        components: {
            Search,
        }
}

</script>

<style scoped>
.notiAttachment {
    color: #409EFF;
    cursor: pointer;
}

.notiAttachment:hover {
    text-decoration: underline;
}

.pdf {
    background: url('@/assets/pdf-icon.svg');
    width: 20px;
    height: 20px;
    margin-right: 6px;
    background-size: cover;
}

.doc {
    background: url('@/assets/doc-icon.svg');
    width: 20px;
    height: 20px;
    margin-right: 6px;
    background-size: cover;
}

.xls {
    background: url('@/assets/xls-icon.svg');
    width: 20px;
    height: 20px;
    margin-right: 6px;
    background-size: cover;
}

.ppt {
    background: url('@/assets/ppt-icon.svg');
    width: 20px;
    height: 20px;
    margin-right: 6px;
    background-size: cover;
}

.rar {
    background: url('@/assets/rar-icon.svg');
    width: 20px;
    height: 20px;
    margin-right: 6px;
    background-size: cover;
}


</style>