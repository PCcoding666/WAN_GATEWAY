# 🐳 Docker入门指南 - WAN Gateway应用

欢迎！这是一个为Docker新手准备的完整指南，将帮助您在本地运行WAN Gateway应用，然后迁移到云端。

## 📋 目录
1. [前置条件](#前置条件)
2. [本地Docker运行](#本地docker运行)
3. [云端迁移指南](#云端迁移指南)
4. [常见问题解决](#常见问题解决)

## 🔧 前置条件

### 1. 检查Docker安装
您的系统已经安装了Docker Desktop。您可以通过以下命令验证：
```bash
docker --version
docker info
```

### 2. 获取API密钥
您需要一个阿里云DashScope API密钥：
- 访问: https://help.aliyun.com/document_detail/2712195.html
- 注册并获取您的API密钥

## 🚀 本地Docker运行

### 步骤1：设置环境变量

1. **复制环境变量模板**:
   ```bash
   cp .env.example .env
   ```

2. **编辑.env文件**:
   ```bash
   # 使用您喜欢的编辑器，例如：
   nano .env
   # 或者
   code .env
   ```

3. **将以下内容中的API密钥替换为您的真实密钥**:
   ```bash
   DASHSCOPE_API_KEY=your_actual_api_key_here
   ```

### 步骤2：一键部署

使用我们提供的简化脚本：

```bash
./deploy.sh deploy
```

这个命令会：
- 检查Docker是否运行
- 验证您的.env文件
- 构建Docker镜像
- 启动容器
- 检查应用是否正常运行

### 步骤3：访问应用

部署成功后，打开浏览器访问：
```
http://localhost:7860
```

## 📱 管理您的Docker应用

### 常用命令

```bash
# 查看应用状态
./deploy.sh status

# 查看应用日志
./deploy.sh logs

# 停止应用
./deploy.sh stop

# 重启应用
./deploy.sh restart

# 完全清理（删除容器和镜像）
./deploy.sh cleanup
```

### Docker原生命令 (可选)

如果您想学习原生Docker命令：

```bash
# 查看运行中的容器
docker ps

# 查看所有容器
docker ps -a

# 查看镜像
docker images

# 查看容器日志
docker logs wan-gateway

# 进入容器shell
docker exec -it wan-gateway bash
```

## ☁️ 云端迁移指南

一旦您的应用在本地运行正常，就可以迁移到云端了。

### 选择云平台

我们推荐以下云平台（按易用程度排序）：

#### 1. 🥇 Google Cloud Run (推荐新手)
**优势**: 无服务器，自动扩缩容，按使用付费
**成本**: 免费额度慷慨，之后按请求计费

#### 2. 🥈 阿里云容器服务
**优势**: 国内访问速度快，中文支持
**成本**: 按实例规格计费

#### 3. 🥉 AWS App Runner
**优势**: 全托管，类似Google Cloud Run
**成本**: 按使用付费

### 云端部署步骤

#### Google Cloud Run 部署 (推荐)

1. **安装Google Cloud CLI**:
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # 或下载安装包
   # https://cloud.google.com/sdk/docs/install
   ```

2. **登录并设置项目**:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **构建并推送镜像**:
   ```bash
   # 标记镜像用于Google Container Registry
   docker tag wan-gateway:latest gcr.io/YOUR_PROJECT_ID/wan-gateway
   
   # 推送到Google Container Registry
   docker push gcr.io/YOUR_PROJECT_ID/wan-gateway
   ```

4. **部署到Cloud Run**:
   ```bash
   gcloud run deploy wan-gateway \
     --image gcr.io/YOUR_PROJECT_ID/wan-gateway \
     --platform managed \
     --region asia-east1 \
     --allow-unauthenticated \
     --set-env-vars DASHSCOPE_API_KEY="your_api_key_here" \
     --port 7860
   ```

#### 阿里云容器服务部署

1. **登录阿里云**并创建容器服务集群

2. **推送镜像到阿里云镜像仓库**:
   ```bash
   # 登录阿里云镜像仓库
   docker login --username=your_username registry.cn-hangzhou.aliyuncs.com
   
   # 标记镜像
   docker tag wan-gateway:latest registry.cn-hangzhou.aliyuncs.com/your_namespace/wan-gateway:latest
   
   # 推送镜像
   docker push registry.cn-hangzhou.aliyuncs.com/your_namespace/wan-gateway:latest
   ```

3. **在阿里云控制台创建容器服务**并使用推送的镜像

### 云端环境变量设置

在云平台中，确保设置以下环境变量：
```bash
DASHSCOPE_API_KEY=your_actual_api_key_here
PORT=7860
PYTHONPATH=/app
```

## 🔧 进阶配置

### 自定义端口
如果需要使用不同端口：

1. **修改docker-compose.yml**:
   ```yaml
   ports:
     - "8080:7860"  # 外部端口:内部端口
   ```

2. **或者修改deploy.sh中的PORT变量**

### 持久化存储
如果需要保存生成的视频：

```bash
# 创建本地目录
mkdir -p ./videos ./cache

# 在docker run命令中添加卷挂载
-v "$(pwd)/videos:/app/downloads" \
-v "$(pwd)/cache:/app/cache"
```

### 生产环境优化

1. **使用环境特定的配置文件**:
   ```bash
   # .env.production
   DASHSCOPE_API_KEY=production_api_key
   ```

2. **设置资源限制**:
   ```bash
   docker run --memory="1g" --cpus="1.0" ...
   ```

## 🐛 常见问题解决

### 1. 容器无法启动
```bash
# 查看详细错误信息
./deploy.sh logs

# 或者
docker logs wan-gateway
```

**常见原因**:
- API密钥未设置或无效
- 端口被占用
- Docker内存不足

### 2. 无法访问应用
**检查清单**:
- 容器是否正在运行: `./deploy.sh status`
- 端口是否正确: 默认7860
- 防火墙是否阻止访问

### 3. API调用失败
**解决方案**:
- 验证API密钥是否正确
- 检查网络连接
- 查看API使用限额

### 4. 镜像构建失败
```bash
# 清理Docker缓存
docker system prune -f

# 重新构建
./deploy.sh build
```

### 5. 云端部署失败
**检查清单**:
- 云平台账户权限
- 镜像推送是否成功
- 环境变量是否正确设置
- 区域选择是否合适

## 📚 学习资源

### Docker学习
- [Docker官方教程](https://docs.docker.com/get-started/)
- [Docker中文教程](https://www.runoob.com/docker/docker-tutorial.html)

### 云平台文档
- [Google Cloud Run文档](https://cloud.google.com/run/docs)
- [阿里云容器服务文档](https://help.aliyun.com/product/85222.html)
- [AWS App Runner文档](https://docs.aws.amazon.com/apprunner/)

## 💡 最佳实践

1. **始终使用.env文件**存储敏感信息
2. **定期备份**重要数据
3. **监控**应用性能和日志
4. **使用版本标签**管理Docker镜像
5. **设置健康检查**确保应用可用性

## 📞 获取帮助

如果遇到问题：
1. 查看应用日志: `./deploy.sh logs`
2. 检查Docker状态: `docker ps`
3. 查看系统资源: `docker system df`

---

**恭喜！** 您现在已经学会了如何使用Docker运行应用并迁移到云端。开始您的容器化之旅吧！ 🎉