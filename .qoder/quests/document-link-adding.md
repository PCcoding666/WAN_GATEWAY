# 文档链接添加和目录整理方案

## 概述

本方案旨在实现以下目标：
1. 在每个英文文档的开头添加链接，指向对应的中文文档
2. 将根目录下的所有 Markdown 文档（除 README.md 外）移入 doc 目录
3. 创建 production 目录来管理生产相关的文件
4. 保持根目录整洁

## 实施步骤

### 1. 创建生产环境目录
首先创建 production 目录来管理生产相关的文件：

```bash
mkdir production
```

### 2. 移动生产相关脚本
将生产部署脚本移入 production 目录：

```bash
mv deploy-production.sh production/
```

### 3. 移动文档到 doc 目录
将根目录下除 README.md 外的所有 Markdown 文档移入 doc 目录：

```bash
mv API.md doc/
mv CHANGELOG.md doc/
mv CONTRIBUTING.md doc/
mv DEPLOYMENT.md doc/
```

### 4. 在英文文档中添加中文文档链接

## 当前状态分析

### 根目录文件结构
```
.
├── API.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── DEPLOYMENT.md
├── README.md
├── deploy-production.sh
```

### doc 目录文件结构
```
doc/
├── API_zh.md
├── CHANGELOG_zh.md
├── CONTRIBUTING_zh.md
├── DEPLOYMENT_zh.md
├── README_zh.md
```
在每个英文文档的开头添加指向对应中文文档的链接：

#### README.md
在文件开头添加：
```markdown
[查看中文文档](doc/README_zh.md)

# 🎬 Wan Gateway - Multi-Modal Video Generator
```

#### doc/API.md
在文件开头添加：
```markdown
[查看中文文档](API_zh.md)

# 📡 Wan Gateway API Documentation
```

#### doc/DEPLOYMENT.md
在文件开头添加：
```markdown
[查看中文文档](DEPLOYMENT_zh.md)

# 🚀 Wan Gateway Deployment Guide
```

#### doc/CONTRIBUTING.md
在文件开头添加：
```markdown
[查看中文文档](CONTRIBUTING_zh.md)

# 🤝 Contributing Guide
```

#### doc/CHANGELOG.md
在文件开头添加：
```markdown
[查看中文文档](CHANGELOG_zh.md)

# 📝 Wan Gateway Changelog
```

## 最终目录结构

实施后的目录结构将如下所示：

```
.
├── doc/
│   ├── API.md (添加了链接)
│   ├── API_zh.md
│   ├── CHANGELOG.md (添加了链接)
│   ├── CHANGELOG_zh.md
│   ├── CONTRIBUTING.md (添加了链接)
│   ├── CONTRIBUTING_zh.md
│   ├── DEPLOYMENT.md (添加了链接)
│   ├── DEPLOYMENT_zh.md
│   └── README_zh.md
├── production/
│   └── deploy-production.sh
├── README.md (添加了链接)
└── [其他文件]
```

## 实施计划

1. 创建 production 目录
2. 移动 deploy-production.sh 到 production 目录
3. 移动根目录的 Markdown 文档到 doc 目录（保留 README.md）
4. 更新各个英文文档，在开头添加指向对应中文文档的链接
5. 验证所有链接是否正确工作

## 注意事项

1. 确保所有文档链接正确无误
2. 验证文档中的相对链接仍然有效
3. 确保移动文件后，项目中的引用路径相应更新
4. 保持文档内容与实际代码实现的一致性

## 验证步骤

1. 检查所有文档链接是否能正确跳转
2. 验证移动后的文件路径是否正确
3. 确认项目中的文档引用是否更新
4. 测试生产环境部署脚本是否正常工作

## 总结

通过以上步骤，我们可以实现：
1. 保持根目录整洁，只保留 README.md 文件
2. 将所有英文文档移入 doc 目录并与中文文档对应
3. 在每个英文文档开头添加指向中文文档的链接
4. 将生产相关文件放入 production 目录统一管理
5. 确保项目结构清晰，便于维护和扩展