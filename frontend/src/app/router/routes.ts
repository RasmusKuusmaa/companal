import type { RouteRecordRaw } from "vue-router";

export const routes: RouteRecordRaw[] = [
  {
    path: "/",
    name: "home",
    component: () => import("../views/DashboardView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/learn",
    name: "roadmap",
    component: () => import("@/features/learning/views/RoadmapView.vue"),
    meta: { requiresAuth: true },
  },
  {
    // No course segment: lesson slugs are unique across the whole
    // curriculum (see the backend's Lesson model), so a lesson moved to a
    // different stage keeps its URL rather than breaking every link to it.
    path: "/learn/:lessonSlug",
    name: "lesson",
    component: () => import("@/features/learning/views/LessonView.vue"),
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
