# ☁️ WAN Gateway 云端迁移实战指南

恭喜！您的应用已经在本地Docker中成功运行。现在让我们将它迁移到云端，让全世界都能访问您的应用。

## 🎯 云平台选择建议

根据您的具体需求选择最适合的云平台：

### 🥇 Google Cloud Run (强烈推荐新手)
**为什么推荐**:
- ✅ 最简单的部署流程
- ✅ 无服务器，无需管理服务器
- ✅ 按使用付费，成本可控
- ✅ 自动扩缩容
- ✅ 免费额度很大方

**费用预估**: 每月200个小时免费，超出部分$0.00002400/小时

### 🥈 阿里云容器实例 ACR (国内用户)
**为什么选择**:
- ✅ 国内访问速度最快
- ✅ 中文支持完善
- ✅ 与DashScope API同一厂商
- ✅ 网络延迟最低

**费用预估**: 1核1G约¥30-50/月

### 🥉 AWS App Runner (企业用户)
**为什么选择**:
- ✅ 全球覆盖最广
- ✅ 企业级安全性
- ✅ 丰富的生态系统

**费用预估**: $0.064/小时 + 每GB请求$0.007

---

## 🚀 方案一：Google Cloud Run部署 (推荐)

### 前置准备

1. **创建Google Cloud账户**
   - 访问: https://cloud.google.com/
   - 新用户可获得$300免费积分

2. **安装Google Cloud CLI**
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # 验证安装
   gcloud --version
   ```

### 步骤1：项目设置

```bash
# 登录Google Cloud
gcloud auth login

# 创建新项目 (将 'wan-gateway-12345' 替换为您的唯一项目ID)
gcloud projects create wan-gateway-12345

# 设置当前项目
gcloud config set project wan-gateway-12345

# 启用必要的服务
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 步骤2：准备镜像

```bash
# 配置Docker认证
gcloud auth configure-docker

# 为Google Container Registry打标签
docker tag wan-gateway:latest gcr.io/wan-gateway-12345/wan-gateway:latest

# 推送镜像到Google Container Registry
docker push gcr.io/wan-gateway-12345/wan-gateway:latest
```

### 步骤3：部署到Cloud Run

```bash
# 部署应用
gcloud run deploy wan-gateway \
  --image gcr.io/wan-gateway-12345/wan-gateway:latest \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated \
  --set-env-vars DASHSCOPE_API_KEY="您的真实API密钥" \
  --port 7860 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10
```

### 步骤4：获取访问URL

部署成功后，系统会显示一个URL，类似：
```
https://wan-gateway-xxxx-xx.a.run.app
```

---

## 🐉 方案二：阿里云容器实例部署

### 前置准备

1. **注册阿里云账户**
   - 访问: https://www.aliyun.com/
   - 实名认证

2. **安装阿里云CLI**
   ```bash
   # 下载并安装
   curl -O https://aliyuncli.alicdn.com/aliyun-cli-macosx-3.0.XX-amd64.tgz
   tar xzvf aliyun-cli-macosx-3.0.XX-amd64.tgz
   sudo cp aliyun /usr/local/bin
   ```

### 步骤1：配置阿里云CLI

```bash
# 配置访问密钥
aliyun configure set \
  --profile default \
  --mode AK \
  --region cn-hangzhou \
  --access-key-id 您的AccessKeyId \
  --access-key-secret 您的AccessKeySecret
```

### 步骤2：创建容器镜像仓库

```bash
# 登录阿里云容器镜像服务
docker login --username=您的阿里云用户名 registry.cn-hangzhou.aliyuncs.com

# 创建命名空间 (在控制台或使用API)
# 访问: https://cr.console.aliyun.com/
```

### 步骤3：推送镜像

```bash
# 打标签
docker tag wan-gateway:latest registry.cn-hangzhou.aliyuncs.com/您的命名空间/wan-gateway:latest

# 推送镜像
docker push registry.cn-hangzhou.aliyuncs.com/您的命名空间/wan-gateway:latest
```

### 步骤4：创建容器实例

使用阿里云控制台或Kubernetes部署：

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wan-gateway
spec:
  replicas: 1
  selector:
    matchLabels:
      app: wan-gateway
  template:
    metadata:
      labels:
        app: wan-gateway
    spec:
      containers:
      - name: wan-gateway
        image: registry.cn-hangzhou.aliyuncs.com/您的命名空间/wan-gateway:latest
        ports:
        - containerPort: 7860
        env:
        - name: DASHSCOPE_API_KEY
          value: "您的API密钥"
