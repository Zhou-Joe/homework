// pages/upload/upload.js
const { exerciseAPI } = require('../../utils/api');
const app = getApp();

Page({
  data: {
    imagePath: '',
    imageName: '',
    imageSize: '',
    analysisResult: null,
    isUploading: false
  },

  onLoad: function(options) {
    // 检查登录状态
    if (!app.globalData.token) {
      wx.redirectTo({
        url: '/pages/login/login'
      });
    }
  },

  // 选择图片
  onChooseImage: function() {
    // 优先使用 chooseImage，更稳定
    wx.chooseImage({
      count: 1,
      sizeType: ['original', 'compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const tempFile = res.tempFiles[0];

        // 检查文件大小 (10MB)
        if (tempFile.size > 10 * 1024 * 1024) {
          wx.showToast({
            title: '图片大小不能超过10MB',
            icon: 'none'
          });
          return;
        }

        // 检查文件类型
        const allowedTypes = ['jpg', 'jpeg', 'png', 'gif'];
        const fileType = tempFile.path.split('.').pop().toLowerCase();
        if (!allowedTypes.includes(fileType)) {
          wx.showToast({
            title: '请选择图片文件',
            icon: 'none'
          });
          return;
        }

        this.setData({
          imagePath: tempFile.path,
          imageName: tempFile.path.split('/').pop() || '图片',
          imageSize: this.formatFileSize(tempFile.size)
        });

        console.log('图片选择成功:', {
          path: tempFile.path,
          size: tempFile.size
        });
      },
      fail: (err) => {
        console.error('选择图片失败:', err);
        wx.showToast({
          title: '选择图片失败',
          icon: 'none'
        });
      }
    });
  },

  // 上传并分析图片
  onUpload: async function() {
    const { imagePath } = this.data;

    if (!imagePath) {
      wx.showToast({
        title: '请先选择图片',
        icon: 'none'
      });
      return;
    }

    this.setData({ isUploading: true });

    try {
      // 调用上传API
      const result = await exerciseAPI.uploadExercise(imagePath);
      
      if (result.analysis) {
        const analysis = result.analysis;
        
        // 处理难度文本
        const difficultyMap = {
          'easy': { text: '简单', color: 'success' },
          'medium': { text: '中等', color: 'warning' },
          'hard': { text: '困难', color: 'danger' }
        };
        
        const difficultyInfo = difficultyMap[analysis.difficulty] || { text: '未知', color: 'default' };
        
        this.setData({
          analysisResult: {
            ...analysis,
            difficulty_text: difficultyInfo.text,
            difficulty: difficultyInfo.color
          }
        });

        wx.showToast({
          title: 'AI分析完成',
          icon: 'success',
          duration: 2000
        });
      } else {
        throw new Error('分析结果为空');
      }
    } catch (error) {
      console.error('上传失败:', error);
      wx.showToast({
        title: error.message || 'AI分析失败，请重试',
        icon: 'none',
        duration: 3000
      });
    } finally {
      this.setData({ isUploading: false });
    }
  },

  // 保存习题到错题本
  onSaveExercise: async function() {
    const { analysisResult } = this.data;

    if (!analysisResult || !analysisResult.exercise_id) {
      wx.showToast({
        title: '没有可保存的习题',
        icon: 'none'
      });
      return;
    }

    try {
      wx.showLoading({ title: '保存中...' });
      
      // 保存习题
      await exerciseAPI.saveExercise(analysisResult.exercise_id);
      
      wx.hideLoading();
      wx.showToast({
        title: '保存成功',
        icon: 'success',
        duration: 2000
      });

      // 2秒后返回首页
      setTimeout(() => {
        wx.switchTab({
          url: '/pages/index/index'
        });
      }, 2000);
    } catch (error) {
      wx.hideLoading();
      console.error('保存失败:', error);
      wx.showToast({
        title: error.message || '保存失败',
        icon: 'none'
      });
    }
  },

  // 重置上传
  onReset: function() {
    this.setData({
      imagePath: '',
      imageName: '',
      imageSize: '',
      analysisResult: null
    });
  },

  // 格式化文件大小
  formatFileSize: function(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
});
