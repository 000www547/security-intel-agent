<template>
  <n-tag :type="tagType" :bordered="false" size="small" round>
    {{ label }}
  </n-tag>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  level: { type: String, required: true },  // "高危" / "中危" / "低危"
});

const tagType = computed(() => {
  const map = { "高危": "error", "中危": "warning", "低危": "success" };
  return map[props.level] || "default";
});

const label = computed(() => {
  return props.level || "未知";
});
</script>
