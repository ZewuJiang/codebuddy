# Lighthouse 部署指南

本指南将帮助您将 Todo 应用部署到腾讯云 Lighthouse 轻量应用服务器。

## 前置条件

在开始部署之前,请确保:

1. ✅ 您已有腾讯云账号
2. ✅ 您已购买并运行 Lighthouse 实例
3. ✅ 实例已安装 TAT (腾讯云自动化助手)
4. ✅ 实例已安装 Docker 环境

## 部署流程概览

```
1. 选择部署地域
   ↓
2. 选择目标服务器实例
   ↓
3. 上传项目文件
   ↓
4. 配置防火墙规则
   ↓
5. 启动 Web 服务
   ↓
6. 访问应用
```

## 详细步骤

### 步骤 1: 选择部署地域

首先需要确定您的服务器所在地域。常见地域包括:

- **ap-guangzhou** (广州)
- **ap-shanghai** (上海)
- **ap-beijing** (北京)
- **ap-chengdu** (成都)
- **ap-nanjing** (南京)
- **ap-hongkong** (香港)

💡 **选择建议**: 选择距离您目标用户最近的地域,可获得更好的访问速度。

### 步骤 2: 选择目标服务器

在选定地域后,系统会列出该地域所有运行中的 Lighthouse 实例。您需要:

1. 查看实例列表
2. 确认实例状态为"运行中"
3. 确认实例已安装 Docker 和 TAT
4. 选择要部署的实例

### 步骤 3: 上传项目文件

系统会自动将您的项目文件打包并上传到服务器的 `/root/projects/todo-app` 目录。

上传内容包括:
- `index.html` - 应用主文件
- `README.md` - 项目说明文档

### 步骤 4: 配置防火墙规则

为了让外网能访问您的应用,需要开放 HTTP 端口:

- **默认端口**: 80 (HTTP)
- **备选端口**: 8080 (如果 80 被占用)

系统会自动检查端口是否已开放,如未开放则自动添加防火墙规则。

### 步骤 5: 启动 Web 服务

对于静态 HTML 应用,我们使用 Nginx 作为 Web 服务器,通过 Docker 运行:

```bash
# 停止旧容器(如果存在)
docker stop todo-app 2>/dev/null || true
docker rm todo-app 2>/dev/null || true

# 启动新容器
docker run -d \
  --name todo-app \
  -p 80:80 \
  -v /root/projects/todo-app:/usr/share/nginx/html:ro \
  nginx:alpine

# 验证容器运行状态
docker ps | grep todo-app
```

### 步骤 6: 访问应用

部署完成后,您可以通过以下方式访问:

```
http://[服务器公网IP]
```

系统会自动提供完整的访问链接。

## 部署架构

```
┌─────────────────────────────────────┐
│     Lighthouse 服务器实例           │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  Docker 容器 (nginx:alpine)  │  │
│  │                              │  │
│  │  监听端口: 80                │  │
│  │  文档根目录: /usr/share/... │  │
│  │                              │  │
│  │  挂载卷:                     │  │
│  │  /root/projects/todo-app    │  │
│  │    └─ index.html             │  │
│  │    └─ README.md              │  │
│  └──────────────────────────────┘  │
│                                     │
│  防火墙规则: 允许 TCP 80 入站      │
└─────────────────────────────────────┘
              ↓
         公网访问
    http://服务器IP
```

## 常见问题

### Q1: 如何检查 Docker 是否已安装?

登录服务器后执行:
```bash
docker --version
```

如未安装,可执行:
```bash
# CentOS/RHEL
yum install -y docker
systemctl start docker

# Ubuntu/Debian
apt-get update
apt-get install -y docker.io
systemctl start docker
```

### Q2: 如何检查 TAT 是否已安装?

TAT (腾讯云自动化助手) 通常在 Lighthouse 实例创建时自动安装。您可以在腾讯云控制台查看实例详情确认。

### Q3: 端口 80 被占用怎么办?

如果端口 80 已被其他服务占用,可以:

1. **更换端口**: 使用其他端口(如 8080)
   ```bash
   docker run -d --name todo-app -p 8080:80 ...
   ```

2. **停止占用服务**: 找出占用进程并停止
   ```bash
   # 查看占用端口的进程
   netstat -tuln | grep :80
   lsof -i :80
   
   # 停止进程
   kill -9 [进程ID]
   ```

### Q4: 如何更新已部署的应用?

重新执行部署流程即可。系统会:
1. 停止并删除旧容器
2. 上传新文件覆盖旧文件
3. 启动新容器

### Q5: 如何查看部署日志?

```bash
# 查看容器日志
docker logs todo-app

# 实时查看日志
docker logs -f todo-app

# 查看 Nginx 访问日志
docker exec todo-app tail -f /var/log/nginx/access.log
```

### Q6: 如何绑定自定义域名?

1. 在域名服务商处添加 A 记录,指向服务器公网 IP
2. 等待 DNS 解析生效(通常 10 分钟内)
3. (可选) 配置 SSL 证书启用 HTTPS

## 安全建议

1. ✅ 定期更新系统和 Docker 镜像
2. ✅ 只开放必要的端口
3. ✅ 设置强密码或使用 SSH 密钥登录
4. ✅ 启用腾讯云安全组规则
5. ✅ 定期备份重要数据

## 性能优化建议

1. **启用 Gzip 压缩**: 减少传输数据量
2. **使用 CDN**: 加速静态资源访问
3. **设置缓存策略**: 提高重复访问速度
4. **监控资源使用**: 确保服务器负载正常

## 下一步

部署完成后,您可以:

- 📱 在手机浏览器访问测试
- 🔗 分享访问链接给其他用户
- 📊 配置监控和日志分析
- 🔒 配置 HTTPS 加密访问
- 🌐 绑定自定义域名

## 获取帮助

如遇到部署问题,可以:
- 查看腾讯云 Lighthouse 官方文档
- 联系腾讯云技术支持
- 检查服务器日志排查问题

---

现在让我们开始部署吧! 🚀
