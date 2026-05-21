<template>
  <div class="intel-list-page">
    <h2 class="page-title">📋 安全情报列表</h2>

    <!-- 筛选栏 -->
    <n-card size="small" class="filter-bar">
      <n-space align="center" :wrap="true">
        <n-input
          v-model:value="keyword"
          placeholder="搜索标题或内容..."
          clearable
          style="width: 240px"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <n-icon><SearchOutline /></n-icon>
          </template>
        </n-input>
        <n-select
          v-model:value="riskFilter"
          :options="riskOptions"
          placeholder="风险等级"
          clearable
          style="width: 120px"
          @update:value="handleSearch"
        />
        <n-select
          v-model:value="typeFilter"
          :options="typeOptions"
          placeholder="威胁类型"
          clearable
          style="width: 140px"
          @update:value="handleSearch"
        />
        <n-button type="primary" @click="handleSearch">
          <template #icon><n-icon><SearchOutline /></n-icon></template>
          搜索
        </n-button>
      </n-space>
    </n-card>

    <!-- 表格 -->
    <n-data-table
      :columns="columns"
      :data="items"
      :loading="loading"
      :pagination="pagination"
      :row-key="(row) => row.id"
      remote
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, h } from "vue";
import { useRouter } from "vue-router";
import { NTag, NButton, NIcon } from "naive-ui";
import { SearchOutline } from "@vicons/ionicons5";
import { fetchIntelList } from "../api";
import RiskBadge from "../components/RiskBadge.vue";

const router = useRouter();

const loading = ref(false);
const items = ref([]);
const keyword = ref("");
const riskFilter = ref(null);
const typeFilter = ref(null);

const pagination = ref({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
});

const riskOptions = [
  { label: "高危", value: "高危" },
  { label: "中危", value: "中危" },
  { label: "低危", value: "低危" },
];

const typeOptions = [
  { label: "漏洞", value: "漏洞" },
  { label: "恶意软件", value: "恶意软件" },
  { label: "APT攻击", value: "APT攻击" },
  { label: "数据泄露", value: "数据泄露" },
  { label: "钓鱼攻击", value: "钓鱼攻击" },
  { label: "DDoS攻击", value: "DDoS攻击" },
  { label: "零日漏洞", value: "零日漏洞" },
  { label: "Web攻击", value: "Web攻击" },
  { label: "配置缺陷", value: "配置缺陷" },
  { label: "其他", value: "其他" },
];

const columns = [
  {
    title: "标题",
    key: "title",
    ellipsis: { tooltip: true },
    width: 300,
  },
  {
    title: "风险等级",
    key: "risk_level",
    width: 100,
    render(row) {
      return h(RiskBadge, { level: row.risk_level });
    },
  },
  {
    title: "威胁类型",
    key: "threat_type",
    width: 110,
    render(row) {
      return h(NTag, { size: "small", bordered: false }, { default: () => row.threat_type });
    },
  },
  {
    title: "CVE",
    key: "cve_id",
    width: 150,
    render(row) {
      return row.cve_id || "-";
    },
  },
  {
    title: "来源",
    key: "source_name",
    width: 100,
  },
  {
    title: "时间",
    key: "analyzed_at",
    width: 160,
    render(row) {
      return row.analyzed_at?.slice(0, 16) || "-";
    },
  },
  {
    title: "操作",
    key: "actions",
    width: 80,
    render(row) {
      return h(
        NButton,
        {
          size: "small",
          text: true,
          type: "primary",
          onClick: () => router.push(`/intel/${row.id}`),
        },
        { default: () => "详情" }
      );
    },
  },
];

async function loadData() {
  loading.value = true;
  try {
    const res = await fetchIntelList({
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
      risk_level: riskFilter.value || undefined,
      threat_type: typeFilter.value || undefined,
      keyword: keyword.value || undefined,
    });
    items.value = res.items || [];
    pagination.value.itemCount = res.total || 0;
  } catch (e) {
    console.error("加载情报列表失败:", e);
  } finally {
    loading.value = false;
  }
}

function handleSearch() {
  pagination.value.page = 1;
  loadData();
}

function handlePageChange(page) {
  pagination.value.page = page;
  loadData();
}

function handlePageSizeChange(size) {
  pagination.value.pageSize = size;
  pagination.value.page = 1;
  loadData();
}

onMounted(() => {
  loadData();
});
</script>

<style scoped>
.intel-list-page {
  max-width: 1200px;
}

.page-title {
  margin-bottom: 16px;
  font-size: 22px;
}

.filter-bar {
  margin-bottom: 16px;
}
</style>
