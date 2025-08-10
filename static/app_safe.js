class SafeBrowserApp {
    constructor() {
        console.log('Initializing SafeBrowserApp');
        this.connected = false;
        this.currentUrl = '';
        this.vncClient = null;
        
        // Initialize elements safely
        this.initializeElements();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Start VNC connection
        this.startVNCConnection();
        
        // Initialize tabs
        this.tabs = new Map();
        this.activeTabId = 0;
        this.nextTabId = 1;
    }
    
    initializeElements() {
        // Browser controls - safe initialization
        this.backBtn = document.getElementById('backBtn');
        this.forwardBtn = document.getElementById('forwardBtn');
        this.refreshBtn = document.getElementById('refreshBtn');
        this.bookmarkBtn = document.getElementById('bookmarkBtn');
        this.historyBtn = document.getElementById('historyBtn');
        this.settingsBtn = document.getElementById('settingsBtn');
        this.urlInput = document.getElementById('urlInput');
        this.goBtn = document.getElementById('goBtn');
        
        // Status elements
        this.connectionStatus = document.getElementById('connectionStatus');
        this.browserStatus = document.getElementById('browserStatus');
        
        // Overlays
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.errorOverlay = document.getElementById('errorOverlay');
        this.errorText = document.getElementById('errorText');
        this.retryBtn = document.getElementById('retryBtn');
        
        // Canvas
        this.canvas = document.getElementById('vncCanvas');
    }
    
    setupEventListeners() {
        // Navigation controls - safe event binding
        if (this.backBtn) this.backBtn.addEventListener('click', () => this.sendBrowserCommand('back'));
        if (this.forwardBtn) this.forwardBtn.addEventListener('click', () => this.sendBrowserCommand('forward'));
        if (this.refreshBtn) this.refreshBtn.addEventListener('click', () => this.sendBrowserCommand('refresh'));
        
        // Tab controls
        const newTabBtn = document.getElementById('newTabBarBtn');
        if (newTabBtn) newTabBtn.addEventListener('click', () => this.createNewTab());
        
        // Enhanced controls
        if (this.bookmarkBtn) this.bookmarkBtn.addEventListener('click', () => this.addBookmark());
        if (this.historyBtn) this.historyBtn.addEventListener('click', () => this.showHistory());
        if (this.settingsBtn) this.settingsBtn.addEventListener('click', () => this.showSettings());
        
        // URL input
        if (this.urlInput) {
            this.urlInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.navigate();
                }
            });
        }
        
        if (this.goBtn) this.goBtn.addEventListener('click', () => this.navigate());
        
        // Retry button
        if (this.retryBtn) {
            this.retryBtn.addEventListener('click', () => {
                this.hideError();
                this.startVNCConnection();
            });
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
        
        // Window resize
        window.addEventListener('resize', () => {
            this.resizeCanvas();
        });
    }
    
    handleKeyboardShortcuts(e) {
        // Prevent shortcuts when typing in input fields
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }
        
        // Check for browser shortcuts
        if (e.ctrlKey || e.metaKey) {
            switch (e.key) {
                case 't':
                    e.preventDefault();
                    this.createNewTab();
                    break;
                case 'w':
                    e.preventDefault();
                    this.closeCurrentTab();
                    break;
                case 'r':
                    e.preventDefault();
                    this.sendBrowserCommand('refresh');
                    break;
                case 'd':
                    e.preventDefault();
                    this.addBookmark();
                    break;
                case 'l':
                    e.preventDefault();
                    if (this.urlInput) {
                        this.urlInput.focus();
                        this.urlInput.select();
                    }
                    break;
            }
        } else if (e.altKey) {
            switch (e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    this.sendBrowserCommand('back');
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.sendBrowserCommand('forward');
                    break;
            }
        }
    }
    
    startVNCConnection() {
        this.showLoading();
        this.updateConnectionStatus('connecting');
        this.updateBrowserStatus('Connecting to browser...');
        
        // Initialize VNC client
        this.vncClient = new VNCClient(this.canvas);
        
        // Override event handlers
        this.vncClient.onConnectionChange = (status) => {
            this.handleConnectionChange(status);
        };
        
        this.vncClient.onError = (message) => {
            this.showError(message);
        };
        
        // Connect to VNC
        this.vncClient.connect();
        
        // Render test pattern initially
        this.vncClient.renderTestPattern();
    }
    
    handleConnectionChange(status) {
        this.connected = (status === 'connected');
        this.updateConnectionStatus(status);
        
        switch (status) {
            case 'connected':
                this.hideLoading();
                this.hideError();
                this.updateBrowserStatus('Browser ready');
                this.enableControls(true);
                break;
                
            case 'disconnected':
                this.updateBrowserStatus('Disconnected');
                this.enableControls(false);
                break;
                
            case 'error':
                this.showError('Failed to connect to the remote browser');
                this.enableControls(false);
                break;
        }
    }
    
    sendBrowserCommand(command, data = {}) {
        if (!this.connected || !this.vncClient) {
            console.log('Not connected - cannot send command:', command);
            return;
        }
        
        const message = {
            type: 'browser_command',
            command: command,
            ...data
        };
        
        this.vncClient.sendMessage(message);
    }
    
    navigate() {
        if (!this.urlInput) return;
        
        const url = this.urlInput.value.trim();
        if (!url) return;
        
        this.currentUrl = url;
        this.sendBrowserCommand('navigate', { url: url });
        this.updateBrowserStatus(`Navigating to ${url}`);
    }
    
    createNewTab() {
        this.sendMessage({
            type: 'browser_command',
            command: 'new_tab'
        });
    }
    
    closeCurrentTab() {
        if (this.tabs.size <= 1) return;
        
        this.sendMessage({
            type: 'browser_command',
            command: 'close_tab',
            tab_id: this.activeTabId
        });
    }
    
    closeTab(tabId) {
        this.sendMessage({
            type: 'browser_command',
            command: 'close_tab',
            tab_id: tabId
        });
    }
    
    switchToTab(tabId) {
        this.sendMessage({
            type: 'browser_command',
            command: 'switch_tab',
            tab_id: tabId
        });
    }
    
    updateTabsUI(tabsInfo) {
        const tabBar = document.getElementById('tabBar');
        const newTabBtn = document.getElementById('newTabBarBtn');
        
        if (!tabBar || !newTabBtn) return;
        
        // Clear existing tabs except the new tab button
        const existingTabs = tabBar.querySelectorAll('.tab');
        existingTabs.forEach(tab => tab.remove());
        
        // Create tabs
        tabsInfo.forEach(tabInfo => {
            const tabElement = this.createTabElement(tabInfo);
            tabBar.insertBefore(tabElement, newTabBtn);
        });
        
        // Update tabs map
        this.tabs.clear();
        tabsInfo.forEach(tab => this.tabs.set(tab.id, tab));
    }
    
    createTabElement(tabInfo) {
        const tab = document.createElement('div');
        tab.className = `tab ${tabInfo.id === this.activeTabId ? 'active' : ''}`;
        tab.id = `tab-${tabInfo.id}`;
        tab.dataset.tabId = tabInfo.id;
        
        tab.innerHTML = `
            <span class="tab-title">${this.truncateTitle(tabInfo.title)}</span>
            <button class="tab-close" onclick="window.app && window.app.closeTab(${tabInfo.id})">×</button>
        `;
        
        tab.addEventListener('click', (e) => {
            if (!e.target.classList.contains('tab-close')) {
                this.switchToTab(tabInfo.id);
            }
        });
        
        return tab;
    }
    
    truncateTitle(title) {
        return title.length > 20 ? title.substring(0, 20) + '...' : title;
    }
    
    sendMessage(message) {
        if (this.vncClient && this.vncClient.connected) {
            this.vncClient.sendMessage(message);
        }
    }
    
    updateConnectionStatus(status) {
        if (!this.connectionStatus) return;
        
        this.connectionStatus.className = `status-${status}`;
        
        const statusText = {
            'connected': 'Connected',
            'disconnected': 'Disconnected', 
            'connecting': 'Connecting...',
            'error': 'Error'
        };
        
        const icon = {
            'connected': 'fas fa-circle',
            'disconnected': 'fas fa-circle',
            'connecting': 'fas fa-spinner fa-spin',
            'error': 'fas fa-exclamation-circle'
        };
        
        this.connectionStatus.innerHTML = `
            <i class="${icon[status]}"></i> ${statusText[status]}
        `;
    }
    
    updateBrowserStatus(status) {
        if (this.browserStatus && typeof this.browserStatus.textContent !== 'undefined') {
            this.browserStatus.textContent = status;
        }
    }
    
    enableControls(enabled) {
        if (this.backBtn) this.backBtn.disabled = !enabled;
        if (this.forwardBtn) this.forwardBtn.disabled = !enabled;
        if (this.refreshBtn) this.refreshBtn.disabled = !enabled;
        if (this.urlInput) this.urlInput.disabled = !enabled;
        if (this.goBtn) this.goBtn.disabled = !enabled;
    }
    
    showLoading() {
        if (this.loadingOverlay) this.loadingOverlay.style.display = 'flex';
    }
    
    hideLoading() {
        if (this.loadingOverlay) this.loadingOverlay.style.display = 'none';
    }
    
    showError(message) {
        if (this.errorText) this.errorText.textContent = message;
        if (this.errorOverlay) this.errorOverlay.style.display = 'flex';
        this.hideLoading();
    }
    
    hideError() {
        if (this.errorOverlay) this.errorOverlay.style.display = 'none';
    }
    
    addBookmark() {
        console.log('Adding bookmark feature not yet implemented');
    }
    
    showHistory() {
        console.log('History feature not yet implemented');
    }
    
    showSettings() {
        console.log('Settings feature not yet implemented');
    }
    
    resizeCanvas() {
        if (!this.canvas) return;
        
        const container = this.canvas.parentElement;
        if (!container) return;
        
        const containerRect = container.getBoundingClientRect();
        
        // Maintain aspect ratio
        const aspectRatio = 1280 / 720;
        let newWidth = containerRect.width - 20;
        let newHeight = newWidth / aspectRatio;
        
        if (newHeight > containerRect.height - 20) {
            newHeight = containerRect.height - 20;
            newWidth = newHeight * aspectRatio;
        }
        
        this.canvas.style.width = newWidth + 'px';
        this.canvas.style.height = newHeight + 'px';
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing SafeBrowserApp');
    window.app = new SafeBrowserApp();
    
    // Initial canvas resize
    setTimeout(() => {
        if (window.app) window.app.resizeCanvas();
    }, 100);
});