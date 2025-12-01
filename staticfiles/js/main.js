// 全局变量
let accessToken = localStorage.getItem('access_token');
let refreshToken = localStorage.getItem('refresh_token');

// API基础URL
const API_BASE_URL = '/api';

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面
    initPage();

    // 绑定全局事件
    bindGlobalEvents();
});

// 初始化页面
function initPage() {
    // 检查用户登录状态
    checkAuthStatus();

    // 初始化工具提示
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

// 绑定全局事件
function bindGlobalEvents() {
    // 文件上传事件
    const uploadAreas = document.querySelectorAll('.upload-area');
    uploadAreas.forEach(area => {
        area.addEventListener('dragover', handleDragOver);
        area.addEventListener('dragleave', handleDragLeave);
        area.addEventListener('drop', handleFileDrop);
        area.addEventListener('click', () => {
            const fileInput = area.querySelector('input[type="file"]');
            if (fileInput) fileInput.click();
        });
    });
}

// 检查用户认证状态
async function checkAuthStatus() {
    const currentPage = window.location.pathname;

    // 这些页面不需要认证
    const publicPages = ['/login/', '/register/', '/'];
    if (publicPages.some(page => currentPage.includes(page))) {
        return;
    }

    if (!accessToken) {
        // 重定向到登录页
        if (!currentPage.includes('/login/') && !currentPage.includes('/register/')) {
            window.location.href = '/login/';
        }
        return;
    }

    // 验证token是否有效
    try {
        const response = await fetch(`${API_BASE_URL}/auth/user-info/`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (!response.ok) {
            throw new Error('Token invalid');
        }

        const userData = await response.json();
        updateUserInterface(userData);

    } catch (error) {
        console.error('认证检查失败:', error);
        await refreshAccessToken();
    }
}

// 更新用户界面
function updateUserInterface(userData) {
    // 更新用户名显示
    const userNameElements = document.querySelectorAll('.user-name');
    userNameElements.forEach(element => {
        element.textContent = userData.nickname || userData.username;
    });

    // 更新用户头像
    const userAvatarElements = document.querySelectorAll('.user-avatar');
    userAvatarElements.forEach(element => {
        element.textContent = (userData.nickname || userData.username).charAt(0).toUpperCase();
    });
}

// 刷新访问令牌
async function refreshAccessToken() {
    if (!refreshToken) {
        window.location.href = '/login/';
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/auth/token/refresh/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                refresh: refreshToken
            })
        });

        if (!response.ok) {
            throw new Error('Refresh token invalid');
        }

        const data = await response.json();
        accessToken = data.access;
        localStorage.setItem('access_token', accessToken);

    } catch (error) {
        console.error('Token刷新失败:', error);
        logout();
    }
}

// 登出
async function logout() {
    try {
        // 先尝试JWT登出
        if (refreshToken) {
            await fetch(`${API_BASE_URL}/auth/logout/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${accessToken}`
                },
                body: JSON.stringify({
                    refresh: refreshToken
                })
            });
        }
    } catch (error) {
        console.error('JWT登出请求失败:', error);
    }

    try {
        // 再尝试Django session登出
        await fetch('/logout/', {
            method: 'GET',
            credentials: 'same-origin'
        });
    } catch (error) {
        console.error('Django登出请求失败:', error);
    }

    finally {
        // 清除本地存储
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        accessToken = null;
        refreshToken = null;

        // 强制刷新页面以更新Django session状态
        window.location.reload();
    }
}

// API请求封装
async function apiRequest(url, options = {}) {
    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    };

    if (accessToken) {
        config.headers['Authorization'] = `Bearer ${accessToken}`;
    }

    try {
        let response = await fetch(`${API_BASE_URL}${url}`, config);

        // 如果token过期，尝试刷新
        if (response.status === 401 && refreshToken) {
            await refreshAccessToken();
            config.headers['Authorization'] = `Bearer ${accessToken}`;
            response = await fetch(`${API_BASE_URL}${url}`, config);
        }

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }

        return await response.json();

    } catch (error) {
        console.error('API请求失败:', error);
        throw error;
    }
}

