// pages/index/index.js
const { statsAPI, exerciseAPI } = require('../../utils/api');
const app = getApp();

Page({
  data: {
    userInfo: {},
    stats: {
      total_exercises: 0,
      mistake_count: 0,
      practice_count: 0,
      accuracy_rate: 0
    },
    subjectStats: [],
    weakKnowledgePoints: [],
    recentMistakes: [],
    isLoading: true
  },

  onLoad: function(options) {
    // 获取用户信息
    const userInfo = app.globalData.userInfo || wx.getStorageSync('userInfo');
    if (userInfo) {
      this.setData({ userInfo });
    }
  },

  onShow: function() {
    // 加载数据
    this.loadDashboardData();
  },

  // 加载仪表板数据
  async loadDashboardData() {
    this.setData({ isLoading: true });
    
    try {
      // 并行加载所有数据
      const [statsRes, subjectsRes, knowledgeRes, mistakesRes] = await Promise.all([
        statsAPI.getDashboardStats(),
        statsAPI.getSubjectStats(),
        statsAPI.getWeakKnowledgePoints(),
        statsAPI.getRecentMistakes()
      ]);

      console.log('学科统计数据:', subjectsRes);
      console.log('薄弱知识点数据:', knowledgeRes);
      console.log('统计数据:', statsRes);
      console.log('错题数据:', mistakesRes);

      // 处理学科统计数据
      const processedSubjects = Array.isArray(subjectsRes) ? subjectsRes : (subjectsRes.results || []);
      
      // 处理薄弱知识点数据
      const processedKnowledge = Array.isArray(knowledgeRes) ? knowledgeRes : (knowledgeRes.results || []);

      // 处理错题数据字段映射
      const processedMistakes = Array.isArray(mistakesRes) ? mistakesRes.map(mistake => {
        // 格式化时间，只显示日期部分
        const uploadTime = mistake.upload_time || mistake.created_at || '';
        const formattedDate = uploadTime.split('T')[0]; // 只取日期部分
        
        return {
          id: mistake.id,
          title: mistake.exercise_title || mistake.title || '错题',  // 将exercise_title映射为title
          subject_name: mistake.exercise_subject || mistake.subject_name || '未知学科',  // 将exercise_subject映射为subject_name
          created_at: formattedDate,  // 将upload_time映射为created_at并格式化
          // 由于API没有返回难度信息，使用默认值
          difficulty: mistake.difficulty || 'medium',
          difficulty_text: this.getDifficultyText(mistake.difficulty || 'medium'),
          // 保留原始数据以便后续使用
          original_data: mistake
        };
      }) : [];

      this.setData({
        stats: statsRes,
        subjectStats: processedSubjects,
        weakKnowledgePoints: processedKnowledge,
        recentMistakes: processedMistakes,
        isLoading: false
      });
    } catch (error) {
      console.error('加载数据失败:', error);
      wx.showToast({
        title: '加载数据失败',
        icon: 'none'
      });
      this.setData({ isLoading: false });
    }
  },

  // 获取难度文本
  getDifficultyText(difficulty) {
    const difficultyMap = {
      'easy': '简单',
      'medium': '中等',
      'hard': '困难'
    };
    return difficultyMap[difficulty] || '中等';
  },

  // 点击查看错题详情
  onExerciseTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/question-detail/question-detail?id=${id}`
    });
  },

  // 查看所有错题
  onViewAllMistakes() {
    wx.navigateTo({
      url: '/pages/upload/upload'
    });
  },

  // 上传新题
  onUploadNewQuestion() {
    wx.switchTab({
      url: '/pages/upload/upload'
    });
  },

  // 下拉刷新
  onPullDownRefresh() {
    this.loadDashboardData().then(() => {
      wx.stopPullDownRefresh();
    });
  }
});
