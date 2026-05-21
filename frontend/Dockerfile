# =====================================
# 前端 Dockerfile - 多阶段构建
# =====================================
# 面试: "多阶段构建的好处？"
# → 构建阶段用 node, 运行阶段用 nginx
# → 最终镜像极小(约 20MB), 不含 node_modules

# ---- 阶段1: 构建 ----
FROM node:22-alpine AS builder

WORKDIR /app

# 复制 package 文件
COPY package.json package-lock.json* ./

# 安装依赖
RUN npm ci --registry=https://registry.npmmirror.com

# 复制源码
COPY . .

# 构建
RUN npm run build

# ---- 阶段2: 运行 ----
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx 配置 (SPA 路由支持)
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    location /api/ { \
        proxy_pass http://backend:8000/api/; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
