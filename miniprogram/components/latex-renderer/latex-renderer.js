// components/latex-renderer/latex-renderer.js
// Unicode转换函数
const superscriptToUnicode = (sup) => {
  const superscripts = {
    '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
    '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
    '+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾',
    'n': 'ⁿ', 'i': 'ⁱ'
  };
  
  let result = '';
  for (let char of sup) {
    result += superscripts[char] || char;
  }
  return result;
};

const subscriptToUnicode = (sub) => {
  const subscripts = {
    '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
    '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
    '+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎',
    'a': 'ₐ', 'e': 'ₑ', 'i': 'ᵢ', 'j': 'ⱼ', 'k': 'ₖ',
    'l': 'ₗ', 'm': 'ₘ', 'n': 'ₙ', 'o': 'ₒ',
    'p': 'ₚ', 'r': 'ᵣ', 's': 'ₛ', 't': 'ₜ',
    'u': 'ᵤ', 'v': 'ᵥ', 'x': 'ₓ'
  };
  
  let result = '';
  for (let char of sub) {
    result += subscripts[char] || char;
  }
  return result;
};

Component({
  properties: {
    content: {
      type: String,
      value: ''
    },
    fontSize: {
      type: Number,
      value: 16
    }
  },

  data: {
    renderedContent: [],
    isLoading: false
  },

  lifetimes: {
    attached() {
      // 组件初始化时渲染内容
      if (this.properties.content) {
        this.renderLaTeX(this.properties.content, this.properties.fontSize);
      }
    }
  },

  observers: {
    'content, fontSize': function(content, fontSize) {
      console.log('LaTeX组件接收到内容:', content);
      console.log('LaTeX组件字体大小:', fontSize);
      if (content !== undefined && content !== null) {
        this.renderLaTeX(content, fontSize);
      }
    }
  },

  methods: {
    // 渲染LaTeX内容 - 增强版本，支持图片和Unicode双重渲染
    renderLaTeX(content, fontSize = 16) {
      console.log('开始渲染LaTeX内容:', content);
      console.log('字体大小:', fontSize);
      this.setData({ isLoading: true });

      try {
        // 如果内容为空，直接返回
        if (!content || content.trim() === '') {
          console.log('内容为空，不渲染');
          this.setData({
            renderedContent: [],
            isLoading: false
          });
          return;
        }

        // 检查是否包含复杂的LaTeX语法
        const hasComplexLaTeX = /\\(frac|sqrt|sum|int|lim|alpha|beta|gamma|delta|epsilon|theta|lambda|mu|pi|sigma|phi|omega)/.test(content);

        let renderedContent = [];

        if (hasComplexLaTeX) {
          // 复杂LaTeX使用图片渲染
          const segments = this.parseLaTeXSegments(content, fontSize);
          renderedContent = segments.map((segment, index) => ({
            type: segment.isLaTeX ? 'image' : 'text',
            content: segment.isLaTeX ? this.renderLaTeXToImage(segment.content) : segment.content,
            key: `segment_${index}`
          }));
        } else {
          // 简单LaTeX使用Unicode替换
          const processedContent = this.replaceCommonMathSymbols(content);
          renderedContent = [{
            type: 'text',
            content: processedContent
          }];
        }

        console.log('处理后的渲染内容:', renderedContent);

        this.setData({
          renderedContent: renderedContent,
          isLoading: false
        });
        console.log('LaTeX渲染完成');
      } catch (error) {
        console.error('LaTeX渲染失败:', error);
        // 出错时降级为纯文本显示
        this.setData({
          renderedContent: [{ type: 'fallback-text', content: content }],
          isLoading: false
        });
      }
    },

    // 解析LaTeX段落
    parseLaTeXSegments(text, fontSize) {
      const segments = [];
      const regex = /\\(frac|sqrt|sum|int|lim|alpha|beta|gamma|delta|epsilon|theta|lambda|mu|pi|sigma|phi|omega)[^\\]*|\\[a-zA-Z]+|\$[^$]+\$|\\\([^)]+\\\)/g;
      let lastIndex = 0;
      let match;

      while ((match = regex.exec(text)) !== null) {
        // 添加LaTeX前的文本
        if (match.index > lastIndex) {
          const plainText = text.substring(lastIndex, match.index);
          if (plainText.trim()) {
            segments.push({
              content: plainText,
              isLaTeX: false
            });
          }
        }

        // 添加LaTeX段落
        segments.push({
          content: match[0].replace(/^\$|^\(|\$|\)$/g, ''), // 清理包围符号
          isLaTeX: true
        });

        lastIndex = match.index + match[0].length;
      }

      // 添加剩余文本
      if (lastIndex < text.length) {
        const remainingText = text.substring(lastIndex);
        if (remainingText.trim()) {
          segments.push({
            content: remainingText,
            isLaTeX: false
          });
        }
      }

      // 如果没有匹配到LaTeX，整个内容都是普通文本
      if (segments.length === 0) {
        segments.push({
          content: text,
          isLaTeX: false
        });
      }

      return segments;
    },

    // 替换常见数学符号为Unicode
    replaceCommonMathSymbols(content) {
      // 如果没有LaTeX语法符号，直接返回原文
      if (!content.includes('\\') && !content.includes('^') && !content.includes('_')) {
        return content;
      }
      
      return content
        // 分数
        .replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, '($1/$2)')
        // 上标
        .replace(/\^(\{[^}]+\}|\w)/g, (match, sup) => {
          const superscript = sup.replace(/[{}]/g, '');
          return superscriptToUnicode(superscript);
        })
        // 下标
        .replace(/_(\{[^}]+\}|\w)/g, (match, sub) => {
          const subscript = sub.replace(/[{}]/g, '');
          return subscriptToUnicode(subscript);
        })
        // 平方根
        .replace(/\\sqrt\{([^}]+)\}/g, '√($1)')
        // 希腊字母
        .replace(/\\alpha/g, 'α')
        .replace(/\\beta/g, 'β')
        .replace(/\\gamma/g, 'γ')
        .replace(/\\delta/g, 'δ')
        .replace(/\\epsilon/g, 'ε')
        .replace(/\\theta/g, 'θ')
        .replace(/\\lambda/g, 'λ')
        .replace(/\\mu/g, 'μ')
        .replace(/\\pi/g, 'π')
        .replace(/\\sigma/g, 'σ')
        .replace(/\\phi/g, 'φ')
        .replace(/\\omega/g, 'ω')
        // 求和
        .replace(/\\sum/g, '∑')
        // 积分
        .replace(/\\int/g, '∫')
        // 极限
        .replace(/\\lim/g, 'lim')
        // 无穷
        .replace(/\\infty/g, '∞')
        // 大于等于
        .replace(/\\geq/g, '≥')
        // 小于等于
        .replace(/\\leq/g, '≤')
        // 不等于
        .replace(/\\neq/g, '≠')
        // 约等于
        .replace(/\\approx/g, '≈')
        // 乘以
        .replace(/\\times/g, '×')
        // 除以
        .replace(/\\div/g, '÷')
        // 正负
        .replace(/\\pm/g, '±')
        // 度
        .replace(/\\deg/g, '°');
    },

    // 处理公式内容
    processFormula(formula) {
      return this.replaceCommonMathSymbols(formula);
    },

    // 解析行内公式
    parseInlineMath(text) {
      const segments = [];
      const regex = /\$([^$]+)\$|\\\(([^)]+)\\\)/g;
      let lastIndex = 0;
      let match;
      
      while ((match = regex.exec(text)) !== null) {
        // 添加公式前的文本
        if (match.index > lastIndex) {
          segments.push({
            type: 'text',
            content: text.substring(lastIndex, match.index)
          });
        }
        
        // 添加行内公式
        const formula = match[1] || match[2];
        segments.push({
          type: 'inline-math',
          content: this.processFormula(formula.trim()),
          key: Math.random().toString(36).substr(2, 9)
        });
        
        lastIndex = match.index + match[0].length;
      }
      
      // 添加剩余文本
      if (lastIndex < text.length) {
        segments.push({
          type: 'text',
          content: text.substring(lastIndex)
        });
      }
      
      // 如果没有匹配到公式，整个内容都是文本
      if (segments.length === 0) {
        segments.push({
          type: 'text',
          content: text
        });
      }
      
      return segments;
    },

    // 渲染LaTeX为图片URL（使用在线LaTeX渲染服务）
    renderLaTeXToImage(formula, displayMode = false) {
      try {
        // 使用多个LaTeX渲染服务作为备选
        const services = [
          {
            baseUrl: 'https://latex.codecogs.com/png.latex?',
            encoding: 'full'
          },
          {
            baseUrl: 'https://quicklatex.com/latex3.f/ql_',
            encoding: 'simple'
          },
          {
            baseUrl: 'https://chart.googleapis.com/chart?cht=tx&chl=',
            encoding: 'simple'
          }
        ];

        // 优先使用Codecogs服务
        const service = services[0];

        // 清理公式，移除可能的恶意代码
        const cleanFormula = this.cleanLaTeX(formula);

        // 根据显示模式设置参数
        const fontSize = displayMode ? 20 : 16;

        // 构建URL，添加缓存破坏参数确保最新渲染
        const timestamp = Date.now();
        const cacheBuster = `&t=${timestamp}`;
        const formulaParam = displayMode ? `\\displaystyle ${cleanFormula}` : cleanFormula;

        const encodedFormula = encodeURIComponent(formulaParam);
        const fullUrl = `${service.baseUrl}${encodedFormula}\\size=${fontSize}${cacheBuster}`;

        console.log('LaTeX图片URL:', fullUrl);
        return fullUrl;
      } catch (error) {
        console.error('生成LaTeX图片URL失败:', error);
        // 返回默认的占位图片或空字符串
        return '';
      }
    },

    // 清理LaTeX公式，移除潜在的安全风险
    cleanLaTeX(formula) {
      // 移除潜在的危险字符和命令
      return formula
        .replace(/\\input/g, '')
        .replace(/\\include/g, '')
        .replace(/\\write/g, '')
        .replace(/\\def/g, '')
        .replace(/\\newcommand/g, '')
        .replace(/\\renewcommand/g, '')
        .replace(/\\let/g, '')
        .replace(/\\catcode/g, '')
        .replace(/\\expandafter/g, '')
        .trim();
    },

    // 处理图片加载错误
    onImageError(e) {
      console.error('LaTeX图片加载失败:', e.detail);
      const { key } = e.currentTarget.dataset;
      
      // 显示原始LaTeX代码作为后备
      this.setData({
        [`renderedContent[${key}].type`]: 'fallback-text'
      });
    }
  }
});
