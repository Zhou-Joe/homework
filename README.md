# 学生学习平台

一个基于Django的学生课后习题归纳总结应用，支持智能错题分析和个性化练习推荐。

## 功能特点

### 🔐 用户认证
- 学生注册/登录
- 管理员权限管理
- JWT Token认证

### 📊 数据统计
- 个人学习数据分析
- 分学科错题统计
- 知识点掌握程度评估
- 学习进度跟踪

### 📸 智能错题识别
- 支持PDF和图片上传
- VL LLM智能识别题目内容
- 自动匹配知识点
- 生成详细解题步骤

### 🎯 个性化练习
- 基于薄弱环节智能推荐题目
- 错题重练
- 答题质量分析
- 实时反馈

### ⚙️ 系统管理
- VL LLM配置管理
- 学科和知识点管理
- 后台数据管理

## 技术栈

- **后端**: Django 4.2.7 + Django REST Framework
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **AI服务**: SiliconFlow VL LLM API
- **认证**: JWT Token
- **文件处理**: Pillow
- **部署**: Docker + Nginx + Gunicorn

## 快速开始

### 1. 环境准备

```bash
# 确保Python 3.8+
python --version

# 克隆项目
git clone <repository_url>
cd student_learning_platform
```

### 2. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 数据库初始化

```bash
# 执行数据库迁移
python manage.py migrate

# 创建管理员用户 (默认: admin/admin123)
python manage.py init_admin
```

### 4. 启动服务

```bash
# 启动开发服务器
python manage.py runserver 0.0.0.0:8000
```

服务启动后，访问：
- API根地址: http://localhost:8000/
- 管理后台: http://localhost:8000/admin/
- API文档: 查看 `API_DOCUMENTATION.md`

## API使用示例

### 1. 用户注册

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "student001",
    "password": "password123",
    "password_confirm": "password123",
    "nickname": "小明",
    "birth_date": "2010-05-15",
    "grade_level": 7
  }'
```

### 2. 用户登录

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "student001",
    "password": "password123"
  }'
```

### 3. 获取首页数据

```bash
curl -X GET http://localhost:8000/api/exercises/dashboard/stats/ \
  -H "Authorization: Bearer <your_access_token>"
```

## 项目结构

```
student_learning_platform/
├── accounts/                 # 用户管理应用
│   ├── models.py            # 用户模型
│   ├── views.py             # 用户相关API
│   ├── serializers.py       # 序列化器
│   └── admin.py             # 后台管理
├── exercises/               # 习题管理应用
│   ├── models.py            # 习题相关模型
│   ├── views.py             # 习题相关API
│   ├── vllm_service.py      # VL LLM服务
│   ├── serializers.py       # 序列化器
│   └── admin.py             # 后台管理
├── practice/                # 练习训练应用
│   ├── models.py            # 练习相关模型
│   ├── views.py             # 练习相关API
│   ├── serializers.py       # 序列化器
│   └── admin.py             # 后台管理
├── media/                   # 媒体文件存储
│   └── uploads/             # 上传文件目录
│       ├── questions/       # 题目图片
│       └── answers/         # 答案图片
├── student_learning_platform/  # 项目配置
│   ├── settings.py          # Django设置
│   ├── urls.py              # URL路由
│   └── wsgi.py              # WSGI配置
├── manage.py                # Django管理脚本
├── requirements.txt         # 依赖包列表
├── README.md               # 项目说明
└── API_DOCUMENTATION.md    # API文档
```

## 默认配置

### 管理员账号
- 用户名: `admin`
- 密码: `admin123`

### VL LLM配置
- API地址: `https://api.siliconflow.cn/v1/chat/completions`
- API密钥: `sk-hglnfzrlezgqtiionjdduvqrfmwfpjnkdksfizvnpseqvlwu`
- 模型: `Qwen/Qwen3-VL-32B-Instruct`

## 环境变量配置

创建 `.env` 文件：

```env
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# 数据库配置 (生产环境)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# VL LLM配置 (可选覆盖默认值)
VLLM_API_URL=https://api.siliconflow.cn/v1/chat/completions
VLLM_API_KEY=your-api-key
VLLM_MODEL_NAME=Qwen/Qwen3-VL-32B-Instruct
```

## 小程序集成

本项目专门为小程序提供了完整的API接口，包括：

1. **用户认证API** - 注册、登录、获取用户信息
2. **文件上传API** - 上传习题图片和答案图片
3. **数据分析API** - 获取学习统计数据和薄弱点分析
4. **练习API** - 智能题目推荐和答案分析
5. **配置API** - VL LLM配置管理（仅管理员）

详细的小程序集成指南请参考 [API_DOCUMENTATION.md](API_DOCUMENTATION.md) 中的"小程序集成说明"部分。

## 开发指南

### 添加新的学科

1. 在管理后台添加学科
2. 为学科添加相关知识点
3. 系统会自动支持新学科的题目识别

### 自定义VL LLM

1. 登录管理后台
2. 进入"VL LLM配置"管理
3. 添加新的配置并设置为启用

### 扩展功能

项目采用模块化设计，可以方便地扩展新功能：

- 在 `accounts/` 应用中添加用户相关功能
- 在 `exercises/` 应用中添加习题相关功能
- 在 `practice/` 应用中添加练习相关功能

## 部署指南

### Docker部署

```bash
# 构建镜像
docker build -t student-learning-platform .

# 运行容器
docker run -p 8000:8000 student-learning-platform
```

### 生产环境

推荐使用以下部署方案：

1. **Web服务器**: Nginx
2. **应用服务器**: Gunicorn
3. **数据库**: PostgreSQL
4. **缓存**: Redis
5. **进程管理**: Supervisor

详细部署配置请联系开发团队。

## 常见问题

### Q: 如何修改默认密码策略？
A: 在 `settings.py` 中修改 `AUTH_PASSWORD_VALIDATORS` 配置。

### Q: 如何更换VL LLM服务？
A: 在管理后台的"VL LLM配置"中添加新配置，或修改 `settings.py` 中的默认配置。

### Q: 如何备份数据？
A: 使用 `python manage.py dumpdata > backup.json` 命令备份数据。

### Q: 如何升级版本？
A: 运行 `pip install -r requirements.txt` 更新依赖，然后执行 `python manage.py migrate` 更新数据库。

## 贡献指南

欢迎提交Issue和Pull Request来改进项目。

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 技术支持

如有技术问题，请通过以下方式联系：

- 提交GitHub Issue
- 发送邮件至开发团队
- 查看API文档和代码注释

---

**注意**: 本项目仅供学习和研究使用，请勿用于商业用途。