// pages/practice-history/practice-history.js
const { practiceAPI } = require('../../utils/api');
const app = getApp();

Page({
  data: {
    practiceHistory: [],
    isLoading: true,
    currentPage: 1,
    pageSize: 10,
    hasMore: true
  },

  onLoad: function(options) {
    // 检查登录状态
    if (!app.globalData.token) {
      wx.redirectTo({
        url: '/pages/login/login'
      });
      return;
    }
    
    this.loadPracticeHistory();
  },

  onReachBottom: function() {
    // 加载更多历史记录
    if (this.data.hasMore && !this.data.isLoading) {
      this.loadMoreHistory();
    }
  },

  onPullDownRefresh: function() {
    // 下拉刷新
    this.setData({
      currentPage: 1,
      hasMore: true
    });
    this.loadPracticeHistory().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  // 加载练习历史
  async loadPracticeHistory() {
    try {
      this.setData({ isLoading: true });

      const res = await practiceAPI.getPracticeHistory({
        page: this.data.currentPage,
        page_size: this.data.pageSize
      });

      const history = (res.results || res).map(item => ({
        ...item,
        date: new Date(item.start_time).toLocaleDateString(),
        time: new Date(item.start_time).toLocaleTimeString(),
        mode_text: this.getModeText(item.mode || 'weakness'),
        accuracy_rate: item.accuracy_rate ? item.accuracy_rate.toFixed(1) : 0
      }));

      if (this.data.currentPage === 1) {
        this.setData({
          practiceHistory: history,
          hasMore: history.length >= this.data.pageSize
        });
      } else {
        this.setData({
          practiceHistory: [...this.data.practiceHistory, ...history],
          hasMore: history.length >= this.data.pageSize
        });
      }

    } catch (error) {
      console.error('加载练习历史失败:', error);
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    } finally {
      this.setData({ isLoading: false });
    }
  },

  // 加载更多历史记录
  async loadMoreHistory() {
    this.setData({
      currentPage: this.data.currentPage + 1
    });
    await this.loadPracticeHistory();
  },

  // 获取模式文本
  getModeText(mode) {
    const modeMap = {
      'weakness': '薄弱强化',
      'mixed': '综合练习',
      'mistakes': '错题重练'
    };
    return modeMap[mode] || '未知';
  },

  // 获取状态颜色
  getStatusColor(status) {
    const colorMap = {
      'completed': '#34C759',
      'in_progress': '#FF9500',
      'cancelled': '#FF3B30'
    };
    return colorMap[status] || '#8E8E93';
  },

  // 获取状态文本
  getStatusText(status) {
    const textMap = {
      'completed': '已完成',
      'in_progress': '进行中',
      'cancelled': '已取消'
    };
    return textMap[status] || '未知';
  },

  // 查看练习结果
  onViewResult(e) {
    const { id } = e.currentTarget.dataset;
    wx.navigateTo({
      url: `/pages/practice-result/practice-result?session_id=${id}`
    });
  },

  // 重新练习
  onRepractice() {
    wx.redirectTo({
      url: '/pages/practice/practice'
    });
  },

  // 返回首页
  onGoHome() {
    wx.switchTab({
      url: '/pages/index/index'
    });
  },

  // 分享练习记录
  onShareRecord(e) {
    const { index } = e.currentTarget.dataset;
    const record = this.data.practiceHistory[index];
    
    if (!record) return;

    const shareText = `我在${record.date}完成了一次${record.mode_text}练习，正确率${record.accuracy_rate}%，得分${record.score || 0}分！`;
    
    wx.showShareMenu({
      withShareTicket: true,
      menus: ['shareAppMessage', 'shareTimeline']
    });
  },

  onShareAppMessage(e) {
    const { index } = e.currentTarget.dataset;
    const record = this.data.practiceHistory[index];
    
    if (!record) return {};

    return {
      title: `${record.mode_text}练习记录`,
      path: '/pages/index/index',
      imageUrl: '/images/share-practice.png'
    };
  },

  // 阻止事件冒泡
  stopPropagation() {
    // 空方法，仅用于阻止事件冒泡
  }
});
