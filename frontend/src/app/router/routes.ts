import type { RouteRecordRaw } from "vue-router";

export const routes: RouteRecordRaw[] = [
  {
    path: "/",
    name: "home",
    component: () => import("../views/DashboardView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/projects/new",
    name: "project-create",
    component: () => import("@/features/projects/views/ProjectCreateView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/projects/:id",
    name: "project-detail",
    component: () => import("@/features/projects/views/ProjectDetailView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/projects/:id/score",
    name: "score-viewer",
    component: () => import("@/features/projects/views/ScoreView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/login",
    name: "login",
    component: () => import("@/features/auth/views/LoginView.vue"),
    meta: { requiresAuth: false, guestOnly: true },
  },
  {
    path: "/register",
    name: "register",
    component: () => import("@/features/auth/views/RegisterView.vue"),
    meta: { requiresAuth: false, guestOnly: true },
  },
  {
    path: "/:pathMatch(.*)*",
    name: "not-found",
    component: () => import("../views/NotFoundView.vue"),
    meta: { requiresAuth: false },
  },
];
