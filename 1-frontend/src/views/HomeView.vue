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
            :data="paginatedData"
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
                tempTableData: [],
                openAlertDialog: false,
                openNotiDialog: false,
                search: '',
                statusFilter: [], // 存储当前的状态筛选
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
            this.isLoading = true
            axios({
                url: '/api/findMyCommonMsgPublish',
                method: 'get',
            })
            .then(res => {
                this.isLoading = false
                // console.log(res)
                this.tableData = res.data.data
                // 把时间戳转换为日期格式
                this.tableData.forEach(row => {
                    row.publish_time = new Date(row.publish_time).toLocaleDateString()
                    row.end_time = new Date(row.end_time).toLocaleDateString()
                })
                this.pagi.total = this.tableData.length
                this.tempTableData = this.tableData
                // console.log(this.tableData)
            })
            .catch(err => {
                this.isLoading = false
                console.log(err)
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
                    this.isLoading = true
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
                        url: '/api/findMyCommonMsgPublishById',
                        method: 'post',
                        headers: {
                            'X-CSRF-TOKEN': get_csrf_token(document.cookie)
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
                        this.isLoading = false
                    })
                    .catch(err => {
                        ElMessage({
                            message: err.response.data.msg,
                            type: 'error'
                        })
                        
                        // 如果返回的状态码是 401，说明 token 过期了，需要重新登录
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
                // 如果 cookie 为空，说明在另一个窗口退出了，这时候需要重新登录
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
                    url: '/api/downloadAttachmentByFileName',
                    method: 'post',
                    headers: {
                        'X-CSRF-TOKEN': get_csrf_token(document.cookie)
                    },
                    data: {
                        fileLocation: encryptedFilename
                    },
                })
                .then(res => {
                    const url = res.data.location;
                    window.open(url, '_blank');
                })
                .catch(err => {
                    console.log(err)
                    // 如果返回的状态码是 401，说明 token 过期了，需要重新登录
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
            },
            handleCurrentChange(val) {
                this.pagi.currentPage = val
            },
            // 当表格的筛选条件发生变化的时候会触发该事件，参数的值是一个对象，对象的 key 是 column 的 columnKey，对应的 value 为用户选择的筛选条件的数组。
            handleFilter(filters) {
                // console.log(filters)
                const status = filters['statusColumn'] // 需要在 el-table-column 中设置 column-key 属性才可以，不然传入的是个动态的值，每次刷新可能会变，需要写一个静态的值才好
                this.statusFilter = status // 保存当前的状态筛选
                this.applyFilters()
            },
            handleClose() {
                localStorage.setItem('hadTourBefore', 'true')
            },
            wantBeginTour() {
                return this.$store.state.isLoggedin && localStorage.getItem('hadTourBefore') !== 'true'
            },
            handleSearch() {
                this.applyFilters()
            },
            applyFilters() {
                // 从原始数据开始筛选
                let filteredData = this.tableData
                
                // 应用状态筛选
                if (this.statusFilter.length > 0) {
                    filteredData = filteredData.filter(row => this.statusFilter.includes(row.status))
                }
                
                // 应用搜索筛选
                if (this.search) {
                    filteredData = filteredData.filter(row => row.title.includes(this.search))
                }
                
                // 更新显示数据和分页信息
                this.tempTableData = filteredData
                this.pagi.total = this.tempTableData.length
                this.pagi.currentPage = 1
            }
        },
        computed: {
            paginatedData() {
                const start = (this.pagi.currentPage - 1) * this.pagi.pageSize
                const end = start + this.pagi.pageSize
                return this.tempTableData.slice(start, end)
            }
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