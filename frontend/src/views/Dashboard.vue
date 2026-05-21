<template>
  <div class="dashboard">
    <h2 class="page-title">📊 安全情报仪表盘</h2>

    <!-- 统计卡片 -->
    <n-grid :cols="4" :x-gap="16" :y-gap="16" class="stats-grid">
      <n-grid-item>
        <n-card class="stat-card">
          <n-statistic label="情报总数" :value="stats.total">
            <template #prefix>
              <n-icon size="24" color="#1890ff"><DocumentTextOutline /></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card class="stat-card stat-high">
          <n-statistic label="🔴 高危" :value="highCount" />
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card class="stat-card stat-medium">
          <n-statistic label="🟠 中危" :value="mediumCount" />
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card class="stat-card stat-low">
          <n-statistic label="🟢 低危" :value="lowCount" />
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 风险分布 + 类型分布 -->
    <n-grid :cols="2" :x-gap="16" class="charts-grid">
      <n-grid-item>
        <n-card title="风险等级分布" size="small">
          <div v-if="riskDistribution.length" class="chart-container">
            <div
              v-for="item in riskDistribution"
              :key="item.level"
              class="bar-row"
            >
              <span class="bar-label">{{ item.level }}</span>
              <n-progress
                :percentage="getPercent(item.count, stats.total)"
                :color="riskColor(item.level)"
                :height="24"
                :border-radius="4"
                :show-indicator="false"
              />
              <span class="bar-count">{{ item.count }}</span>
            </div>
          </div>
          <n-empty v-else description="暂无数据" size="small" />
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card title="威胁类型分布 (Top 5)" size="small">
          <div v-if="typeDistribution.length" class="chart-container">
            <div
              v-for="item in typeDistribution.slice(0, 5)"
              :key="item.type"
              class="bar-row"
            >
              <span class="bar-label">{{ item.type }}</span>
              <n-progress
                :percentage="getPercent(item.count, stats.total)"
                color="#1890ff"
                :height="24"
                :border-radius="4"
                :show-indicator="false"
              />
              <span class="bar-count">{{ item.count }}</span>
            </div>
          </div>
          <n-empty v-else description="暂无数据" size="small" />
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 最新情报 -->
    <n-card title="最新情报" size="small" class="latest-intel">
      <div v-if="latestIntel.length" class="intel-grid">
        <IntelCard
          v-for="item in latestIntel"
          :key="item.id"
          :item="item"
          @click="goToDetail"
        />
      </div>
      <n-empty v-else description="暂无情报，请先触发采集" />
    </n-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { NIcon } from "naive-ui";
import { DocumentTextOutline } from "@vicons/ionicons5";
import { fetchStats, fetchIntelList } from "../api";
import IntelCard from "../components/IntelCard.vue";

const router = useRouter();

const stats = ref({
  total: 0,
  risk_distribution: [],
  type_distribution: [],
  daily_trend: [],
});

const latestIntel = ref([]);

const highCount = ref(0);
const mediumCount = ref(0);
const lowCount = ref(0);

const riskDistribution = ref([]);
const typeDistribution = ref([]);

onMounted(async () => {
  try {
    const [statsRes, intelRes] = await Promise.all([
      fetchStats(),
      fetchIntelList({ page: 1, page_size: 6 }),
    ]);
    stats.value = statsRes;
    latestIntel.value = intelRes.items || [];

    // 解析风险分布
    const riskMap = {};
    (statsRes.risk_distribution || []).forEach((r) => {
      riskMap[r.level] = r.count;
    });
    highCount.value = riskMap["高危"] || 0;
    mediumCount.value = riskMap["中危"] || 0;
    lowCount.value = riskMap["低危"] || 0;
    riskDistribution.value = statsRes.risk_distribution || [];
    typeDistribution.value = statsRes.type_distribution || [];
  } catch (e) {
    console.error("加载仪表盘失败:", e);
  }
});

function getPercent(count, total) {
  if (!total) return 0;
  return Math.round((count / total) * 100);
}

function riskColor(level) {
  const map = { "高危": "#f5222d", "中危": "#fa8c16", "低危": "#52c41a" };
  return map[level] || "#d9d9d9";
}

function goToDetail(id) {
  router.push(`/intel/${id}`);
}
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
}

.page-title {
  margin-bottom: 20px;
  font-size: 22px;
}

.stats-grid {
  margin-bottom: 16px;
}

.stat-card {
  text-align: center;
}

.stat-high {
  border-top: 3px solid #f5222d;
}
.stat-medium {
  border-top: 3px solid #fa8c16;
}
.stat-low {
  border-top: 3px solid #52c41a;
}

.charts-grid {
  margin-bottom: 16px;
}

.chart-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 0;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.bar-label {
  width: 50px;
  font-size: 13px;
  flex-shrink: 0;
}

.bar-count {
  width: 30px;
  text-align: right;
  font-size: 13px;
  font-weight: 600;
}

.latest-intel {
  margin-top: 16px;
}

.intel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
}
</style>
