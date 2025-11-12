import { createRouter, createWebHistory } from 'vue-router';
import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'dashboard',
    meta: { view: 'dashboard' }
  },
  {
    path: '/chat',
    name: 'chat',
    meta: { view: 'chat' }
  },
  {
    path: '/timeline',
    name: 'timeline',
    meta: { view: 'timeline' }
  },
  {
    path: '/tips/:id',
    name: 'tipDetail',
    meta: { view: 'tipDetail' }
  },
  {
    path: '/reports/:id',
    name: 'reportDetail',
    meta: { view: 'reportDetail' }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