---
apiVersion: v1
kind: Service
metadata:
  name: wan-gateway-service
spec:
  selector:
    app: wan-gateway
  ports:
  - port: 80
    targetPort: 7860
  type: LoadBalancer
```

---

## 🔧 云端配置优化

### 环境变量设置

在云平台中设置以下环境变量：

```bash
# 必需
DASHSCOPE_API_KEY=您的真实API密钥

# 可选优化
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
PORT=7860

# 生产环境优化
GUNICORN_WORKERS=2
GUNICORN_TIMEOUT=300
```

### 资源配置建议

**最小配置** (适合测试):
- CPU: 0.5 核
- 内存: 512MB
- 费用: 约$10-15/月

**推荐配置** (适合生产):
- CPU: 1 核
- 内存: 1GB
- 费用: 约$20-30/月

**高性能配置** (高并发):
- CPU: 2 核
- 内存: 2GB
- 费用: 约$40-60/月

### 网络和安全配置

1. **HTTPS证书**:
   - Google Cloud Run: 自动提供
   - 阿里云: 需要申请SSL证书

2. **域名绑定** (可选):
   ```bash
   # Google Cloud Run
   gcloud run domain-mappings create --service wan-gateway --domain 您的域名.com
   ```

3. **访问控制**:
   ```bash
   # 限制特定IP访问 (如果需要)
   gcloud run services update wan-gateway \
     --add-cloudsql-instances=项目ID:地区:实例ID
   ```

---

## 📊 成本优化策略

### Google Cloud Run成本优化

1. **使用最小配置**:
   ```bash
   --memory 512Mi --cpu 0.5
   ```

2. **设置最大实例数**:
   ```bash
   --max-instances 5
   ```

3. **配置并发数**:
   ```bash
   --concurrency 10
   ```

### 阿里云成本优化

1. **选择合适的地域**: 华东1(杭州)通常最便宜
2. **使用按量付费**: 适合不确定流量的场景
3. **设置自动关机**: 夜间自动停止实例

---

## 🔍 监控和维护

### 日志查看

**Google Cloud Run**:
```bash
# 查看实时日志
gcloud run logs tail wan-gateway

# 查看历史日志
gcloud run logs read wan-gateway
```

**阿里云**:
- 使用日志服务 SLS
- 在控制台查看容器日志

### 性能监控

1. **设置告警**:
   - CPU使用率 > 80%
   - 内存使用率 > 90%
   - 响应时间 > 30秒

2. **流量监控**:
   - 日活跃用户
   - API调用次数
   - 错误率

### 自动备份

```bash
# 定期备份Docker镜像
docker save wan-gateway:latest | gzip > wan-gateway-backup-$(date +%Y%m%d).tar.gz
```

---

## 🆘 故障排除

### 常见问题

1. **部署失败**:
   ```bash
   # 检查构建日志
   gcloud builds list
   gcloud builds log [BUILD_ID]
   ```

2. **应用无法访问**:
   ```bash
   # 检查服务状态
   gcloud run services describe wan-gateway
   ```

3. **API调用失败**:
   - 检查环境变量是否正确设置
   - 验证API密钥权限
   - 检查网络连接

### 回滚策略

```bash
# Google Cloud Run回滚到上一版本
gcloud run services replace-traffic wan-gateway --to-revisions=wan-gateway-00001-abc=100
```

---

## 🎉 完成检查清单

部署完成后，请检查以下项目：

- [ ] 应用可以正常访问
- [ ] API功能正常工作
- [ ] 视频生成功能正常
- [ ] 日志记录正常
- [ ] 监控告警设置完成
- [ ] 成本控制措施生效
- [ ] 备份策略实施

---

## 📞 获取支持

如果在迁移过程中遇到问题：

1. **查看云平台文档**:
   - [Google Cloud Run文档](https://cloud.google.com/run/docs)
   - [阿里云容器服务文档](https://help.aliyun.com/product/85222.html)

2. **社区支持**:
   - Stack Overflow
   - 云平台官方论坛

3. **专业支持**:
   - 云平台技术支持
   - 第三方专业服务

---

**祝贺您！** 通过这个指南，您已经学会了如何将Docker应用从本地迁移到云端。现在您的应用可以为全世界的用户提供服务了！ 🌍✨