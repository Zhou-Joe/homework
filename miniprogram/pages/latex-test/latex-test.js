// pages/latex-test/latex-test.js
Page({
  data: {
    testCases: [
      {
        name: '简单数学公式',
        content: '计算：2 + 3 = 5',
        latex: '$x^2 + y^2 = z^2$'
      },
      {
        name: '分数测试',
        content: '分数公式：\\frac{1}{2} + \\frac{3}{4} = \\frac{5}{4}',
        latex: '\\frac{a}{b} + \\frac{c}{d} = \\frac{ad + bc}{bd}'
      },
      {
        name: '平方根测试',
        content: '平方根：\\sqrt{4} = 2',
        latex: '\\sqrt{x^2 + y^2}'
      },
      {
        name: '希腊字母测试',
        content: '希腊字母：α, β, γ, δ, π',
        latex: '\\alpha + \\beta = \\gamma'
      },
      {
        name: '求和符号测试',
        content: '求和：\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}',
        latex: '\\sum_{i=1}^{\\infty} \\frac{1}{i^2} = \\frac{\\pi^2}{6}'
      },
      {
        name: '积分测试',
        content: '积分：\\int x dx = \\frac{x^2}{2} + C',
        latex: '\\int_0^1 f(x) dx'
      },
      {
        name: '混合复杂公式',
        content: '复杂公式：\\frac{\\partial^2 u}{\\partial t^2} = c^2 \\nabla^2 u',
        latex: 'E = mc^2, F = ma, \\nabla \\cdot \\mathbf{E} = \\frac{\\rho}{\\epsilon_0}'
      }
    ],
    currentCase: 0,
    fontSize: 16,
    showDebug: true
  },

  onLoad() {
    console.log('LaTeX测试页面加载');
  },

  // 切换测试用例
  switchCase(e) {
    const index = e.currentTarget.dataset.index;
    this.setData({
      currentCase: index
    });
    console.log('切换到测试用例:', this.data.testCases[index]);
  },

  // 调整字体大小
  adjustFontSize(e) {
    this.setData({
      fontSize: e.detail.value
    });
  },

  // 切换调试信息显示
  toggleDebug() {
    this.setData({
      showDebug: !this.data.showDebug
    });
  },

  // 测试原始文本显示
  testRawText(e) {
    const content = e.currentTarget.dataset.content;
    wx.showModal({
      title: '原始文本内容',
      content: content,
      showCancel: false
    });
  },

  // 复制LaTeX内容
  copyLatex(e) {
    const content = e.currentTarget.dataset.content;
    wx.setClipboardData({
      data: content,
      success: () => {
        wx.showToast({
          title: '已复制到剪贴板',
          icon: 'success'
        });
      }
    });
  }
});