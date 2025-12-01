App({
  globalData: {
    userInfo: null,
    token: null,
    apiBaseUrl: 'http://127.0.0.1:8000/api',
    // 生产环境使用线上地址
    // apiBaseUrl: 'https://www.zctestbench.asia/api'
  },

  onLaunch: function() {
    // 检查登录状态
    const token = wx.getStorageSync('token');
    if (token) {
      this.globalData.token = token;
      // 验证token有效性
      this.checkAuth();
    }
  },

  // 检查认证状态
  checkAuth: function() {
    const token = this.globalData.token;
    if (!token) {
      wx.redirectTo({
        url: '/pages/login/login'
      });
      return;
    }

    wx.request({
      url: `${this.globalData.apiBaseUrl}/auth/user-info/`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`
      },
      success: (res) => {
        if (res.statusCode === 200) {
          this.globalData.userInfo = res.data;
        } else {
          // token无效，清除并跳转到登录
          wx.removeStorageSync('token');
          this.globalData.token = null;
          wx.redirectTo({
            url: '/pages/login/login'
          });
        }
      },
      fail: () => {
        wx.showToast({
          title: '网络连接失败',
          icon: 'none'
        });
      }
    });
  },

  // 登录成功回调
  loginSuccess: function(token, userInfo) {
    this.globalData.token = token;
    this.globalData.userInfo = userInfo;
    wx.setStorageSync('token', token);
    wx.setStorageSync('userInfo', userInfo);
  },

  // 退出登录
  logout: function() {
    wx.removeStorageSync('token');
    wx.removeStorageSync('userInfo');
    this.globalData.token = null;
    this.globalData.userInfo = null;
    
    wx.request({
      url: `${this.globalData.apiBaseUrl}/auth/logout/`,
      method: 'POST',
      header: {
        'Authorization': `Bearer ${this.globalData.token}`,
        'Content-Type': 'application/json'
      },
      data: {
        refresh: wx.getStorageSync('refresh_token')
      },
      complete: () => {
        wx.removeStorageSync('refresh_token');
        wx.redirectTo({
          url: '/pages/login/login'
        });
      }
    });
  }
});
