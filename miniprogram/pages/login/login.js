// pages/login/login.js
const { authAPI } = require('../../utils/api');
const app = getApp();

Page({
  data: {
    username: '',
    password: '',
    isLoading: false
  },

  onLoad: function(options) {
    // 检查微信小程序配置
    this.checkWechatConfig();
    
    // 检查是否已登录
    if (app.globalData.token) {
      wx.switchTab({
        url: '/pages/index/index'
      });
    }
  },

  // 检查微信小程序配置
  checkWechatConfig: function() {
    try {
      const accountInfo = wx.getAccountInfoSync();
      console.log('小程序信息:', {
        appId: accountInfo.appId,
        env: accountInfo.miniProgram.envVersion
      });

      // 检查是否在微信环境中
      if (!accountInfo.appId || accountInfo.appId === 'touristappid') {
        wx.showToast({
          title: '请在微信中打开小程序',
          icon: 'none',
          duration: 3000
        });
        return;
      }

      console.log('微信小程序配置正常');
    } catch (error) {
      console.error('获取小程序配置失败:', error);
      wx.showToast({
        title: '小程序配置错误',
        icon: 'none',
        duration: 3000
      });
    }
  },

  // 用户名输入
  onUsernameInput: function(e) {
    this.setData({
      username: e.detail.value
    });
  },

  // 密码输入
  onPasswordInput: function(e) {
    this.setData({
      password: e.detail.value
    });
  },

  // 密码登录
  onPasswordLogin: async function() {
    const { username, password } = this.data;

    if (!username || !password) {
      wx.showToast({
        title: '请填写用户名和密码',
        icon: 'none'
      });
      return;
    }

    this.setData({ isLoading: true });

    try {
      console.log('开始密码登录:', { username, password: '***' });
      console.log('API基础URL:', app.globalData.apiBaseUrl);

      // 调用统一登录API - 密码登录方式
      const res = await authAPI.unifiedLogin('password', {
        username: username,
        password: password
      });

      console.log('登录响应:', res);

      if (res.tokens && res.tokens.access) {
        console.log('登录成功，保存token');

        // 保存token和用户信息
        const access = res.tokens.access;
        const refresh = res.tokens.refresh;
        const userInfo = res.user;

        wx.setStorageSync('access_token', access);
        wx.setStorageSync('refresh_token', refresh);
        wx.setStorageSync('user_info', userInfo);
        wx.setStorageSync('login_type', res.login_type);

        app.globalData.token = access;
        app.globalData.userInfo = userInfo;
        app.globalData.loginType = res.login_type;

        wx.showToast({
          title: '登录成功',
          icon: 'success',
          duration: 1500
        });

        // 跳转到首页
        setTimeout(() => {
          wx.switchTab({
            url: '/pages/index/index'
          });
        }, 1500);
      } else {
        console.error('登录响应格式错误:', res);
        throw new Error('登录响应格式错误');
      }
    } catch (error) {
      console.error('登录失败详细信息:', {
        message: error.message,
        statusCode: error.statusCode,
        data: error.data,
        stack: error.stack
      });
      
      let errorMsg = '登录失败，请检查用户名和密码';
      if (error.statusCode === 401) {
        // 401错误可能是用户名密码错误，也可能是其他认证问题
        if (error.data && error.data.error) {
          errorMsg = error.data.error;
        } else {
          errorMsg = '用户名或密码错误';
        }
      } else if (error.statusCode === 404) {
        errorMsg = '登录接口不存在，请联系管理员';
      } else if (error.statusCode >= 500) {
        errorMsg = '服务器错误，请稍后重试';
      } else if (error.message) {
        errorMsg = error.message;
      }
      
      wx.showToast({
        title: errorMsg,
        icon: 'none',
        duration: 3000
      });
    } finally {
      this.setData({ isLoading: false });
    }
  },

  // 微信登录
  onWechatLogin: async function() {
    wx.showLoading({
      title: '微信登录中...'
    });

    try {
      // 获取微信登录code
      console.log('开始调用wx.login...');
      const loginRes = await this.wxLogin();
      console.log('wx.login结果:', loginRes);

      if (loginRes.code) {
        console.log('获取到微信登录code:', loginRes.code);

        // 尝试获取用户信息（可选）
        let userProfile = {};
        try {
          userProfile = await this.getUserProfile();
          console.log('获取到用户信息:', userProfile);
        } catch (err) {
          console.log('用户拒绝授权获取用户信息，使用默认信息');
        }

        // 调用统一登录API - 微信登录方式
        const response = await authAPI.unifiedLogin('wechat', {
          code: loginRes.code,
          userInfo: userProfile
        });

        console.log('微信登录响应:', response);

        if (response.tokens && response.tokens.access) {
          console.log('微信登录成功，保存token');

          // 保存token和用户信息
          const access = response.tokens.access;
          const refresh = response.tokens.refresh;
          const userInfo = response.user;

          wx.setStorageSync('access_token', access);
          wx.setStorageSync('refresh_token', refresh);
          wx.setStorageSync('user_info', userInfo);
          wx.setStorageSync('login_type', response.login_type);

          app.globalData.token = access;
          app.globalData.userInfo = userInfo;
          app.globalData.loginType = response.login_type;

          wx.hideLoading();
          wx.showToast({
            title: '登录成功',
            icon: 'success',
            duration: 1500
          });

          // 跳转到首页
          setTimeout(() => {
            wx.switchTab({
              url: '/pages/index/index'
            });
          }, 1500);
        } else {
          console.error('微信登录响应格式错误:', response);
          throw new Error('登录响应格式错误');
        }
      } else {
        throw new Error('获取微信登录code失败');
      }
    } catch (error) {
      console.error('微信登录失败详细信息:', {
        message: error.message,
        statusCode: error.statusCode,
        data: error.data,
        stack: error.stack
      });
      
      wx.hideLoading();
      
      let errorMsg = '微信登录失败';
      if (error.statusCode === 400) {
        errorMsg = '微信授权失败，请重试';
      } else if (error.statusCode === 401) {
        errorMsg = '微信授权无效，请重试';
      } else if (error.statusCode >= 500) {
        errorMsg = '服务器错误，请稍后重试';
      } else if (error.message) {
        errorMsg = error.message;
      }
      
      wx.showToast({
        title: errorMsg,
        icon: 'none',
        duration: 3000
      });
    }
  },

  // 封装wx.login为Promise
  wxLogin: function() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: resolve,
        fail: reject
      });
    });
  },

  // 获取用户信息
  getUserProfile: function() {
    return new Promise((resolve, reject) => {
      wx.getUserProfile({
        desc: '用于完善用户资料',
        success: (res) => {
          resolve(res.userInfo);
        },
        fail: (err) => {
          reject(err);
        }
      });
    });
  }
});
