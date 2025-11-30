# 学生学习平台 API 文档

## 概述

这是一个基于Django的学生课后习题归纳总结应用的后端API，提供了完整的用户认证、错题管理、智能练习和数据分析功能。

**基础URL**: `http://localhost:8000`

**认证方式**: JWT Token (需要在请求头中添加 `Authorization: Bearer <token>`)

---

## 目录

1. [认证相关 API](#认证相关-api)
2. [首页数据 API](#首页数据-api)
3. [习题管理 API](#习题管理-api)
4. [练习训练 API](#练习训练-api)
5. [系统设置 API](#系统设置-api)
6. [错误码说明](#错误码说明)
7. [数据模型说明](#数据模型说明)

---

## 认证相关 API

### 1. 用户注册

**POST** `/api/auth/register/`

注册新用户账号。

**请求参数**:
```json
{
    "username": "student001",
    "password": "password123",
    "password_confirm": "password123",
    "nickname": "小明",
    "birth_date": "2010-05-15",
    "grade_level": 7,
    "email": "student@example.com"
}
```

**响应示例**:
```json
{
    "user": {
        "id": 1,
        "username": "student001",
        "nickname": "小明",
        "email": "student@example.com",
        "birth_date": "2010-05-15",
        "grade_level": 7,
        "user_type": "student",
        "created_at": "2024-01-01T10:00:00Z"
    },
    "tokens": {
        "refresh": "refresh_token_here",
        "access": "access_token_here"
    }
}
```

### 2. 用户登录

**POST** `/api/auth/login/`

用户登录获取访问令牌。

**请求参数**:
```json
{
    "username": "student001",
    "password": "password123"
}
```

**响应示例**:
```json
{
    "user": {
        "id": 1,
        "username": "student001",
        "nickname": "小明",
        "email": "student@example.com",
        "birth_date": "2010-05-15",
        "grade_level": 7,
        "user_type": "student",
        "created_at": "2024-01-01T10:00:00Z"
    },
    "tokens": {
        "refresh": "refresh_token_here",
        "access": "access_token_here"
    }
}
```

### 3. 用户登出

**POST** `/api/auth/logout/`

用户登出，使refresh token失效。

**请求参数**:
```json
{
    "refresh": "refresh_token_here"
}
```

**响应示例**:
```json
{
    "message": "登出成功"
}
```

### 4. 获取用户信息

**GET** `/api/auth/user-info/`

获取当前用户的详细信息。

**响应示例**:
```json
{
    "id": 1,
    "username": "student001",
    "nickname": "小明",
    "email": "student@example.com",
    "birth_date": "2010-05-15",
    "grade_level": 7,
    "user_type": "student",
    "created_at": "2024-01-01T10:00:00Z"
}
```

### 5. 更新用户资料

**PUT/PATCH** `/api/auth/profile/`

更新当前用户的个人信息。

**请求参数**:
```json
{
    "nickname": "小明同学",
    "email": "new_email@example.com",
    "birth_date": "2010-05-15",
    "grade_level": 8
}
```

---

## 首页数据 API

### 1. 获取首页统计数据

**GET** `/api/exercises/dashboard/stats/`

获取学生的学习统计数据和薄弱知识点分析。

**响应示例**:
```json
{
    "total_exercises": 156,
    "mistake_count": 23,
    "practice_count": 15,
    "accuracy_rate": 85.2,
    "subject_stats": [
        {
            "subject_name": "数学",
            "total_exercises": 89,
            "mistake_count": 12,
            "accuracy_rate": 86.5
        },
        {
            "subject_name": "语文",
            "total_exercises": 67,
            "mistake_count": 11,
            "accuracy_rate": 83.6
        }
    ],
    "recent_mistakes": [
        {
            "id": 45,
            "exercise_title": "一元二次方程求解",
            "subject": "数学",
            "upload_time": "2024-01-15 14:30",
            "status": "wrong"
        }
    ],
    "weak_knowledge_points": [
        {
            "knowledge_point": "三角函数",
            "subject": "数学",
            "mastery_level": 45.5,
            "total_attempts": 12,
            "accuracy_rate": 41.7
        }
    ]
}
```

---

## 习题管理 API

### 1. 获取学科列表

**GET** `/api/exercises/subjects/`

获取所有可用的学科列表。

**响应示例**:
```json
[
    {
        "id": 1,
        "name": "数学",
        "description": "数学学科",
        "created_at": "2024-01-01T00:00:00Z"
    },
    {
        "id": 2,
        "name": "语文",
        "description": "语文学科",
        "created_at": "2024-01-01T00:00:00Z"
    }
]
```

### 2. 获取知识点列表

**GET** `/api/exercises/knowledge-points/`

获取知识点列表，可按学科和年级筛选。

**查询参数**:
- `subject`: 学科ID
- `grade_level`: 年级

**响应示例**:
```json
[
    {
        "id": 1,
        "name": "一元二次方程",
        "description": "一元二次方程相关知识点",
        "subject": 1,
        "subject_name": "数学",
        "grade_level": 8,
        "parent": null,
        "created_at": "2024-01-01T00:00:00Z"
    }
]
```

### 3. 上传习题图片

**POST** `/api/exercises/upload/`

上传习题图片，系统将使用VL LLM进行分析和识别。

**请求参数** (multipart/form-data):
- `image`: 图片文件

**响应示例**:
```json
{
    "message": "习题上传分析成功",
    "exercise_id": 123,
    "student_exercise_id": 456,
    "analysis": {
        "subject": "数学",
        "grade_level": 8,
        "knowledge_points": ["一元二次方程"],
        "question_text": "求解方程: x² + 5x + 6 = 0",
        "difficulty": "medium",
        "answer_steps": "使用求根公式...",
        "correct_answer": "x₁ = -2, x₂ = -3",
        "title": "一元二次方程求解"
    }
}
```

### 4. 分析学生答案

**POST** `/api/exercises/analyze-answer/`

分析学生提交的答案，判断是否正确并提供反馈。

**请求参数** (multipart/form-data):
- `exercise_id`: 习题ID
- `answer_image`: 学生答案图片

**响应示例**:
```json
{
    "message": "答案分析完成",
    "is_correct": false,
    "analysis": {
        "student_answer": "x = -1",
        "is_correct": false,
        "confidence": 95,
        "error_analysis": "计算错误，应该使用因式分解法",
        "feedback": "建议复习一元二次方程的解法",
        "solution_quality": "解题步骤不完整"
    }
}
```

### 5. 获取学生错题列表

**GET** `/api/exercises/mistakes/`

获取当前学生的所有错题记录。

**响应示例**:
```json
[
    {
        "id": 1,
        "student": 1,
        "student_nickname": "小明",
        "exercise": 123,
        "exercise_title": "一元二次方程求解",
        "exercise_subject": "数学",
        "student_answer_text": "x = -1",
        "status": "wrong",
        "is_mistake": true,
        "upload_time": "2024-01-15T14:30:00Z"
    }
]
```

---

## 练习训练 API

### 1. 开始练习会话

**POST** `/api/practice/sessions/start/`

开始新的练习会话，系统会智能推荐适合的题目。

**请求参数**:
```json
{
    "subject_id": 1,
    "knowledge_point_ids": [1, 2, 3],
    "difficulty": "medium",
    "question_count": 10
}
```

**响应示例**:
```json
{
    "session_id": 789,
    "recommended_exercises": [
        {
            "exercise": {
                "id": 456,
                "title": "三角函数求值",
                "subject": "数学",
                "difficulty": "medium"
            },
            "weight": 8.5,
            "reason": "这是您之前的错题;涉及您掌握薄弱的知识点"
        }
    ]
}
```

### 2. 提交练习答案

**POST** `/api/practice/submit-answer/`

提交练习题目的答案并获取分析结果。

**请求参数** (multipart/form-data):
- `session_id`: 练习会话ID
- `exercise_id`: 习题ID
- `answer_image`: 答案图片
- `response_time`: 响应时间（秒）

**响应示例**:
```json
{
    "message": "答案提交成功",
    "is_correct": true,
    "analysis": {
        "student_answer": "x₁ = -2, x₂ = -3",
        "is_correct": true,
        "confidence": 98,
        "error_analysis": "",
        "feedback": "解题过程清晰，答案正确！"
    },
    "session_score": 85.5
}
```

### 3. 结束练习会话

**POST** `/api/practice/sessions/end/`

结束当前练习会话并生成最终成绩。

**请求参数**:
```json
{
    "session_id": 789
}
```

**响应示例**:
```json
{
    "message": "练习会话已结束",
    "session": {
        "id": 789,
        "student": 1,
        "student_nickname": "小明",
        "start_time": "2024-01-15T15:00:00Z",
        "end_time": "2024-01-15T15:30:00Z",
        "total_questions": 10,
        "correct_answers": 8,
        "score": 80.0,
        "accuracy_rate": 80.0
    }
}
```

### 4. 获取推荐练习题目

**GET** `/api/practice/recommended/`

获取基于学生情况的智能推荐练习题目。

**查询参数**:
- `subject_id`: 学科ID
- `knowledge_point_ids`: 知识点ID列表
- `difficulty`: 难度等级
- `count`: 题目数量

### 5. 获取知识点掌握程度

**GET** `/api/practice/mastery/`

获取学生在各知识点的掌握程度。

**查询参数**:
- `subject_id`: 学科ID
- `min_mastery`: 最低掌握程度

**响应示例**:
```json
[
    {
        "id": 1,
        "student": 1,
        "knowledge_point": 1,
        "knowledge_point_name": "三角函数",
        "subject_name": "数学",
        "mastery_level": 45.5,
        "total_attempts": 12,
        "correct_attempts": 5,
        "accuracy_rate": 41.7,
        "last_practiced": "2024-01-15T14:30:00Z"
    }
]
```

---

## 系统设置 API

### 1. 获取VL LLM配置列表

**GET** `/api/practice/vllm-config/`

获取VL LLM配置列表（仅管理员可查看所有配置）。

**响应示例**:
```json
[
    {
        "id": 1,
        "name": "默认配置",
        "api_url": "https://api.siliconflow.cn/v1/chat/completions",
        "model_name": "Qwen/Qwen3-VL-32B-Instruct",
        "is_active": true,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
]
```

### 2. 创建VL LLM配置

**POST** `/api/practice/vllm-config/`

创建新的VL LLM配置（仅管理员）。

**请求参数**:
```json
{
    "name": "新配置",
    "api_url": "https://api.example.com/v1/chat/completions",
    "api_key": "your_api_key_here",
    "model_name": "model_name",
    "is_active": false
}
```

### 3. 更新VL LLM配置

**PUT/PATCH** `/api/practice/vllm-config/{id}/`

更新指定的VL LLM配置（仅管理员）。

### 4. 删除VL LLM配置

**DELETE** `/api/practice/vllm-config/{id}/`

删除指定的VL LLM配置（仅管理员）。

---

## 错误码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权，需要登录 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 405 | 请求方法不允许 |
| 500 | 服务器内部错误 |

**常见错误响应示例**:
```json
{
    "error": "用户名或密码错误"
}
```

---

## 数据模型说明

### 用户模型 (User)

```json
{
    "id": 1,
    "username": "student001",
    "nickname": "小明",
    "email": "student@example.com",
    "birth_date": "2010-05-15",
    "grade_level": 7,
    "user_type": "student|admin",
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
}
```

### 学科模型 (Subject)

```json
{
    "id": 1,
    "name": "数学",
    "description": "数学学科",
    "created_at": "2024-01-01T00:00:00Z"
}
```

### 知识点模型 (KnowledgePoint)

```json
{
    "id": 1,
    "name": "一元二次方程",
    "description": "一元二次方程相关知识点",
    "subject": 1,
    "grade_level": 8,
    "parent": null,
    "created_at": "2024-01-01T00:00:00Z"
}
```

### 习题模型 (Exercise)

```json
{
    "id": 1,
    "title": "一元二次方程求解",
    "question_text": "求解方程: x² + 5x + 6 = 0",
    "answer_steps": "使用求根公式...",
    "answer_text": "x₁ = -2, x₂ = -3",
    "subject": 1,
    "grade_level": 8,
    "difficulty": "easy|medium|hard",
    "total_attempts": 50,
    "correct_attempts": 35,
    "accuracy_rate": 70.0
}
```

### 练习会话模型 (PracticeSession)

```json
{
    "id": 1,
    "student": 1,
    "start_time": "2024-01-15T15:00:00Z",
    "end_time": "2024-01-15T15:30:00Z",
    "total_questions": 10,
    "correct_answers": 8,
    "score": 80.0,
    "accuracy_rate": 80.0
}
```

---

## 小程序集成说明

### 1. 基础配置

```javascript
const API_BASE_URL = 'http://localhost:8000/api';

// 设置请求拦截器，添加认证头
function getAuthHeader() {
    const token = wx.getStorageSync('access_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// 封装网络请求
function request(url, options = {}) {
    return new Promise((resolve, reject) => {
        wx.request({
            url: `${API_BASE_URL}${url}`,
            method: options.method || 'GET',
            data: options.data,
            header: {
                'Content-Type': 'application/json',
                ...getAuthHeader(),
                ...options.header
            },
            success: resolve,
            fail: reject
        });
    });
}
```

### 2. 文件上传封装

```javascript
function uploadFile(filePath, additionalData = {}) {
    return new Promise((resolve, reject) => {
        wx.uploadFile({
            url: `${API_BASE_URL}/exercises/upload/`,
            filePath: filePath,
            name: 'image',
            formData: additionalData,
            header: getAuthHeader(),
            success: (res) => {
                const data = JSON.parse(res.data);
                resolve(data);
            },
            fail: reject
        });
    });
}
```

### 3. API调用示例

```javascript
// 用户登录
async function login(username, password) {
    const response = await request('/auth/login/', {
        method: 'POST',
        data: { username, password }
    });

    // 保存token
    wx.setStorageSync('access_token', response.tokens.access);
    wx.setStorageSync('refresh_token', response.tokens.refresh);
    wx.setStorageSync('user_info', response.user);

    return response;
}

// 获取首页数据
async function getDashboardStats() {
    return await request('/exercises/dashboard/stats/');
}

// 上传习题
async function uploadExercise(imagePath) {
    return await uploadFile(imagePath);
}

// 开始练习
async function startPractice(options) {
    return await request('/practice/sessions/start/', {
        method: 'POST',
        data: options
    });
}
```

### 4. Token刷新机制

```javascript
// 检查token是否过期
async function checkAndRefreshToken() {
    const token = wx.getStorageSync('access_token');
    if (!token) {
        throw new Error('未登录');
    }

    // 这里可以添加token过期检查逻辑
    // 如果过期，使用refresh_token获取新的token

    return token;
}

// 请求前检查token
async function authenticatedRequest(url, options = {}) {
    await checkAndRefreshToken();
    return await request(url, options);
}
```

### 5. 错误处理

```javascript
function handleApiError(error) {
    console.error('API Error:', error);

    if (error.statusCode === 401) {
        // 未授权，跳转到登录页
        wx.redirectTo({ url: '/pages/login/login' });
    } else if (error.statusCode === 403) {
        wx.showToast({ title: '权限不足', icon: 'none' });
    } else {
        const message = error.data?.error || '网络错误，请重试';
        wx.showToast({ title: message, icon: 'none' });
    }
}
```

---

## 部署说明

### 1. 环境要求

- Python 3.8+
- Django 4.2.7
- PostgreSQL/MySQL (推荐) 或 SQLite (开发环境)

### 2. 安装步骤

```bash
# 克隆项目
git clone <repository_url>
cd student_learning_platform

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export DJANGO_SECRET_KEY='your-secret-key'
export DATABASE_URL='your-database-url'

# 数据库迁移
python manage.py migrate

# 创建管理员
python manage.py init_admin

# 启动服务
python manage.py runserver 0.0.0.0:8000
```

### 3. 生产环境配置

- 使用Nginx + Gunicorn部署
- 配置HTTPS
- 设置环境变量
- 配置数据库连接池
- 设置日志记录
- 配置缓存（Redis）

---

## 联系方式

如有问题或建议，请联系开发团队。