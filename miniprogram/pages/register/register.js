// pages/register/register.js
const authAPI = require('../../utils/api').authAPI;
const app = getApp();

Page({
  data: {
    username: '',
    nickname: '',
    password: '',
    passwordConfirm: '',
    birthDate: '',
    gradeIndex: 0,
    gradeLevels: [
      '小学1年级', '小学2年级', '小学3年级',
      '小学4年级', '小学5年级', '小学6年级',
      '初一', '初二', '初三',
      '高一', '高二', '高三'
    ],
    isLoading: false
  },

  onLoad: function(options) {
    // 检查是否已登录
    if (app.globalData.token) {
      wx.switchTab({
        url: '/pages/index/index'
      });
    }
  },

  // 用户名输入
  onUsernameInput: function(e) {
    this.setData({
      username: e.detail.value
    });
  },

  // 昵称输入
  onNicknameInput: function(e) {
    this.setData({
      nickname: e.detail.value
    });
  },

  // 密码输入
  onPasswordInput: function(e) {
    this.setData({
      password: e.detail.value
    });
  },

  // 确认密码输入
  onPasswordConfirmInput: function(e) {
    this.setData({
      passwordConfirm: e.detail.value
    });
  },

  // 出生日期选择
  onBirthDateChange: function(e) {
    this.setData({
      birthDate: e.detail.value
    });
  },

  // 年级选择
  onGradeChange: function(e) {
    this.setData({
      gradeIndex: parseInt(e.detail.value)
    });
  },

  // 注册
  onRegister: async function() {
    const {
      username,
      nickname,
      password,
      passwordConfirm,
      birthDate,
      gradeIndex,
      gradeLevels
    } = this.data;

    // 表单验证
    if (!username) {
      wx.showToast({
        title: '请输入用户名',
        icon: 'none'
      });
      return;
    }

    if (!nickname) {
      wx.showToast({
        title: '请输入昵称',
        icon: 'none'
      });
      return;
    }

    if (!password) {
      wx.showToast({
        title: '请输入密码',
        icon: 'none'
      });
      return;
    }

    if (password.length < 6) {
      wx.showToast({
        title: '密码至少6位',
        icon: 'none'
      });
      return;
    }

    if (password !== passwordConfirm) {
      wx.showToast({
        title: '两次密码不一致',
        icon: 'none'
      });
      return;
    }

    if (!birthDate) {
      wx.showToast({
        title: '请选择出生日期',
        icon: 'none'
      });
      return;
    }

    this.setData({ isLoading: true });

    try {
      console.log('开始注册:', {
        username,
        nickname,
        password: '***',
        birthDate,
        gradeLevel: gradeLevels[gradeIndex]
      });

      // 调用注册API
      const response = await authAPI.register({
        username: username,
        password: password,
        password_confirm: passwordConfirm,
        nickname: nickname,
        birth_date: birthDate,
        grade_level: gradeIndex + 1 // 传递数字给后端
      });

      console.log('注册响应:', response);

      if (response.tokens) {
        // 自动登录
        wx.setStorageSync('token', response.tokens.access);
        wx.setStorageSync('refresh_token', response.tokens.refresh);
        app.globalData.token = response.tokens.access;
        app.globalData.userInfo = response.user;
        wx.setStorageSync('userInfo', response.user);

        wx.showToast({
          title: '注册成功',
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
        throw new Error('注册响应格式错误');
      }
    } catch (error) {
      console.error('注册失败:', error);
      wx.showToast({
        title: error.message || '注册失败，请重试',
        icon: 'none',
        duration: 3000
      });
    } finally {
      this.setData({ isLoading: false });
    }
  }
});