// pages/practice-result/practice-result.js
const { practiceAPI, exerciseAPI } = require('../../utils/api');
const app = getApp();

Page({
  data: {
    sessionId: null,
    practiceSession: null,
    practiceRecords: [],
    knowledgePointScores: {},
    totalScore: 0,
    correctCount: 0,
    totalCount: 0,
    accuracyRate: 0,
    totalTime: 0,
    maxStreak: 0,
    knowledgeCount: 0,
    avgDifficulty: '中等',
    isLoading: true,
    analysisStatus: {
      isAnalyzing: false,
      pendingCount: 0,
      completedCount: 0
    },
    refreshTimer: null
  },

  onLoad: function(options) {
    // 检查登录状态
    if (!app.globalData.token) {
      wx.redirectTo({
        url: '/pages/login/login'
      });
      return;
    }

    const sessionId = options.session_id || wx.getStorageSync('last_practice_session');
    if (!sessionId) {
      wx.showModal({
        title: '提示',
        content: '未找到练习会话信息，请先完成一次练习',
        showCancel: false,
        success: () => {
          wx.navigateBack();
        }
      });
      return;
    }

    this.setData({ sessionId });
    this.loadPracticeResult();
    this.startAutoRefresh();
  },

  onUnload: function() {
    // 清除定时器
    if (this.data.refreshTimer) {
      clearInterval(this.data.refreshTimer);
    }
  },

  // 加载练习结果
  async loadPracticeResult() {
    try {
      this.setData({ isLoading: true });

      // 加载会话数据
      const sessionRes = await practiceAPI.getPracticeResult(this.data.sessionId);
      const recordsRes = await practiceAPI.getPracticeRecords(this.data.sessionId);

      const practiceSession = sessionRes;
      const practiceRecords = recordsRes.results || recordsRes;

      // 计算统计数据
      const stats = this.calculateStats(practiceSession, practiceRecords);

      // 检查是否有pending状态的题目
      const pendingRecords = practiceRecords.filter(record => record.status === 'pending');
      const isAnalyzing = pendingRecords.length > 0;

      this.setData({
        practiceSession,
        practiceRecords,
        ...stats,
        analysisStatus: {
          isAnalyzing,
          pendingCount: pendingRecords.length,
          completedCount: practiceRecords.length - pendingRecords
        },
        isLoading: false
      });

      // 如果有正在分析的题目，显示提示
      if (isAnalyzing) {
        wx.showToast({
          title: `${pendingRecords.length}道题AI分析中`,
          icon: 'none',
          duration: 2000
        });
      }

    } catch (error) {
      console.error('加载练习结果失败:', error);
      wx.showModal({
        title: '加载失败',
        content: error.message || '无法加载练习结果，请重试',
        confirmText: '重试',
        success: (res) => {
          if (res.confirm) {
            this.loadPracticeResult();
          } else {
            wx.navigateBack();
          }
        }
      });
    }
  },

  // 计算统计数据
  calculateStats(practiceSession, practiceRecords) {
    const totalScore = practiceSession.score || 0;
    const correctCount = practiceSession.correct_answers || 0;
    const totalCount = practiceSession.total_questions || 0;
    const accuracyRate = totalCount > 0 ? (correctCount / totalCount * 100).toFixed(1) : 0;

    // 总用时（分钟）
    const totalTime = practiceRecords.reduce((sum, record) =>
      sum + (record.response_time || 0), 0) / 60000;

    // 连续正确
    let maxStreak = 0;
    let currentStreak = 0;
    practiceRecords.forEach(record => {
      if (record.status === 'correct') {
        currentStreak++;
        maxStreak = Math.max(maxStreak, currentStreak);
      } else {
        currentStreak = 0;
      }
    });

    // 知识点覆盖
    const knowledgePoints = new Set();
    practiceRecords.forEach(record => {
      if (record.exercise && record.exercise.knowledge_points) {
        record.exercise.knowledge_points.forEach(kp => knowledgePoints.add(kp.name));
      }
    });

    // 平均难度
    const difficulties = { easy: 1, medium: 2, hard: 3 };
    const avgDiff = practiceRecords.reduce((sum, record) =>
      sum + (difficulties[record.exercise?.difficulty] || 2), 0) / practiceRecords.length;
    const avgDifficulty = avgDiff <= 1.5 ? '简单' : avgDiff <= 2.5 ? '中等' : '困难';

    return {
      totalScore,
      correctCount,
      totalCount,
      accuracyRate,
      totalTime: totalTime.toFixed(1),
      maxStreak,
      knowledgeCount: knowledgePoints.size,
      avgDifficulty
    };
  },

  // 开始自动刷新
  startAutoRefresh() {
    const refreshTimer = setInterval(async () => {
      try {
        await this.checkAnalysisStatus();
      } catch (error) {
        console.error('检查AI分析状态失败:', error);
      }
    }, 3000);

    this.setData({ refreshTimer });
  },

  // 检查AI分析状态
  async checkAnalysisStatus() {
    try {
      const statusRes = await practiceAPI.getAnalysisStatus(this.data.sessionId);
      
      if (statusRes.analysis_complete) {
        // AI分析完成，停止自动刷新并重新加载数据
        if (this.data.refreshTimer) {
          clearInterval(this.data.refreshTimer);
          this.setData({ refreshTimer: null });
        }
        
        await this.loadPracticeResult();
        wx.showToast({
          title: 'AI分析已完成！',
          icon: 'success',
          duration: 2000
        });
      } else {
        // 更新分析状态
        const pendingCount = statusRes.pending_count || 0;
        const completedCount = this.data.practiceRecords.length - pendingCount;
        
        this.setData({
          analysisStatus: {
            isAnalyzing: pendingCount > 0,
            pendingCount,
            completedCount
          }
        });

        // 如果状态有变化，重新加载记录
        if (pendingCount < this.data.analysisStatus.pendingCount) {
          await this.loadPracticeResult();
        }
      }
    } catch (error) {
      console.error('获取分析状态失败:', error);
    }
  },

  // 获取状态颜色
  getStatusColor(status) {
    const colorMap = {
      'pending': '#FF9500',
      'correct': '#34C759',
      'wrong': '#FF3B30'
    };
    return colorMap[status] || '#8E8E93';
  },

  // 获取状态文本
  getStatusText(status) {
    const textMap = {
      'pending': 'AI老师在分析',
      'correct': '正确',
      'wrong': '错误'
    };
    return textMap[status] || '未知';
  },

  // 查看题目详情
  onViewQuestionDetail(e) {
    const { index } = e.currentTarget.dataset;
    const record = this.data.practiceRecords[index];
    
    if (!record) return;

    // 如果题目还在分析中，显示提示
    if (record.status === 'pending') {
      wx.showToast({
        title: 'AI分析中，请稍后查看',
        icon: 'none',
        duration: 2000
      });
      return;
    }

    // 显示题目详情弹窗（简化版，避免创建新页面）
    this.showQuestionModal(record);
  },

  // 显示题目详情弹窗
  showQuestionModal(record) {
    const exercise = record.exercise || {};
    const knowledgePoints = exercise.knowledge_points || [];
    
    console.log('原始题目数据:', exercise);
    console.log('answer_steps字段:', record.exercise_answer_steps);
    
    // 跳转到专门的题目详情页面，支持LaTeX和分段显示
    const questionData = {
      questionNumber: this.data.practiceRecords.indexOf(record) + 1,
      exercise: {
        ...exercise,
        answer_steps: record.exercise_answer_steps || '暂无解题步骤'
      },
      knowledgePoints: knowledgePoints,
      studentAnswer: record.student_answer_text,
      correctAnswer: record.exercise_correct_answer,
      llmAnalysis: record.llm_analysis,
      status: record.status,
      responseTime: record.response_time
    };
    
    console.log('传递给详情页面的数据:', questionData);
    
    wx.navigateTo({
      url: `/pages/question-detail/question-detail?data=${encodeURIComponent(JSON.stringify(questionData))}`
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

  // 查看练习历史
  onViewHistory() {
    wx.navigateTo({
      url: '/pages/practice-history/practice-history'
    });
  },

  // 分享成绩
  onShareScore() {
    const { totalScore, correctCount, totalCount, accuracyRate } = this.data;
    
    const shareText = `我在智能学习平台完成了${totalCount}道题的练习，正确率${accuracyRate}%，综合得分${totalScore}分！`;
    
    wx.showShareMenu({
      withShareTicket: true,
      menus: ['shareAppMessage', 'shareTimeline']
    });
  },

  onShareAppMessage() {
    const { totalScore, accuracyRate } = this.data;
    return {
      title: '智能学习平台练习成绩',
      path: '/pages/index/index',
      imageUrl: '/images/share-score.png'
    };
  }
});
