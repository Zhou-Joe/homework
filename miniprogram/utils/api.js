// API请求工具
const app = getApp();

class ApiClient {
  constructor() {
    this.baseUrl = app.globalData.apiBaseUrl;
    this.token = app.globalData.token;
  }

  // 获取请求头
  getHeaders(url = '') {
    const headers = {
      'Content-Type': 'application/json'
    };

    // 登录相关的请求不应该带上Authorization头
    const isAuthEndpoint = url.includes('/auth/login') || url.includes('/auth/unified-login') || 
                          url.includes('/auth/register') || url.includes('/auth/token/refresh');
    
    if (!isAuthEndpoint && (this.token || app.globalData.token)) {
      headers['Authorization'] = `Bearer ${this.token || app.globalData.token}`;
    }

    return headers;
  }

  // GET请求
  get(url, data = {}) {
    return this.request('GET', url, data);
  }

  // POST请求
  post(url, data = {}) {
    return this.request('POST', url, data);
  }

  // PUT请求
  put(url, data = {}) {
    return this.request('PUT', url, data);
  }

  // DELETE请求
  delete(url, data = {}) {
    return this.request('DELETE', url, data);
  }

  // 上传文件（习题图片）
  upload(url, filePath, formData = {}) {
    return new Promise((resolve, reject) => {
      const header = {};
      
      // 登录相关的请求不应该带上Authorization头
      const isAuthEndpoint = url.includes('/auth/login') || url.includes('/auth/unified-login') || 
                            url.includes('/auth/register') || url.includes('/auth/token/refresh');
      
      if (!isAuthEndpoint && (this.token || app.globalData.token)) {
        header['Authorization'] = `Bearer ${this.token || app.globalData.token}`;
      }

      wx.uploadFile({
        url: `${this.baseUrl}${url}`,
        filePath: filePath,
        name: 'image', // 修复字段名，与后端upload_exercise期望一致
        formData: formData,
        header: header,
        success: (res) => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            try {
              const data = JSON.parse(res.data);
              resolve(data);
            } catch (e) {
              resolve(res.data);
            }
          } else {
            try {
              const errorData = JSON.parse(res.data);
              reject({
                statusCode: res.statusCode,
                message: errorData.error || errorData.detail || '请求失败'
              });
            } catch (e) {
              reject({
                statusCode: res.statusCode,
                message: '请求失败'
              });
            }
          }
        },
        fail: (err) => {
          reject({
            message: '网络请求失败',
            error: err
          });
        }
      });
    });
  }

  // 上传答案图片
  uploadAnswer(url, filePath, formData = {}) {
    return new Promise((resolve, reject) => {
      const header = {};
      
      // 登录相关的请求不应该带上Authorization头
      const isAuthEndpoint = url.includes('/auth/login') || url.includes('/auth/unified-login') || 
                            url.includes('/auth/register') || url.includes('/auth/token/refresh');
      
      if (!isAuthEndpoint && (this.token || app.globalData.token)) {
        header['Authorization'] = `Bearer ${this.token || app.globalData.token}`;
      }

      wx.uploadFile({
        url: `${this.baseUrl}${url}`,
        filePath: filePath,
        name: 'answer_image', // 用于答案图片上传
        formData: formData,
        header: header,
        success: (res) => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            try {
              const data = JSON.parse(res.data);
              resolve(data);
            } catch (e) {
              resolve(res.data);
            }
          } else {
            try {
              const errorData = JSON.parse(res.data);
              reject({
                statusCode: res.statusCode,
                message: errorData.error || errorData.detail || '请求失败'
              });
            } catch (e) {
              reject({
                statusCode: res.statusCode,
                message: '请求失败'
              });
            }
          }
        },
        fail: (err) => {
          reject({
            message: '网络请求失败',
            error: err
          });
        }
      });
    });
  }

  // 通用请求方法
  request(method, url, data = {}) {
    return new Promise((resolve, reject) => {
      const requestUrl = `${this.baseUrl}${url}`;
      console.log(`API请求: ${method} ${requestUrl}`, {
        data: data,
        headers: this.getHeaders()
      });

      wx.request({
        url: requestUrl,
        method: method,
        header: this.getHeaders(url),
        data: data,
        success: (res) => {
          console.log(`API响应: ${method} ${requestUrl}`, {
            statusCode: res.statusCode,
            data: res.data
          });

          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(res.data);
          } else if (res.statusCode === 401) {
            // 401错误处理 - 登录接口不应该清除token，其他接口才需要清除
            if (url.includes('/auth/login') || url.includes('/auth/unified-login')) {
              // 登录接口的401错误，直接返回错误信息
              reject({
                statusCode: res.statusCode,
                message: res.data.error || res.data.detail || '用户名或密码错误',
                data: res.data
              });
            } else {
              // 其他接口的401错误，可能是token过期
              wx.removeStorageSync('token');
              wx.removeStorageSync('access_token');
              wx.removeStorageSync('refresh_token');
              app.globalData.token = null;
              app.globalData.userInfo = null;
              
              // 延迟重定向，避免干扰当前请求的错误处理
              setTimeout(() => {
                wx.redirectTo({
                  url: '/pages/login/login'
                });
              }, 1000);
              
              reject({
                statusCode: res.statusCode,
                message: '登录已过期，请重新登录',
                data: res.data
              });
            }
          } else {
            reject({
              statusCode: res.statusCode,
              message: res.data.error || res.data.detail || '请求失败',
              data: res.data
            });
          }
        },
        fail: (err) => {
          console.error(`API请求失败: ${method} ${requestUrl}`, err);
          reject({
            message: '网络请求失败',
            error: err
          });
        }
      });
    });
  }
}

