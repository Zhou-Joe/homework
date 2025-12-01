# 微信小程序与Django API集成说明

## 项目概述

这是一个基于Django后端的智能学习平台微信小程序，支持以下核心功能：

### 🎯 核心功能
- **用户认证**：登录、退出登录
- **练习功能**：AI智能推荐题目、异步AI分析
- **结果查看**：实时AI分析状态、详细练习结果
- **题目上传**：图片上传、AI智能分析
- **个人中心**：学习统计、练习历史

### 📱 小程序页面结构

```
miniprogram/
├── pages/
│   ├── login/              # 登录页面
│   ├── index/              # 首页
│   ├── practice/           # 练习页面
│   ├── practice-result/     # 练习结果页面 (新增)
│   ├── upload/             # 上传页面
│   └── profile/            # 个人资料页面 (已更新)
├── utils/
│   └── api.js             # API工具类 (已更新)
├── app.js                 # 小程序入口 (已更新)
├── app.json               # 页面配置 (已更新)
└── README.md              # 说明文档
```

## 🔧 配置说明

### 1. API基础URL配置

在 `app.js` 中配置后端API地址：

```javascript
globalData: {
  userInfo: null,
  token: null,
  apiBaseUrl: 'http://127.0.0.1:8000/api',  // 开发环境（当前使用）
  // 生产环境使用线上地址
  // apiBaseUrl: 'https://www.zctestbench.asia/api'
}
```

### 2. 服务器域名配置

在微信小程序管理后台配置以下域名：

**开发环境配置**：
```
request合法域名：
- http://127.0.0.1:8000   (开发环境，需要开启"不校验合法域名")

uploadFile合法域名：
- http://127.0.0.1:8000   (开发环境)

downloadFile合法域名：
- http://127.0.0.1:8000   (开发环境)
```

**生产环境配置**：
```
request合法域名：
- https://www.zctestbench.asia  (生产环境)

uploadFile合法域名：
- https://www.zctestbench.asia  (生产环境)

downloadFile合法域名：
- https://www.zctestbench.asia  (生产环境)
```

## 🚀 功能测试步骤

### 1. 用户登录测试
1. 打开小程序，自动跳转到登录页面
2. 输入用户名和密码
3. 验证登录成功后跳转到首页
4. 检查token是否正确保存

### 2. 练习功能测试
1. 在首页点击"练习"tab
2. 选择练习模式、学科、题目数量
3. 点击"开始练习"
4. 答题并提交答案（文字/图片）
5. 查看AI分析结果
6. 完成练习后自动跳转到结果页面

### 3. 练习结果测试
1. 在结果页面查看总体成绩
2. 查看详细统计数据
3. 观察AI分析状态提示
4. 点击题目查看详细分析
5. 测试自动刷新功能

### 4. 题目上传测试
1. 点击"上传"tab
2. 选择图片文件
3. 点击"上传并分析"
4. 查看AI分析结果
5. 保存到错题本

### 5. 个人中心测试
1. 查看用户信息和学习统计
2. 点击"练习历史"查看记录
3. 点击最近练习查看详情
4. 测试退出登录功能

## 🔗 API接口对应关系

### 认证相关
- `POST /auth/login/` - 用户登录
- `GET /auth/user-info/` - 获取用户信息
- `POST /auth/logout/` - 退出登录

### 练习相关
- `POST /practice/sessions/start/` - 开始练习会话
- `GET /practice/recommended/` - 获取推荐题目
- `POST /practice/submit-answer-async/` - 异步提交答案
- `POST /practice/sessions/end/` - 完成练习会话
- `GET /practice/sessions/{id}/` - 获取练习结果
- `GET /practice/records/` - 获取答题记录
- `GET /practice/sessions/{id}/analysis-status/` - 获取AI分析状态

### 题目相关
- `POST /exercises/upload/` - 上传题目图片
- `GET /exercises/subjects/` - 获取学科列表
- `GET /exercises/knowledge-points/` - 获取知识点列表

### 统计相关
- `GET /exercises/dashboard/stats/` - 获取仪表板统计
- `GET /practice/stats/` - 获取练习统计

## 🛠️ 开发调试

### 1. 本地开发环境
- 确保Django服务运行在 `http://127.0.0.1:8000` (当前配置)
- 使用真机调试时需要配置代理
- 在微信开发者工具中需要开启"不校验合法域名"选项

### 2. 常见问题解决

#### Token过期处理
- 自动检测401错误
- 清除本地token并跳转到登录页面
- 支持token刷新机制

#### 网络请求失败
- 统一错误处理
- 友好的错误提示
- 支持重试机制

#### 文件上传限制
- 图片大小限制10MB
- 支持jpg、png、gif格式
- 压缩上传优化

### 3. 日志调试
```javascript
// 在API工具中启用详细日志
console.log('API请求:', { url, method, data });
console.log('API响应:', response);
console.log('API错误:', error);
```

## 📱 小程序特性

### 1. 用户体验优化
- 加载状态提示
- 错误信息友好展示
- 操作反馈及时
- 页面切换流畅

### 2. 数据缓存
- 用户信息本地缓存
- 练习记录本地存储
- 网络状态检测

### 3. 性能优化
- 图片压缩上传
- 请求防重复提交
- 页面预加载
- 数据懒加载

## 🔄 版本更新记录

### v2.0 (2025-11-29)
- ✅ 新增练习结果页面
- ✅ 实现AI分析状态实时显示
- ✅ 优化异步提交答案功能
- ✅ 更新个人资料页面
- ✅ 完善API工具类
- ✅ 修复页面跳转逻辑

### v1.0 (2025-11-28)
- ✅ 基础登录功能
- ✅ 练习功能框架
- ✅ 题目上传功能
- ✅ 个人中心页面

## 📞 技术支持

如有问题，请检查：
1. Django服务是否正常运行
2. API接口是否可访问
3. 小程序配置是否正确
4. 网络连接是否正常

## 🎯 后续优化计划

1. **性能优化**
   - 图片懒加载
   - 数据分页加载
   - 缓存策略优化

2. **功能增强**
   - 错题本页面
   - 知识点详情页面
   - 学习报告功能

3. **用户体验**
   - 暗色模式支持
   - 主题自定义
   - 动画效果优化