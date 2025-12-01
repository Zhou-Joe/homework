// pages/question-detail/question-detail.js
Page({
  data: {
    questionData: null,
    isLoading: true,
    showQuestionImage: false
  },

  onLoad: function(options) {
    try {
      const questionData = JSON.parse(decodeURIComponent(options.data));
      console.log('题目详情页面接收到的数据:', questionData);
      console.log('exercise对象:', questionData.exercise);
      console.log('answer_steps:', questionData.exercise.answer_steps);
      console.log('llmAnalysis:', questionData.llmAnalysis);
      console.log('llmAnalysis.feedback:', questionData.llmAnalysis?.feedback);
      console.log('llmAnalysis.suggestions:', questionData.llmAnalysis?.suggestions);

      this.setData({
        questionData,
        isLoading: false
      });
    } catch (error) {
      console.error('解析题目数据失败:', error);
      wx.showToast({
        title: '数据加载失败',
        icon: 'none'
      });
      wx.navigateBack();
    }
  },

  // 获取难度颜色
  getDifficultyColor(difficulty) {
    const colorMap = {
      'easy': '#34C759',
      'medium': '#FF9500', 
      'hard': '#FF3B30'
    };
    return colorMap[difficulty] || '#FF9500';
  },

  // 获取难度文本
  getDifficultyText(difficulty) {
    const textMap = {
      'easy': '简单',
      'medium': '中等',
      'hard': '困难'
    };
    return textMap[difficulty] || '中等';
  },

  // 格式化响应时间
  formatResponseTime(responseTime) {
    if (!responseTime) return '--';
    const seconds = Math.round(responseTime / 1000);
    return `${seconds}秒`;
  },

  // 获取状态文本
  getStatusText(status) {
    const textMap = {
      'correct': '正确',
      'wrong': '错误',
      'pending': 'AI分析中'
    };
    return textMap[status] || '未知';
  },

  // 获取状态颜色
  getStatusColor(status) {
    const colorMap = {
      'correct': '#34C759',
      'wrong': '#FF3B30',
      'pending': '#FF9500'
    };
    return colorMap[status] || '#8E8E93';
  },

  // 复制文本
  onCopyText(e) {
    const { text } = e.currentTarget.dataset;
    wx.setClipboardData({
      data: text,
      success: () => {
        wx.showToast({
          title: '已复制到剪贴板',
          icon: 'success',
          duration: 1500
        });
      },
      fail: () => {
        wx.showToast({
          title: '复制失败',
          icon: 'none'
        });
      }
    });
  },

  // 切换题目图片显示
  toggleQuestionImage() {
    this.setData({
      showQuestionImage: !this.data.showQuestionImage
    });
  },

  // 查看题目图片
  onViewImage(e) {
    const { url } = e.currentTarget.dataset;
    wx.previewImage({
      urls: [url],
      current: url
    });
  },

  // 分享题目
  onShareQuestion() {
    const { questionData } = this.data;
    const shareText = `第${questionData.questionNumber}题 - ${questionData.knowledgePoints.length > 0 ? questionData.knowledgePoints[0].name : '通用题'}`;
    
    wx.showShareMenu({
      withShareTicket: true,
      menus: ['shareAppMessage', 'shareTimeline']
    });
  },

  // 返回上一页
  onGoBack() {
    wx.navigateBack();
  },

  // 切换AI分析显示
  toggleAnalysis() {
    // 这里可以添加显示/隐藏AI分析的逻辑
    console.log('切换AI分析显示');
  },

  // 复制解题步骤
  onCopySolutionSteps(e) {
    const { text } = e.currentTarget.dataset;
    wx.setClipboardData({
      data: text,
      success: () => {
        wx.showToast({
          title: '解题步骤已复制到剪贴板',
          icon: 'success',
          duration: 1500
        });
      },
      fail: () => {
        wx.showToast({
          title: '复制失败',
          icon: 'none'
        });
      }
    });
  },

  onShareAppMessage() {
    const { questionData } = this.data;
    return {
      title: `题目${questionData.questionNumber} - ${questionData.knowledgePoints.length > 0 ? questionData.knowledgePoints[0].name : '通用题'}`,
      path: '/pages/index/index',
      imageUrl: '/images/share-question.png'
    };
  }
});
