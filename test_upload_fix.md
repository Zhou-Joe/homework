# 微信小程序上传新题按钮修复说明

## 问题描述
在首页的"最近错题回顾"部分，"上传新题"按钮没有绑定函数，无法跳转到上传界面。

## 修复方案

### 1. 修改首页 WXML 文件
文件：`miniprogram/pages/index/index.wxml`

**修改前：**
```xml
<navigator url="/pages/upload/upload" class="more-link">上传新题</navigator>
```

**修改后：**
```xml
<text class="more-link" bindtap="onUploadNewQuestion" hover-class="more-link-hover">上传新题</text>
```

### 2. 添加点击事件处理函数
文件：`miniprogram/pages/index/index.js`

在 `onViewAllMistakes` 函数后添加：
```javascript
// 上传新题
onUploadNewQuestion() {
  wx.switchTab({
    url: '/pages/upload/upload'
  });
},
```

### 3. 优化按钮样式
文件：`miniprogram/pages/index/index.wxss`

为 `.more-link` 添加更明显的按钮样式：
```css
.more-link {
  font-size: 26rpx;
  color: var(--brand-primary);
  font-weight: 500;
  padding: 8rpx 16rpx;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 12rpx;
  border: 2rpx solid var(--brand-primary);
  transition: all 0.2s ease;
}

.more-link-hover {
  background: rgba(102, 126, 234, 0.2);
  transform: scale(0.95);
}
```

## 功能验证

### 测试步骤：
1. 打开微信小程序
2. 进入首页
3. 找到"最近错题回顾"部分
4. 点击"上传新题"按钮
5. 验证是否能正确跳转到上传界面

### 预期结果：
- "上传新题"按钮显示为带有边框的按钮样式
- 点击按钮时有视觉反馈（悬停效果）
- 正确跳转到上传界面（/pages/upload/upload）
- 上传界面功能正常：
  - 可以选择图片（拍照或从相册选择）
  - 可以上传图片进行AI分析
  - 可以保存分析结果到错题本

## 相关文件
- `miniprogram/pages/index/index.wxml` - 首页布局文件
- `miniprogram/pages/index/index.js` - 首页逻辑文件
- `miniprogram/pages/index/index.wxss` - 首页样式文件
- `miniprogram/pages/upload/upload.wxml` - 上传页面布局文件
- `miniprogram/pages/upload/upload.js` - 上传页面逻辑文件
- `miniprogram/utils/api.js` - API接口文件

## 注意事项
- 上传页面已在 app.json 的 tabBar 中配置
- 使用 `wx.switchTab` 进行跳转，因为上传页面是 tabBar 页面
- 上传功能依赖后端 API `/exercises/upload/`