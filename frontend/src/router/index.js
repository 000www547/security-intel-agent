import { createRouter, createWebHistory } from "vue-router";
import Dashboard from "../views/Dashboard.vue";
import IntelList from "../views/IntelList.vue";
import IntelDetail from "../views/IntelDetail.vue";

const routes = [
  {
    path: "/",
    name: "Dashboard",
    component: Dashboard,
    meta: { title: "仪表盘" },
  },
  {
    path: "/intel",
    name: "IntelList",
    component: IntelList,
    meta: { title: "情报列表" },
  },
  {
    path: "/intel/:id",
    name: "IntelDetail",
    component: IntelDetail,
    meta: { title: "情报详情" },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
