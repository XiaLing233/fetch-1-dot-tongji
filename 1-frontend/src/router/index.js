import { createRouter, createWebHistory } from 'vue-router'
import store from '../store'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
    },
    {
      path: "/user",
      name: "user",
      component: () => import('../views/UserView.vue'),
      beforeEnter: (to, from, next) => {
        if (store.state.isLoggedin) {
          next();
        }
        else {
          window.location.href = '/api/sso/login';
        }
      }
    },
  ],
});

export default router
