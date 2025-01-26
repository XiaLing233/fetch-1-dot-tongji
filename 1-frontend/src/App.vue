import { RouterView } from 'vue-router';


<template>
    <el-container>
      <el-header>
        <div class="edu-header-left" style="display: flex;">
          <a href="/"><div class="edu-header-logo"></div></a>
        </div>
        <div class="edu-header-right">
          <div v-if="this.$store.state.isLoggedin" style="display: flex;">
            <div class="edu-item" style="margin-top: 8px">
                <el-text type="info">
                    {{ this.$store.state.userInfo.xl_login_log.length > 1 ? '上次登录：' : '首次登录' }}
                </el-text>
                <el-text>
                      {{ this.$store.state.userInfo.xl_login_log.length > 1 ? this.$store.state.userInfo.xl_login_log[1]['login_at'] : '' }}
                </el-text>
              </div>
            <div class="edu-item">
            <el-avatar :src="malePNG" size="default"></el-avatar>
          </div>
          <div class="edu-item" style="margin-top: 12px" id="personalInfo">
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
          </div>
          <div v-else style="display: flex; padding-bottom: 7px">
            <div class="edu-item">
              <el-button link type="primary" @click="() => $router.push('/login')">登录</el-button>
            </div>
            <div class="edu-item">
              <el-button link type="primary" @click="() => $router.push('/register')">注册</el-button>
            </div>
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
                    <a href="https://github.com/XiaLing233/fetch-1-dot-tongji" target="_blank" style="text-decoration: none;"><el-dropdown-item><img src="@/assets/github-mark.svg" alt="github" style="width: 15px; height: 15px; margin-right: 10px">Github 仓库</el-dropdown-item></a>
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
  background: url('@/assets/my_icon_logo.png');
  width: 380px;
  height: 40px;
  float: left;
  margin-top: 4px;
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

.open {
  transform: rotate(0deg);
}

</style>

<script>
  import { ArrowDown } from '@element-plus/icons-vue';
  import { Menu } from '@element-plus/icons-vue';
  import axios from 'axios';
  import malePNG from '@/assets/male.png';

  export default {
    data() {
      return {
        openMenu: false,
        malePNG
      }
    },
    created() {
        if (window.innerWidth < 768) {
            this.$store.commit('setIsMobile', true)
        }
    },
    components: {
      ArrowDown,
      Menu,
    },
    methods:
    {
      logout() {
        // 清空 vuex 中的所有数据
        this.$store.commit('logout')
        this.$router.push('/login')
        // 让后端清除 cookie
        axios({
          method: 'get',
          url: '/api/logout',
          headers: {
            'X-CSRF-TOKEN': document.cookie.split('; ').find(row => row.startsWith('csrf_access_token=')).split('=')[1]
          },
        })
        .then(response => {
          // console.log(response)
        })
        .catch(error => {
          console.log(error)
        })
      },
      handleMenu()
      {
        this.openMenu = !this.openMenu
        // console.log(this.openMenu)
      }
    },
}
</script>