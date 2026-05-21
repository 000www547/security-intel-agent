/**
 * API 请求封装
 * 
 * 面试: "axios 拦截器做了什么？"
 * → request: 统一添加 header/token
 * → response: 统一错误处理 + 数据提取
 */
import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1",
  timeout: 30000,
});

// 响应拦截器: 统一提取 data
api.interceptors.response.use(
  (resp) => resp.data,
  (error) => {
    console.error("API Error:", error.message);
    return Promise.reject(error);
  }
);

// ============================
// API 方法
// ============================

/** 获取情报列表 */
export function fetchIntelList(params = {}) {
  return api.get("/intel", { params });
}

/** 获取情报详情 */
export function fetchIntelById(id) {
  return api.get(`/intel/${id}`);
}

/** 获取统计概览 */
export function fetchStats() {
  return api.get("/stats");
}

/** 手动触发采集 */
export function triggerPipeline() {
  return api.post("/pipeline/run");
}

/** 健康检查 */
export function healthCheck() {
  return api.get("/health");
}