// 导出API实例
const api = new ApiClient();

// 用户认证API - 更新版本v3.0（支持统一登录）
const authAPI = {
  // 传统登录
  login: (username, password) => {
    console.log('AUTH API - 登录请求:', {
      url: '/auth/login/',
      username,
      password: '***'
    });

    return api.post('/auth/login/', {
      username: username,
      password: password
    });
  },

  // 统一登录接口 - 支持密码和微信两种方式
  unifiedLogin: (loginType, data) => {
    console.log('AUTH API - 统一登录请求:', {
      url: '/auth/unified-login/',
      loginType,
      data: loginType === 'password' ? { username: data.username, password: '***' } : { code: data.code, userInfo: data.userInfo }
    });

    const requestData = {
      login_type: loginType
    };

    if (loginType === 'password') {
      requestData.username = data.username;
      requestData.password = data.password;
    } else if (loginType === 'wechat') {
      requestData.code = data.code;
      requestData.user_info = data.userInfo || {};
    }

    return api.post('/auth/unified-login/', requestData);
  },

  // 注册
  register: (userData) => {
    console.log('AUTH API - 注册请求:', {
      url: '/auth/register/',
      userData: { ...userData, password: '***' }
    });

    return api.post('/auth/register/', userData);
  },

  // 微信登录（独立接口）
  wechatLogin: (code, userInfo = {}) => {
    console.log('AUTH API - 微信登录请求:', {
      url: '/auth/wechat/login/',
      code: code,
      userInfo: userInfo
    });

    return api.post('/auth/wechat/login/', {
      code: code,
      user_info: userInfo
    });
  },

  // 绑定微信账号
  bindWechat: (code) => {
    console.log('AUTH API - 绑定微信请求:', {
      url: '/auth/wechat/bind/',
      code: code
    });

    return api.post('/auth/wechat/bind/', {
      code: code
    });
  },

  // 解绑微信账号
  unbindWechat: () => {
    console.log('AUTH API - 解绑微信请求:', {
      url: '/auth/wechat/unbind/'
    });

    return api.post('/auth/wechat/unbind/');
  },

  // 刷新token
  refreshToken: (refreshToken) => {
    return api.post('/auth/token/refresh/', {
      refresh: refreshToken
    });
  },

  // 获取用户信息
  getUserInfo: () => {
    return api.get('/auth/user-info/');
  },

  // 获取用户资料
  getProfile: () => {
    return api.get('/auth/profile/');
  },

  // 更新用户资料
  updateProfile: (userData) => {
    return api.put('/auth/profile/', userData);
  },

  // 退出登录
  logout: (refreshToken) => {
    return api.post('/auth/logout/', {
      refresh: refreshToken
    });
  }
};

