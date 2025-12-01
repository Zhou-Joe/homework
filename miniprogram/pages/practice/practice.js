// pages/practice/practice.js
const { practiceAPI, exerciseAPI, api } = require('../../utils/api');
const app = getApp();

Page({
  data: {
    practiceMode: 'weakness',
    modeIndex: 0,
    practiceModes: [
      { name: '薄弱强化', value: 'weakness', desc: '针对薄弱知识点进行强化训练' },
      { name: '综合练习', value: 'mixed', desc: '混合各知识点进行全面练习' },
      { name: '错题重练', value: 'mistakes', desc: '重新练习之前的错题' }
    ],
    subjects: [],
    subjectIndex: 0,
    questionCount: 5,
    questions: [],
    currentIndex: 0,
    currentQuestion: null,
    answerText: '',
    answerImage: '',
    isPracticing: false,
    isLoading: false,
    showResult: false,
    isCorrect: false,
    result: {},
    practiceHistory: [],
    sessionId: null,
    showQuestionImage: false
  },

  onLoad: function(options) {
    // 检查登录状态
    if (!app.globalData.token) {
      wx.redirectTo({
        url: '/pages/login/login'
      });
      return;
    }
    
    // 加载学科列表
    this.loadSubjects();
    // 加载练习历史
    this.loadPracticeHistory();
  },

  // 加载学科列表
  async loadSubjects() {
    try {
      const res = await exerciseAPI.getSubjects();
      const subjects = [{id: '', name: '全部学科'}, ...(res.results || res)];
      this.setData({ subjects });
    } catch (error) {
      console.error('加载学科失败:', error);
    }
  },

  // 加载练习历史
  async loadPracticeHistory() {
    try {
      const res = await practiceAPI.getPracticeHistory({ limit: 10 });
      const history = (res.results || res).map(item => ({
        ...item,
        date: new Date(item.start_time).toLocaleDateString(),
        mode_text: this.getModeText(item.mode || 'weakness')
      }));
      this.setData({ practiceHistory: history });
    } catch (error) {
      console.error('加载历史失败:', error);
    }
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

  // 练习模式改变
  onModeChange(e) {
    const modeIndex = e.detail.value;
    const practiceMode = this.data.practiceModes[modeIndex].value;
    this.setData({ 
      modeIndex,
      practiceMode 
    });
  },

  // 学科选择改变
  onSubjectChange(e) {
    this.setData({ subjectIndex: e.detail.value });
  },

  // 题目数量改变
  onCountChange(e) {
    this.setData({ questionCount: e.detail.value });
  },

  // 开始练习
  async onStartPractice() {
    const { practiceMode, subjects, subjectIndex, questionCount } = this.data;
    
    this.setData({ isLoading: true });
    
    try {
      // 获取推荐题目
      const params = {
        count: questionCount,
        mode: practiceMode
      };
      
      if (subjects[subjectIndex] && subjects[subjectIndex].id) {
        params.subject_id = subjects[subjectIndex].id;
      }
      
      const res = await practiceAPI.getRecommendedExercises(params);
      
      if (res.recommended_exercises && res.recommended_exercises.length > 0) {
        // 开始练习会话
        const sessionRes = await practiceAPI.startSession({
          subject_id: subjects[subjectIndex] ? subjects[subjectIndex].id : null,
          knowledge_point_ids: [],
          difficulty: null,
          question_count: questionCount
        });
        
        // 添加调试信息，查看实际数据结构
        console.log('API返回的推荐题目数据:', res.recommended_exercises);
        console.log('第一个题目数据结构:', res.recommended_exercises[0]);
        
        const questions = res.recommended_exercises.map(item => {
          const exercise = item.exercise || item;
          console.log('处理后的题目数据:', exercise);
          console.log('题目文本内容:', exercise.question_text);
          
          const difficultyMap = {
            'easy': { text: '简单', color: 'success' },
            'medium': { text: '中等', color: 'warning' },
            'hard': { text: '困难', color: 'danger' }
          };
          const difficultyInfo = difficultyMap[exercise.difficulty] || { text: '未知', color: 'default' };
          
          return {
            ...exercise,
            difficulty_text: difficultyInfo.text,
            difficulty: difficultyInfo.color
          };
        });
        
        // 添加调试信息，检查第一个题目数据
        console.log('设置前的题目数据:', questions[0]);
        console.log('第一个题目的question_text:', questions[0].question_text);
        
        this.setData({
          questions,
          currentIndex: 0,
          currentQuestion: questions[0],
          isPracticing: true,
          isLoading: false,
          sessionId: sessionRes.session_id,
          answerText: '',
          answerImage: '',
          totalQuestions: questions.length
        }, () => {
          // setData回调中检查数据是否正确设置
          console.log('设置后的当前题目:', this.data.currentQuestion);
          console.log('当前题目question_text:', this.data.currentQuestion.question_text);
          console.log('当前题目数据结构完整:', JSON.stringify(this.data.currentQuestion, null, 2));
        });
      } else {
        throw new Error('没有找到合适的题目');
      }
    } catch (error) {
      console.error('开始练习失败:', error);
      wx.showToast({
        title: error.message || '加载题目失败',
        icon: 'none'
      });
      this.setData({ isLoading: false });
    }
  },

  // 输入答案
  onAnswerInput(e) {
    this.setData({ answerText: e.detail.value });
  },

  // 选择答案图片
  onChooseAnswerImage() {
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const tempFilePath = res.tempFilePaths[0];
        this.setData({ answerImage: tempFilePath });
        console.log('答案图片选择成功:', tempFilePath);
        console.log('设置后的answerImage状态:', this.data.answerImage);
        
        // 确保状态更新完成后再检查
        wx.nextTick(() => {
          console.log('nextTick后的answerImage状态:', this.data.answerImage);
        });
      },
      fail: (err) => {
        console.error('选择答案图片失败:', err);
        wx.showToast({
          title: '选择图片失败',
          icon: 'none'
        });
      }
    });
  },

  // 提交答案
  async onSubmitAnswer() {
    const { sessionId, currentQuestion, currentIndex, questions, answerText, answerImage } = this.data;

    // 添加调试信息
    console.log('提交答案时的状态检查:');
    console.log('answerText:', answerText);
    console.log('answerImage:', answerImage);
    console.log('answerImage类型:', typeof answerImage);
    console.log('answerImage长度:', answerImage ? answerImage.length : 'null');

    // 改进验证逻辑，确保字符串trim后的检查
    const hasText = answerText && answerText.trim().length > 0;
    const hasImage = answerImage && answerImage.trim().length > 0;

    console.log('hasText:', hasText);
    console.log('hasImage:', hasImage);

    if (!hasText && !hasImage) {
      wx.showToast({
        title: '请上传图片或者文本',
        icon: 'none'
      });
      return;
    }

    wx.showLoading({ title: 'AI分析中...' });

    try {
      // 调用异步AI分析API
      let answerData = {};

      if (hasText) {
        answerData.answer_text = answerText.trim();
      }

      if (hasImage) {
        // 如果是图片答案，直接通过uploadFile提交
        console.log('开始提交答案图片:', answerImage);
        
        wx.hideLoading();
        wx.showLoading({ title: '提交中...' });
        
        try {
          const result = await api.uploadAnswer('/practice/submit-answer-async/', answerImage, {
            session_id: sessionId,
            exercise_id: currentQuestion.id,
            answer_text: answerText ? answerText.trim() : ''
          });
          
          console.log('图片答案提交成功:', result);
          
          // 直接跳转到下一题，不显示解析结果
          wx.hideLoading();
          
          // 显示提交成功提示
          wx.showToast({
            title: '答案已提交',
            icon: 'success',
            duration: 1000
          });

          // 延迟跳转到下一题
          setTimeout(() => {
            this.nextQuestion();
          }, 1000);
          
          return; // 直接返回，不执行后续逻辑
          
        } catch (uploadError) {
          console.error('图片答案提交失败:', uploadError);
          wx.hideLoading();
          wx.showToast({
            title: uploadError.message || '提交失败，请重试',
            icon: 'none',
            duration: 3000
          });
          return;
        }
      }

      console.log('准备调用API:', {
        sessionId,
        currentQuestion: currentQuestion.id,
        answerData,
        apiMethod: 'submitAnswerAsync'
      });

      const result = await practiceAPI.submitAnswerAsync(sessionId, currentQuestion.id, answerData);

      console.log('API响应结果:', result);

      // 直接跳转到下一题，不显示解析结果
      wx.hideLoading();
      
      // 显示提交成功提示
      wx.showToast({
        title: '答案已提交',
        icon: 'success',
        duration: 1000
      });

      // 延迟跳转到下一题
      setTimeout(() => {
        this.nextQuestion();
      }, 1000);
    } catch (error) {
      console.error('提交答案失败:', error);
      wx.showToast({
        title: error.message || 'AI分析失败，请重试',
        icon: 'none',
        duration: 3000
      });
    } finally {
      wx.hideLoading();
    }
  },

  // 跳过题目
  onSkipQuestion() {
    this.nextQuestion();
  },

  // 下一题
  onNextQuestion() {
    this.nextQuestion();
  },

  // 切换题目图片显示
  toggleQuestionImage() {
    this.setData({
      showQuestionImage: !this.data.showQuestionImage
    });
  },

  // 下一题逻辑
  nextQuestion() {
    const { currentIndex, questions } = this.data;
    
    if (currentIndex < questions.length - 1) {
      const nextIndex = currentIndex + 1;
      this.setData({
        currentIndex: nextIndex,
        currentQuestion: questions[nextIndex],
        showResult: false,
        answerText: '',
        answerImage: '',
        showQuestionImage: false // 重置图片显示状态
      });
    } else {
      // 最后一题，自动完成练习
      this.onFinishPractice();
    }
  },

  // 完成练习
  async onFinishPractice() {
    const { sessionId } = this.data;
    
    try {
      if (sessionId) {
        await practiceAPI.completeSession(sessionId);
      }
      
      // 保存session_id到本地存储
      wx.setStorageSync('last_practice_session', sessionId);
      
      wx.showToast({
        title: '练习完成！',
        icon: 'success',
        duration: 1500
      });
      
      // 延迟跳转到结果页面
      setTimeout(() => {
        wx.redirectTo({
          url: `/pages/practice-result/practice-result?session_id=${sessionId}`
        });
      }, 1500);
      
    } catch (error) {
      console.error('完成练习失败:', error);
      wx.showToast({
        title: '完成练习失败',
        icon: 'none'
      });
    }
  }
});

// 版本: v2.1 - 修复图片上传验证问题
// 更新时间: 2025-11-30