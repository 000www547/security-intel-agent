<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-notification-provider>
      <n-layout class="app-layout">
        <!-- 顶部导航 -->
        <n-layout-header bordered class="app-header">
          <div class="header-content">
            <div class="brand" @click="$router.push('/')">
              <span class="brand-icon">🛡️</span>
              <span class="brand-text">Security Intel Agent</span>
            </div>
            <n-space>
              <n-button size="small" @click="handleTrigger">
                <template #icon>
                  <n-icon><RefreshOutline /></n-icon>
                </template>
                触发采集
              </n-button>
            </n-space>
          </div>
        </n-layout-header>

        <!-- 侧边栏 + 内容 -->
        <n-layout has-sider class="app-body">
          <n-layout-sider bordered collapse-mode="width" :width="200">
            <n-menu
              :value="activeMenu"
              :options="menuOptions"
              @update:value="handleMenuChange"
            />
          </n-layout-sider>
          <n-layout-content class="app-content">
            <router-view />
          </n-layout-content>
        </n-layout>
      </n-layout>
    </n-notification-provider>
  </n-config-provider>
</template>

<script setup>
import { computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { NIcon, useNotification } from "naive-ui";
import { RefreshOutline, SpeedometerOutline, ListOutline } from "@vicons/ionicons5";
import { triggerPipeline } from "./api";

const router = useRouter();
const route = useRoute();
const notification = useNotification();

const activeMenu = computed(() => {
  if (route.path === "/") return "dashboard";
  return route.path;
});

const menuOptions = [
  {
    label: "仪表盘",
    key: "dashboard",
    icon: () =>
      h(NIcon, null, { default: () => h(SpeedometerOutline) }),
  },
  {
    label: "情报列表",
    key: "/intel",
    icon: () =>
      h(NIcon, null, { default: () => h(ListOutline) }),
  },
];

import { h } from "vue";

function handleMenuChange(key) {
  if (key === "dashboard") {
    router.push("/");
  } else {
    router.push(key);
  }
}

async function handleTrigger() {
  try {
    const res = await triggerPipeline();
    notification.success({
      title: "采集完成",
      description: `采集 ${res.data.collected} 条，分析 ${res.data.analyzed} 条，入库 ${res.data.stored} 条`,
      duration: 5000,
    });
  } catch (e) {
    notification.error({
      title: "采集失败",
      description: e.message || "未知错误",
    });
  }
}

const themeOverrides = {
  common: {
    primaryColor: "#1890ff",
    primaryColorHover: "#40a9ff",
  },
};
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Helvetica Neue", Arial, sans-serif;
  background: #f5f7fa;
}

.app-layout {
  min-height: 100vh;
}

.app-header {
  height: 56px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  background: #fff;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.brand-icon {
  font-size: 24px;
}

.brand-text {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a2e;
}

.app-body {
  height: calc(100vh - 56px);
}

.app-content {
  padding: 24px;
  overflow-y: auto;
}
</style>
