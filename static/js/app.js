/**
 * FFmpeg Android 编译配置器 - 前端应用
 * 6步配置流程：预设 -> 格式 -> 编解码器 -> 网络协议 -> 优化 -> 编译
 */

class FFmpegConfigApp {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 9;
        this.config = {
            preset: 'basic',
            api: 21,
            outputType: 'shared',
            architectures: ['arm64-v8a', 'armeabi-v7a'],
            decoders: ['h264', 'aac', 'mp3'],
            encoders: [],
            muxers: ['mp4', 'm4a'],
            demuxers: ['mov', 'mp4', 'm4a', 'mp3'],
            protocols: ['file', 'http', 'https'],
            filters: [],
            optimizations: {
                disableAsm: true,
                enablePic: true,
                disableDebug: true,
                disableDoc: true,
                disablePrograms: true,
                enableSmall: false
            }
        };

        this.presets = {};
        this.isCompiling = false;
        this.logEventSource = null;
        this.autoScroll = true;

        this.init();
    }

    async init() {
        await this.loadPresets();
        this.setupEventListeners();
        this.showStep(1);
        this.updateStepNavigation();
        // 默认选中推荐的标准版预设
        this.selectDefaultPreset();
    }

    async loadPresets() {
        try {
            const response = await fetch('/api/presets');
            const data = await response.json();
            this.presets = data || {};
        } catch (error) {
            console.error('加载预设失败:', error);
        }
    }

    setupEventListeners() {
        // 步骤导航
        document.getElementById('prev-step').addEventListener('click', () => this.previousStep());
        document.getElementById('next-step').addEventListener('click', () => this.nextStep());
        document.getElementById('start-compile').addEventListener('click', () => this.startCompilation());

        // 步骤指示器点击
        document.querySelectorAll('.step-item').forEach((item, index) => {
            item.addEventListener('click', () => {
                const stepNum = index + 1;
                if (stepNum <= this.currentStep + 1) { // 只允许跳转到当前步骤或下一步
                    this.showStep(stepNum);
                }
            });
        });

        // 预设选择
        document.querySelectorAll('.preset-card').forEach(card => {
            card.addEventListener('click', (e) => this.selectPreset(e.target.closest('.preset-card')));
        });

        // 标签页切换
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target));
        });

        // 表单控件
        document.getElementById('api').addEventListener('change', (e) => {
            this.config.api = parseInt(e.target.value);
        });

        document.getElementById('outputType').addEventListener('change', (e) => {
            this.config.outputType = e.target.value;
        });

        // 复选框监听
        this.setupCheckboxListeners();

        // 编译相关按钮
        document.getElementById('final-compile-btn').addEventListener('click', () => this.startCompilation());
        document.getElementById('save-config-btn').addEventListener('click', () => this.saveConfig());
        document.getElementById('generate-script-btn').addEventListener('click', () => this.generateScript());
        document.getElementById('clear-logs-btn').addEventListener('click', () => this.clearLogs());
        document.getElementById('auto-scroll-btn').addEventListener('click', () => this.toggleAutoScroll());
    }

    setupCheckboxListeners() {
        // 架构选择
        document.querySelectorAll('input[name="architectures"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => this.updateArchitectures());
        });

        // 格式选择
        document.querySelectorAll('input[name="muxers"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => this.updateMuxers());
        });

        document.querySelectorAll('input[name="demuxers"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => this.updateDemuxers());
        });

        // 编解码器选择
        document.querySelectorAll('input[name="decoders"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => this.updateDecoders());
        });

        document.querySelectorAll('input[name="encoders"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => this.updateEncoders());
        });

        document.querySelectorAll('input[name="filters"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => this.updateFilters());
        });

        // 协议选择
        document.querySelectorAll('input[name="protocols"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => this.updateProtocols());
        });

        // 优化选项
        document.getElementById('enableSmall').addEventListener('change', (e) => {
            this.config.optimizations.enableSmall = e.target.checked;
        });

        document.getElementById('disableDebug').addEventListener('change', (e) => {
            this.config.optimizations.disableDebug = e.target.checked;
        });

        document.getElementById('disablePrograms').addEventListener('change', (e) => {
            this.config.optimizations.disablePrograms = e.target.checked;
        });

        document.getElementById('disableDoc').addEventListener('change', (e) => {
            this.config.optimizations.disableDoc = e.target.checked;
        });

        document.getElementById('enablePic').addEventListener('change', (e) => {
            this.config.optimizations.enablePic = e.target.checked;
        });

        document.getElementById('disableAsm').addEventListener('change', (e) => {
            this.config.optimizations.disableAsm = e.target.checked;
        });
    }

    selectPreset(card) {
        // 移除之前的选择
        document.querySelectorAll('.preset-card').forEach(c => c.classList.remove('selected'));

        // 选择当前卡片
        card.classList.add('selected');

        const presetName = card.dataset.preset;
        this.config.preset = presetName;

        // 应用预设配置
        if (this.presets[presetName]) {
            const presetConfig = this.presets[presetName].config;
       
            // 深度合并配置，确保嵌套对象也被正确更新
            this.config = {
                ...this.config,
                ...presetConfig,
                optimizations: {
                    ...this.config.optimizations,
                    ...presetConfig.optimizations
                }
            };

            // 显示选择的预设信息
            this.showSelectedPresetInfo(presetName);

            // 更新后续步骤的UI
            this.updateUIFromConfig();
        }
        // console.log(this.config)
    }

    selectDefaultPreset() {
        // 默认选择标准版预设
        const standardCard = document.querySelector('.preset-card[data-preset="standard"]');
        if (standardCard) {
            this.selectPreset(standardCard);
        }
    }

    showSelectedPresetInfo(presetName) {
        const info = document.getElementById('selected-preset-info');
        const nameSpan = document.getElementById('selected-preset-name');
        const descSpan = document.getElementById('selected-preset-description');

        if (this.presets[presetName]) {
            nameSpan.textContent = this.presets[presetName].name;
            descSpan.textContent = this.presets[presetName].description;
            info.style.display = 'block';
        }
    }

    updateUIFromConfig() {
        // 更新架构选择
        document.querySelectorAll('input[name="architectures"]').forEach(checkbox => {
            checkbox.checked = this.config.architectures.includes(checkbox.value);
        });

        // 更新格式选择
        document.querySelectorAll('input[name="muxers"]').forEach(checkbox => {
            checkbox.checked = this.config.muxers.includes(checkbox.value);
        });

        document.querySelectorAll('input[name="demuxers"]').forEach(checkbox => {
            checkbox.checked = this.config.demuxers.includes(checkbox.value);
        });

        // 更新编解码器选择
        document.querySelectorAll('input[name="decoders"]').forEach(checkbox => {
            checkbox.checked = this.config.decoders.includes(checkbox.value);
        });

        document.querySelectorAll('input[name="encoders"]').forEach(checkbox => {
            checkbox.checked = this.config.encoders.includes(checkbox.value);
        });

        document.querySelectorAll('input[name="filters"]').forEach(checkbox => {
            checkbox.checked = this.config.filters.includes(checkbox.value);
        });

        // 更新协议选择
        document.querySelectorAll('input[name="protocols"]').forEach(checkbox => {
            checkbox.checked = this.config.protocols.includes(checkbox.value);
        });

        // 更新基础设置
        document.getElementById('api').value = this.config.api;
        document.getElementById('outputType').value = this.config.outputType;

        // 更新优化选项
        document.getElementById('enableSmall').checked = this.config.optimizations.enableSmall;
        document.getElementById('disableDebug').checked = this.config.optimizations.disableDebug;
        document.getElementById('disablePrograms').checked = this.config.optimizations.disablePrograms;
        document.getElementById('disableDoc').checked = this.config.optimizations.disableDoc;
        document.getElementById('enablePic').checked = this.config.optimizations.enablePic;
        document.getElementById('disableAsm').checked = this.config.optimizations.disableAsm;
    }

    switchTab(button) {
        const tabName = button.dataset.tab;
        const tabContainer = button.closest('.section');

        // 更新按钮状态
        tabContainer.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');

        // 更新内容显示
        tabContainer.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });

        const targetContent = document.getElementById(tabName + '-tab');
        if (targetContent) {
            targetContent.classList.add('active');
        }
    }

    updateArchitectures() {
        this.config.architectures = Array.from(document.querySelectorAll('input[name="architectures"]:checked'))
            .map(cb => cb.value);
    }

    updateMuxers() {
        this.config.muxers = Array.from(document.querySelectorAll('input[name="muxers"]:checked'))
            .map(cb => cb.value);
    }

    updateDemuxers() {
        this.config.demuxers = Array.from(document.querySelectorAll('input[name="demuxers"]:checked'))
            .map(cb => cb.value);
    }

    updateDecoders() {
        this.config.decoders = Array.from(document.querySelectorAll('input[name="decoders"]:checked'))
            .map(cb => cb.value);
    }

    updateEncoders() {
        this.config.encoders = Array.from(document.querySelectorAll('input[name="encoders"]:checked'))
            .map(cb => cb.value);
    }

    updateFilters() {
        this.config.filters = Array.from(document.querySelectorAll('input[name="filters"]:checked'))
            .map(cb => cb.value);
    }

    updateProtocols() {
        this.config.protocols = Array.from(document.querySelectorAll('input[name="protocols"]:checked'))
            .map(cb => cb.value);
    }

    showStep(step) {
        // 隐藏所有步骤
        document.querySelectorAll('.step-section').forEach(section => {
            section.style.display = 'none';
            section.classList.remove('active');
        });

        // 显示当前步骤
        const currentSection = document.getElementById(`step-${step}`);
        if (currentSection) {
            currentSection.style.display = 'block';
            currentSection.classList.add('active');
            currentSection.classList.add('fade-in');
        }

        this.currentStep = step;
        this.updateStepNavigation();

        // 如果是最后一步，更新配置摘要
        if (step === 9) {
            this.updateConfigSummary();
        }
    }

    updateStepNavigation() {
        // 更新步骤指示器
        document.querySelectorAll('.step-item').forEach((item, index) => {
            const stepNum = index + 1;
            item.classList.remove('active', 'completed');

            if (stepNum === this.currentStep) {
                item.classList.add('active');
            } else if (stepNum < this.currentStep) {
                item.classList.add('completed');
            }
        });

        // 更新按钮状态
        const prevBtn = document.getElementById('prev-step');
        const nextBtn = document.getElementById('next-step');
        const compileBtn = document.getElementById('start-compile');

        prevBtn.disabled = this.currentStep === 1;

        if (this.currentStep === this.totalSteps) {
            nextBtn.style.display = 'none';
            compileBtn.style.display = 'inline-flex';
        } else {
            nextBtn.style.display = 'inline-flex';
            compileBtn.style.display = 'none';
        }
    }

    previousStep() {
        if (this.currentStep > 1) {
            this.showStep(this.currentStep - 1);
        }
    }

    nextStep() {
        if (this.currentStep < this.totalSteps) {
            // 验证当前步骤
            if (this.validateCurrentStep()) {
                this.showStep(this.currentStep + 1);
            }
        }
    }

    validateCurrentStep() {
        switch (this.currentStep) {
            case 1: // 预设选择
                if (!this.config.preset) {
                    alert('请选择一个配置预设');
                    return false;
                }
                break;
            case 2: // 解码器
                if (this.config.decoders.length === 0) {
                    alert('请至少选择一个解码器');
                    return false;
                }
                break;
            case 5: // 解复用器
                if (this.config.demuxers.length === 0) {
                    alert('请至少选择一个解复用器');
                    return false;
                }
                break;
            case 8: // 优化配置
                if (this.config.architectures.length === 0) {
                    alert('请至少选择一个目标架构');
                    return false;
                }
                break;
        }
        return true;
    }

    updateConfigSummary() {
        document.getElementById('summary-preset').textContent =
            this.presets[this.config.preset]?.name || this.config.preset;

        document.getElementById('summary-architectures').textContent =
            this.config.architectures.join(', ') || '无';

        document.getElementById('summary-decoders').textContent =
            this.config.decoders.slice(0, 5).join(', ') +
            (this.config.decoders.length > 5 ? ` 等${this.config.decoders.length}种` : '');

        document.getElementById('summary-encoders').textContent =
            this.config.encoders.length > 0 ?
                (this.config.encoders.slice(0, 5).join(', ') +
                    (this.config.encoders.length > 5 ? ` 等${this.config.encoders.length}种` : '')) : '无';

        document.getElementById('summary-muxers').textContent =
            this.config.muxers.slice(0, 5).join(', ') +
            (this.config.muxers.length > 5 ? ` 等${this.config.muxers.length}种` : '');

        document.getElementById('summary-demuxers').textContent =
            this.config.demuxers.slice(0, 5).join(', ') +
            (this.config.demuxers.length > 5 ? ` 等${this.config.demuxers.length}种` : '');

        document.getElementById('summary-filters').textContent =
            this.config.filters.length > 0 ?
                (this.config.filters.slice(0, 5).join(', ') +
                    (this.config.filters.length > 5 ? ` 等${this.config.filters.length}种` : '')) : '无';

        document.getElementById('summary-protocols').textContent =
            this.config.protocols.slice(0, 5).join(', ') +
            (this.config.protocols.length > 5 ? ` 等${this.config.protocols.length}种` : '');
    }

    async saveConfig() {
        try {
            const response = await fetch('/api/save-config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.config)
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('配置已保存', 'success');
            } else {
                this.showNotification('保存失败: ' + result.error, 'error');
            }
        } catch (error) {
            this.showNotification('保存失败: ' + error.message, 'error');
        }
    }

    async generateScript() {
        try {
            const response = await fetch('/api/generate-script', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.config)
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('编译脚本已生成: ' + result.script_path, 'success');
            } else {
                this.showNotification('生成失败: ' + result.error, 'error');
            }
        } catch (error) {
            this.showNotification('生成失败: ' + error.message, 'error');
        }
    }

    async startCompilation() {
        if (this.isCompiling) {
            this.showNotification('编译正在进行中...', 'warning');
            return;
        }

        if (!this.validateCurrentStep()) {
            return;
        }

        try {
            this.isCompiling = true;
            this.showCompileStatus();
            this.showLogContainer();

            const response = await fetch('/api/start-compilation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.config)
            });

            const result = await response.json();

            if (result.success) {
                this.startLogStream();
                this.startStatusPolling();
            } else {
                this.showNotification('启动编译失败: ' + result.error, 'error');
                this.isCompiling = false;
            }
        } catch (error) {
            this.showNotification('启动编译失败: ' + error.message, 'error');
            this.isCompiling = false;
        }
    }

    showCompileStatus() {
        document.getElementById('compile-status').style.display = 'block';
        document.getElementById('config-summary').style.display = 'none';
        document.getElementById('final-compile-btn').disabled = true;
        document.getElementById('final-compile-btn').innerHTML =
            '<span class="btn-icon">⏳</span>编译中...';
    }

    showLogContainer() {
        document.getElementById('log-container').style.display = 'block';
        document.getElementById('log-content').innerHTML = '';
    }

    startLogStream() {
        if (this.logEventSource) {
            this.logEventSource.close();
        }

        this.logEventSource = new EventSource('/api/logs/stream');

        this.logEventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                if (data.type === 'heartbeat' || data.type === 'connected') {
                    return;
                }

                this.addLogEntry(data);
            } catch (error) {
                console.error('解析日志数据失败:', error);
            }
        };

        this.logEventSource.onerror = (error) => {
            console.error('日志流连接错误:', error);
        };
    }

    startStatusPolling() {
        const pollStatus = async () => {
            try {
                const response = await fetch('/api/compilation-status');
                const status = await response.json();

                this.updateCompilationStatus(status);

                if (status.running) {
                    setTimeout(pollStatus, 60000);
                } else {
                    this.isCompiling = false;
                    this.onCompilationComplete(status);
                }
            } catch (error) {
                console.error('获取编译状态失败:', error);
                setTimeout(pollStatus, 60000);
            }
        };

        pollStatus();
    }

    updateCompilationStatus(status) {
        document.getElementById('status-text').textContent = status.status || '编译中...';
        document.getElementById('progress-fill').style.width = status.progress + '%';
        document.getElementById('progress-percentage').textContent = status.progress + '%';
        document.getElementById('progress-stage').textContent = status.status || '';

        // 更新状态指示器
        const indicator = document.getElementById('status-indicator');
        const statusDot = indicator.querySelector('.status-dot') || document.createElement('span');
        statusDot.className = 'status-dot ' + (status.running ? 'running' : 'idle');

        if (!indicator.querySelector('.status-dot')) {
            indicator.insertBefore(statusDot, indicator.firstChild);
        }
    }

    onCompilationComplete(status) {
        if (this.logEventSource) {
            this.logEventSource.close();
            this.logEventSource = null;
        }

        // 重新显示配置摘要
        document.getElementById('config-summary').style.display = 'block';

        const btn = document.getElementById('final-compile-btn');
        btn.disabled = false;

        if (status.success) {
            btn.innerHTML = '<span class="btn-icon">✅</span>编译完成';
            btn.classList.remove('btn-success');
            btn.classList.add('btn-success');
            this.showNotification('FFmpeg编译完成！', 'success');
        } else {
            btn.innerHTML = '<span class="btn-icon">❌</span>编译失败';
            btn.classList.remove('btn-success');
            btn.classList.add('btn-danger');
            this.showNotification('编译失败: ' + (status.error || '未知错误'), 'error');
        }

        // 更新状态指示器
        const indicator = document.getElementById('status-indicator');
        const statusDot = indicator.querySelector('.status-dot');
        if (statusDot) {
            statusDot.className = 'status-dot ' + (status.success ? 'success' : 'error');
        }
    }

    addLogEntry(logData) {
        const logContent = document.getElementById('log-content');
        const entry = document.createElement('div');
        entry.className = 'log-entry';

        const timestamp = document.createElement('span');
        timestamp.className = 'log-timestamp';
        timestamp.textContent = logData.timestamp;

        const message = document.createElement('span');
        message.className = 'log-level-' + (logData.level || 'info');
        message.textContent = logData.message;

        entry.appendChild(timestamp);
        entry.appendChild(message);
        logContent.appendChild(entry);

        if (this.autoScroll) {
            logContent.scrollTop = logContent.scrollHeight;
        }
    }

    clearLogs() {
        document.getElementById('log-content').innerHTML =
            '<div class="log-placeholder">日志已清空</div>';
    }

    toggleAutoScroll() {
        this.autoScroll = !this.autoScroll;
        const btn = document.getElementById('auto-scroll-btn');
        btn.textContent = this.autoScroll ? '自动滚动' : '手动滚动';
        btn.dataset.enabled = this.autoScroll;
    }

    showNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;

        // 添加样式
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '15px 20px',
            borderRadius: '8px',
            color: 'white',
            fontWeight: '500',
            zIndex: '10000',
            maxWidth: '400px',
            wordWrap: 'break-word'
        });

        // 设置背景色
        const colors = {
            success: '#28a745',
            error: '#dc3545',
            warning: '#ffc107',
            info: '#007bff'
        };
        notification.style.background = colors[type] || colors.info;

        document.body.appendChild(notification);

        // 自动移除
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.ffmpegApp = new FFmpegConfigApp();
});

// 添加一些全局样式
const style = document.createElement('style');
style.textContent = `
.notification {
    animation: slideInRight 0.3s ease-out;
}

@keyframes slideInRight {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

.btn-danger {
    background: #dc3545;
    color: white;
}

.btn-danger:hover:not(:disabled) {
    background: #c82333;
}
`;
document.head.appendChild(style);