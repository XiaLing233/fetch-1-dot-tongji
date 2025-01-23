import { RouterView } from 'vue-router';


<template>
    <el-container>
      <el-header>
        <div class="edu-header-left">
          <div class="edu-header-logo"></div>
        </div>
        <div class="edu-header-right"  v-if = "$route.path === '/' || $route.path === '/user'">
          <div class="edu-item">
            <!-- 需要使用根路径，不能用相对路径 -->
            <el-avatar src="/src/assets/male.png" size="default"></el-avatar> 
          </div>
          <div class="edu-item">
            <el-dropdown>
              <span class="el-dropdown-link">
                {{ this.$store.state.userInfo.xl_nickname }}
                <el-icon class="el-icon--right">
                  <ArrowDown />
                </el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu slot="dropdown">
                <el-dropdown-item @click="() => $router.push('/user')">个人信息</el-dropdown-item>
                <el-dropdown-item @click="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
              </template>
            </el-dropdown>
            </div>
            <div class="edu-item">
              <el-dropdown>
                <span class="el-dropdown-link">
                  关于
                  <el-icon class="el-icon--right">
                    <ArrowDown />
                  </el-icon>
                </span>
                <template #dropdown>
                  <el-dropdown-menu slot="dropdown">
                    <a href="https://github.com/XiaLing233/fetch-1-dot-tongji" target="_blank" style="text-decoration: none;"><el-dropdown-item><img src="/src/assets/github-mark.svg" alt="github" style="width: 15px; height: 15px; margin-right: 10px">Github 仓库</el-dropdown-item></a>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
        </div>
      </el-header>
      
      <el-container>
        <RouterView />
      </el-container>
    </el-container>
</template>

<style scoped>
.edu-header-left {
  float: left;
  padding: 12px 0;
}

.edu-header-right {
  float: right;
  display: flex;
  padding: 12px 0;
  align-items: center;
  height: 100%;
}

.edu-header-logo {
  background: url('assets/icon_logo.png');
  width: 380px;
  height: 40px;
  float: left;
}

.edu-item {
  margin-left: 25px;
}

.el-dropdown-link {
  cursor: pointer;
  color: var(--el-color-primary);
  display: flex;
  align-items: center;
}

</style>

<script>
  import { ArrowDown } from '@element-plus/icons-vue'
  export default {
    created() {
        if (window.innerWidth < 768) {
            this.$store.commit('setIsMobile', true)
        }
    },
    components: {
      ArrowDown
    },
    methods:
    {
      logout() {
        // 清空 vuex 中的所有数据
        this.$store.commit('logout')
        this.$router.push('/login')
      }
    }
}
</script>