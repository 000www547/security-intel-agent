<template>
  <div class="intel-detail-page">
    <n-button text type="primary" @click="$router.back()" class="back-btn">
      <template #icon><n-icon><ArrowBackOutline /></n-icon></template>
      返回列表
    </n-button>

    <n-spin :show="loading">
      <n-card v-if="item" class="detail-card">
        <template #header>
          <div class="detail-header">
            <h2>{{ item.title }}</h2>
            <n-space>
              <RiskBadge :level="item.risk_level" />
              <n-tag :bordered="false">{{ item.threat_type }}</n-tag>
            </n-space>
          </div>
        </template>

        <n-descriptions :column="2" bordered label-placement="left">
          <n-descriptions-item label="风险等级">
            <RiskBadge :level="item.risk_level" />
          </n-descriptions-item>
          <n-descriptions-item label="AI 置信度">
            <n-progress
              type="circle"
              :percentage="Math.round((item.confidence || 0) * 100)"
              :height="60"
              :color="confidenceColor"
            />
          </n-descriptions-item>
          <n-descriptions-item label="威胁类型">
            <n-tag :bordered="false">{{ item.threat_type }}</n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="CVE 编号">
            {{ item.cve_id || "暂无" }}
          </n-descriptions-item>
          <n-descriptions-item label="来源">
            {{ item.source_name }}
          </n-descriptions-item>
          <n-descriptions-item label="发布时间">
            {{ item.published_at || "未知" }}
          </n-descriptions-item>
          <n-descriptions-item label="分析时间">
            {{ item.analyzed_at }}
          </n-descriptions-item>
          <n-descriptions-item label="受影响产品" :span="2">
            <n-space v-if="item.affected_products?.length">
              <n-tag v-for="p in item.affected_products" :key="p" size="small">
                {{ p }}
              </n-tag>
            </n-space>
            <span v-else>暂无</span>
          </n-descriptions-item>
        </n-descriptions>

        <!-- 详细分析 -->
        <n-divider />
        <h3>📝 情报摘要</h3>
        <n-p class="content-text">{{ item.summary || "暂无摘要" }}</n-p>

        <n-divider v-if="item.attack_vector" />
        <h3 v-if="item.attack_vector">🎯 攻击方式</h3>
        <n-p v-if="item.attack_vector" class="content-text">
          {{ item.attack_vector }}
        </n-p>

        <n-divider v-if="item.defense_plan" />
        <h3 v-if="item.defense_plan">🛡️ 防御方案</h3>
        <n-p v-if="item.defense_plan" class="content-text defense-text">
          {{ item.defense_plan }}
        </n-p>

        <n-divider v-if="item.ioc_indicators?.length" />
        <h3 v-if="item.ioc_indicators?.length">🔍 IOC 威胁指标</h3>
        <n-ul v-if="item.ioc_indicators?.length">
          <n-li v-for="(ioc, idx) in item.ioc_indicators" :key="idx">
            <n-code>{{ ioc }}</n-code>
          </n-li>
        </n-ul>

        <n-divider />
        <n-a :href="item.source_url" target="_blank" v-if="item.source_url">
          查看原文 →
        </n-a>
      </n-card>
    </n-spin>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { NIcon, NCode, NP, NUl, NLi, NA } from "naive-ui";
import { ArrowBackOutline } from "@vicons/ionicons5";
import { fetchIntelById } from "../api";
import RiskBadge from "../components/RiskBadge.vue";

const route = useRoute();
const router = useRouter();

const loading = ref(true);
const item = ref(null);

const confidenceColor = computed(() => {
  if (!item.value) return "#52c41a";
  const c = item.value.confidence || 0;
  if (c >= 0.8) return "#52c41a";
  if (c >= 0.6) return "#fa8c16";
  return "#f5222d";
});

onMounted(async () => {
  try {
    const id = route.params.id;
    item.value = await fetchIntelById(Number(id));
  } catch (e) {
    console.error("加载详情失败:", e);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.intel-detail-page {
  max-width: 900px;
}

.back-btn {
  margin-bottom: 16px;
}

.detail-card {
  /* card styles */
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.detail-header h2 {
  font-size: 20px;
  flex: 1;
}

.content-text {
  line-height: 1.8;
  color: #333;
  font-size: 15px;
  white-space: pre-wrap;
}

.defense-text {
  background: #f6ffed;
  border-left: 3px solid #52c41a;
  padding: 12px 16px;
  border-radius: 4px;
}

h3 {
  font-size: 16px;
  margin: 16px 0 8px;
}
</style>
