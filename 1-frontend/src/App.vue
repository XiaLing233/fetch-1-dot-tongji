import { RouterView } from 'vue-router';


<template>
    <el-container>
      <el-header v-if="$store.state.isMobile === false">
        <div class="edu-header-left">
          <div class="edu-header-logo"></div>
        </div>
        <div class="edu-header-right"  v-if = "$route.path === '/' || $route.path === '/user'">
          <div class="edu-item">
            <div class="user-avatar"></div>
          </div>
          <div class="edu-item">
            <el-dropdown>
              <span>用户名</span>
              <template #dropdown>
                <el-dropdown-menu slot="dropdown">
                <el-dropdown-item>个人信息</el-dropdown-item>
                <el-dropdown-item>退出登录</el-dropdown-item>
              </el-dropdown-menu>
              </template>
            </el-dropdown>
            </div>
            <div class="edu-item">
              <div id="github-link">
                <a href="https://github.com" target="_blank"></a>
              </div>
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
  margin-left: 10px;
}
</style>

<script>
  export default {
    created() {
        if (window.innerWidth < 768) {
            this.$store.commit('setIsMobile', true)
        }
    }
}
</script>