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
      path: '/login',
      name: 'login',
      // route level code-splitting
      // this generates a separate chunk (About.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import('../views/LoginView.vue'),
      beforeEnter: (to, from, next) => {
        if (store.state.isLoggedin) {
          next({ name: 'home' });
        }
        else {
          next();
        }
      }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
      beforeEnter: (to, from, next) => {
        if (store.state.isLoggedin) {
          next({ name: 'home' });
        }
        else {
          next();
        }
      }
    },
    {
      path: "/recovery",
      name: "recovery",
      component: () => import('../views/RecoveryView.vue'),
      beforeEnter: (to, from, next) => {
        if (store.state.isLoggedin) {
          next({ name: 'home' });
        }
        else {
          next();
        }
      }
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
          next({ name: 'login' });
        }
      }
    },
  ],
});

export default router