// 文件上传封装
async function uploadFile(file, url, additionalData = {}) {
    const formData = new FormData();
    formData.append('image', file);

    // 添加额外数据
    Object.keys(additionalData).forEach(key => {
        formData.append(key, additionalData[key]);
    });

    const config = {
        method: 'POST',
        headers: {},
        body: formData
    };

    if (accessToken) {
        config.headers['Authorization'] = `Bearer ${accessToken}`;
    }

    try {
        let response = await fetch(`${API_BASE_URL}${url}`, config);

        // 如果token过期，尝试刷新
        if (response.status === 401 && refreshToken) {
            await refreshAccessToken();
            config.headers['Authorization'] = `Bearer ${accessToken}`;
            response = await fetch(`${API_BASE_URL}${url}`, config);
        }

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }

        return await response.json();

    } catch (error) {
        console.error('文件上传失败:', error);
        throw error;
    }
}

// 显示消息提示
function showMessage(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    const container = document.querySelector('.container');
    const messageDiv = document.createElement('div');
    messageDiv.innerHTML = alertHtml;
    container.insertBefore(messageDiv.firstElementChild, container.firstElementChild);

    // 自动消失
    setTimeout(() => {
        const alert = container.querySelector('.alert');
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

// 文件拖拽处理
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    this.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    this.classList.remove('dragover');
}

function handleFileDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    this.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
}

// 文件选择处理
function handleFileSelect(file) {
    // 验证文件类型
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'application/pdf'];
    if (!allowedTypes.includes(file.type)) {
        showMessage('请选择图片文件或PDF文件', 'warning');
        return;
    }

    // 验证文件大小 (10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showMessage('文件大小不能超过10MB', 'warning');
        return;
    }

    // 显示文件信息
    const fileInput = document.querySelector('input[type="file"]');
    const fileName = document.querySelector('.file-name');

    if (fileInput) {
        fileInput.files = new DataTransfer().files;
        const dt = new DataTransfer();
        dt.items.add(file);
        fileInput.files = dt.files;
    }

    if (fileName) {
        fileName.textContent = file.name;
    }

    // 如果是图片，显示预览
    if (file.type.startsWith('image/')) {
        showImagePreview(file);
    }
}

// 显示图片预览
function showImagePreview(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const previewContainer = document.querySelector('.image-preview');
        if (previewContainer) {
            previewContainer.innerHTML = `
                <img src="${e.target.result}" class="img-fluid rounded" alt="预览">
                <button type="button" class="btn btn-sm btn-danger position-absolute top-0 end-0 m-2" onclick="clearImagePreview()">
                    <i class="fas fa-times"></i>
                </button>
            `;
            previewContainer.classList.remove('d-none');
            previewContainer.classList.add('position-relative');
        }
    };
    reader.readAsDataURL(file);
}

// 清除图片预览
function clearImagePreview() {
    const previewContainer = document.querySelector('.image-preview');
    const fileInput = document.querySelector('input[type="file"]');
    const fileName = document.querySelector('.file-name');

    if (previewContainer) {
        previewContainer.innerHTML = '';
        previewContainer.classList.add('d-none');
    }

    if (fileInput) {
        fileInput.value = '';
    }

    if (fileName) {
        fileName.textContent = '';
    }
}

// 格式化数字
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// 格式化百分比
function formatPercentage(num) {
    return parseFloat(num).toFixed(1) + '%';
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 显示加载状态
function showLoading(element, text = '加载中...') {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }

    if (element) {
        element.innerHTML = `
            <div class="loading">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">${text}</span>
                </div>
                <div class="mt-2">${text}</div>
            </div>
        `;
    }
}

// 隐藏加载状态
function hideLoading(element, content = '') {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }

    if (element) {
        element.innerHTML = content;
    }
}

