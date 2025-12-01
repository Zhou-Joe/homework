// pages/profile/profile.js
const { authAPI, practiceAPI, statsAPI, exerciseAPI } = require('../../utils/api');
const app = getApp();

Page({
  data: {
    userInfo: null,
    isLoading: false,
    stats: {
      totalQuestions: 0,
      correctAnswers: 0,
      accuracyRate: 0,
      totalScore: 0,
      practiceCount: 0,
      avgResponseTime: 0
    },
    recentSessions: [],
    weakKnowledgePoints: [],
    recentMistakes: []
  },

  onLoad: function(options) {
    // 检查登录状态
    if (!app.globalData.token) {
      wx.redirectTo({
        url: '/pages/login/login'
      });
      return;
    }
    
    this.loadUserInfo();
    this.loadStats();
    this.loadRecentSessions();
  },

  onShow: function() {
    // 每次显示页面时刷新数据
    if (app.globalData.token) {
      this.loadStats();
      this.loadRecentSessions();
    }
  },

  // 加载用户信息
  async loadUserInfo() {
    try {
      const userInfo = app.globalData.userInfo || await authAPI.getUserInfo();
      this.setData({ userInfo });
      app.globalData.userInfo = userInfo;
    } catch (error) {
      console.error('加载用户信息失败:', error);
    }
  },

  // 加载统计数据
  async loadStats() {
    try {
      const statsRes = await statsAPI.getDashboardStats();
      const practiceStatsRes = await practiceAPI.getPracticeStats();
      
      this.setData({
        stats: {
          totalQuestions: statsRes.total_exercises || 0,
          correctAnswers: statsRes.correct_answers || 0,
          accuracyRate: statsRes.accuracy_rate || 0,
          totalScore: practiceStatsRes.total_score || 0,
          practiceCount: statsRes.total_practice_sessions || 0,
          avgResponseTime: statsRes.avg_response_time || 0
        }
      });
    } catch (error) {
      console.error('加载统计数据失败:', error);
    }
  },

  // 加载最近练习记录
  async loadRecentSessions() {
    try {
      const res = await practiceAPI.getPracticeHistory({ limit: 5 });
      const sessions = (res.results || res).map(item => ({
        ...item,
        date: new Date(item.start_time).toLocaleDateString(),
        time: new Date(item.start_time).toLocaleTimeString(),
        accuracy: item.total_questions > 0 ? 
          ((item.correct_answers / item.total_questions) * 100).toFixed(1) : 0
      }));
      
      this.setData({ recentSessions: sessions });
    } catch (error) {
      console.error('加载练习记录失败:', error);
    }
  },

  // 查看练习历史
  onViewPracticeHistory() {
    wx.navigateTo({
      url: '/pages/practice-history/practice-history'
    });
  },

  // 查看错题本
  onViewMistakes() {
    wx.navigateTo({
      url: '/pages/mistakes/mistakes'
    });
  },

  // 查看知识点掌握情况
  onViewKnowledgePoints() {
    wx.navigateTo({
      url: '/pages/knowledge-points/knowledge-points'
    });
  },

  // 查看最近练习详情
  onViewSessionDetail(e) {
    const { sessionId } = e.currentTarget.dataset;
    if (sessionId) {
      wx.navigateTo({
        url: `/pages/practice-result/practice-result?session_id=${sessionId}`
      });
    }
  },

  // 开始练习
  onStartPractice() {
    wx.switchTab({
      url: '/pages/practice/practice'
    });
  },

  // 上传题目
  onUploadExercise() {
    wx.switchTab({
      url: '/pages/upload/upload'
    });
  },

  // 编辑资料
  onEditProfile() {
    wx.navigateTo({
      url: '/pages/edit-profile/edit-profile'
    });
  },

  // 设置
  onSettings() {
    wx.navigateTo({
      url: '/pages/settings/settings'
    });
  },

  // 退出登录
  onLogout() {
    wx.showModal({
      title: '确认退出',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          app.logout();
        }
      }
    });
  },

  // 分享小程序
  onShareApp() {
    wx.showShareMenu({
      withShareTicket: true,
      menus: ['shareAppMessage', 'shareTimeline']
    });
  },

  onShareAppMessage() {
    return {
      title: '智能学习平台 - AI驱动的个性化学习',
      path: '/pages/index/index',
      imageUrl: '/images/share-app.png'
    };
  },

  onPullDownRefresh() {
    Promise.all([
      this.loadUserInfo(),
      this.loadStats(),
      this.loadRecentSessions()
    ]).finally(() => {
      wx.stopPullDownRefresh();
    });
  }
});
