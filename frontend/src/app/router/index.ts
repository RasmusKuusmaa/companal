import { createRouter, createWebHistory } from "vue-router";

import { registerGuards } from "./guards";
import { routes } from "./routes";

declare module "vue-router" {
  interface RouteMeta {
    requiresAuth?: boolean;
    guestOnly?: boolean;
  }
}

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    return savedPosition ?? { top: 0 };
  },
});

registerGuards(router);
