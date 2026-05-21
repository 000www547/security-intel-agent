<template>
  <n-card
    :class="['intel-card', `risk-${riskClass}`]"
    hoverable
    @click="$emit('click', item.id)"
  >
    <template #header>
      <div class="card-header">
        <n-ellipsis style="max-width: 100%">{{ item.title }}</n-ellipsis>
        <RiskBadge :level="item.risk_level" />
      </div>
    </template>
    <div class="card-body">
      <p class="card-summary">{{ item.summary || "暂无摘要" }}</p>
      <n-space class="card-meta">
        <n-tag size="tiny" :bordered="false">{{ item.threat_type }}</n-tag>
        <n-tag v-if="item.cve_id" size="tiny" type="info" :bordered="false">
          {{ item.cve_id }}
        </n-tag>
        <span class="meta-source">{{ item.source_name }}</span>
        <span class="meta-time">{{ formatTime(item.analyzed_at) }}</span>
      </n-space>
    </div>
  </n-card>
</template>

<script setup>
import RiskBadge from "./RiskBadge.vue";
import { computed } from "vue";

const props = defineProps({
  item: { type: Object, required: true },
});

defineEmits(["click"]);

const riskClass = computed(() => {
  const map = { "高危": "high", "中危": "medium", "低危": "low" };
  return map[props.item.risk_level] || "low";
});

function formatTime(time) {
  if (!time) return "";
  return time.slice(0, 16).replace("T", " ");
}
</script>

<style scoped>
.intel-card {
  cursor: pointer;
  transition: all 0.2s;
}
.intel-card:hover {
  transform: translateY(-2px);
}
.risk-high {
  border-left: 4px solid #f5222d;
}
.risk-medium {
  border-left: 4px solid #fa8c16;
}
.risk-low {
  border-left: 4px solid #52c41a;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.card-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.card-summary {
  color: #666;
  font-size: 14px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.card-meta {
  font-size: 12px;
  color: #999;
}
.meta-source {
  font-weight: 500;
}
.meta-time {
  margin-left: auto;
}
</style>