// 习题API
const exerciseAPI = {
  // 上传习题
  uploadExercise: (filePath) => {
    return api.upload('/exercises/upload/', filePath);
  },

  // 获取学科列表
  getSubjects: () => {
    return api.get('/exercises/subjects/');
  },

  // 获取知识点列表
  getKnowledgePoints: () => {
    return api.get('/exercises/knowledge-points/');
  },

  // 获取学生习题列表
  getStudentExercises: (params = {}) => {
    return api.get('/exercises/student-exercises/', params);
  },

  // 获取错题列表
  getMistakes: (params = {}) => {
    return api.get('/exercises/mistakes/', params);
  },

  // 获取习题详情
  getExerciseDetail: (id) => {
    return api.get(`/exercises/${id}/`);
  },

  // 保存习题
  saveExercise: (exerciseId) => {
    return api.post('/exercises/student-exercises/', {
      exercise: exerciseId,
      status: 'not_attempted',
      is_mistake: true
    });
  }
};

// 练习API
const practiceAPI = {
  // 开始练习会话
  startSession: (data) => {
    return api.post('/practice/sessions/start/', data);
  },

  // 获取推荐题目
  getRecommendedExercises: (params = {}) => {
    return api.get('/practice/recommended/', params);
  },

  // 获取练习历史
  getPracticeHistory: (params = {}) => {
    return api.get('/practice/sessions/', params);
  },

  // 提交答案 - 修复版本v2.0
  submitAnswer: (sessionId, questionId, answerData) => {
    console.log('API调用 - 提交答案:', {
      url: '/practice/submit-answer/',
      sessionId,
      questionId,
      answerData
    });

    return api.post('/practice/submit-answer/', {
      session_id: sessionId,
      exercise_id: questionId,
      ...answerData
    });
  },

  // 异步提交答案（推荐使用）- 修复版本v2.0
  submitAnswerAsync: (sessionId, questionId, answerData) => {
    console.log('API调用 - 异步提交答案:', {
      url: '/practice/submit-answer-async/',
      sessionId,
      questionId,
      answerData
    });

    return api.post('/practice/submit-answer-async/', {
      session_id: sessionId,
      exercise_id: questionId,
      ...answerData
    });
  },

  // 完成练习会话
  completeSession: (sessionId) => {
    return api.post('/practice/sessions/end/', {
      session_id: sessionId
    });
  },

  // 获取练习统计
  getPracticeStats: () => {
    return api.get('/practice/stats/');
  },

  // 获取练习结果
  getPracticeResult: (sessionId) => {
    return api.get(`/practice/sessions/${sessionId}/`);
  },

  // 获取答题记录
  getPracticeRecords: (sessionId) => {
    return api.get(`/practice/records/?session_id=${sessionId}`);
  },

  // 获取AI分析状态
  getAnalysisStatus: (sessionId) => {
    return api.get(`/practice/sessions/${sessionId}/analysis-status/`);
  },

  // 获取知识点得分
  getKnowledgePointScores: (sessionId) => {
    let url = '/practice/knowledge-points/';
    if (sessionId) {
      url += `?session_id=${sessionId}`;
    }
    return api.get(url);
  }
};

// 统计API
const statsAPI = {
  // 获取学习统计数据
  getDashboardStats: () => {
    return api.get('/practice/stats/');
  },

  // 获取学科统计
  getSubjectStats: () => {
    return api.get('/practice/subject-stats/');
  },

  // 获取薄弱知识点
  getWeakKnowledgePoints: () => {
    return api.get('/practice/weak-knowledge-points/');
  },

  // 获取最近错题
  getRecentMistakes: () => {
    return api.get('/exercises/mistakes/');
  }
};

// 导出所有API
module.exports = {
  api,
  authAPI,
  exerciseAPI,
  practiceAPI,
  statsAPI
};