// 确认对话框
function confirmDialog(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 渲染数学公式
async function renderMathInElement(element) {
    if (!window.MathJax) {
        console.warn('MathJax未加载，等待加载...');
        // 等待MathJax加载
        return new Promise((resolve) => {
            const checkMathJax = () => {
                if (window.MathJax && window.MathJax.typesetPromise) {
                    renderMathInElement(element).then(resolve);
                } else {
                    setTimeout(checkMathJax, 100);
                }
            };
            checkMathJax();
        });
    }

    try {
        // 等待MathJax准备就绪
        if (window.MathJax.typesetPromise) {
            await window.MathJax.typesetPromise([element]);
        } else if (window.MathJax && window.MathJax.Hub) {
            // 兼容旧版MathJax
            return new Promise((resolve) => {
                window.MathJax.Hub.Queue(["Typeset", window.MathJax.Hub, element], resolve);
            });
        }
    } catch (error) {
        console.error('数学公式渲染失败:', error);
    }
}

// 渲染页面中所有数学公式
async function renderAllMath() {
    if (!window.MathJax) {
        console.warn('MathJax未加载');
        return;
    }

    try {
        // 等待MathJax准备就绪
        if (window.MathJax.typesetPromise) {
            await window.MathJax.typesetPromise();
        } else if (window.MathJax && window.MathJax.Hub) {
            // 兼容旧版MathJax
            window.MathJax.Hub.Queue(["Typeset", window.MathJax.Hub]);
        }
    } catch (error) {
        console.error('数学公式渲染失败:', error);
    }
}

// 处理包含数学公式的文本
function processMathContent(text) {
    // 检测常见的数学公式模式并转换为LaTeX格式
    let processedText = text;

    // 转换常见的数学表达式模式
    // 例如: x^2 转换为 $x^2$
    processedText = processedText.replace(/\b([a-zA-Z])\^(\d+)\b/g, '$1^{$2}');

    // 转换分数格式，如: 1/2 转换为 $\frac{1}{2}$
    processedText = processedText.replace(/\b(\d+)\s*\/\s*(\d+)\b/g, '\\frac{$1}{$2}');

    // 转换平方根格式，如: √x 转换为 $\sqrt{x}$
    processedText = processedText.replace(/√([^\s]+)/g, '\\sqrt{$1}');

    // 转换积分格式
    processedText = processedText.replace(/∫/g, '\\int');

    // 转换求和格式
    processedText = processedText.replace(/Σ/g, '\\sum');

    // 转换希腊字母
    processedText = processedText.replace(/α/g, '\\alpha');
    processedText = processedText.replace(/β/g, '\\beta');
    processedText = processedText.replace(/γ/g, '\\gamma');
    processedText = processedText.replace(/δ/g, '\\delta');
    processedText = processedText.replace(/θ/g, '\\theta');
    processedText = processedText.replace(/λ/g, '\\lambda');
    processedText = processedText.replace(/μ/g, '\\mu');
    processedText = processedText.replace(/π/g, '\\pi');
    processedText = processedText.replace(/σ/g, '\\sigma');
    processedText = processedText.replace(/φ/g, '\\phi');
    processedText = processedText.replace(/ω/g, '\\omega');

    return processedText;
}

// 安全地设置包含数学公式的内容
async function setMathContent(element, content) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }

    if (!element) return;

    // 确保内容为字符串
    if (typeof content !== 'string') {
        content = String(content || '');
    }

    // 处理数学公式内容 - 不在这里转换，因为AI已经输出LaTeX格式
    let processedContent = content;

    // 如果内容不包含LaTeX，才进行简单转换
    if (!content.includes('\\') && !content.includes('$')) {
        processedContent = processMathContent(content);
    }

    // 设置内容
    element.innerHTML = processedContent;

    // 等待一下DOM更新再渲染
    await new Promise(resolve => setTimeout(resolve, 50));

    // 渲染数学公式
    try {
        await renderMathInElement(element);
    } catch (error) {
        console.warn('MathJax渲染失败，但内容已设置:', error);
    }
}