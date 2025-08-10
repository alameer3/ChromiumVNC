/**
 * Main application logic for the web-based Chromium browser
 */
class BrowserApp {
    constructor() {
        this.vncClient = null;
        this.connected = false;
        this.currentUrl = '';
        
        this.initializeElements();
        this.setupEventListeners();
        this.startVNCConnection();
    }
    
    initializeElements() {
        // Browser controls
        this.backBtn = document.getElementById('backBtn');
        this.forwardBtn = document.getElementById('forwardBtn');
        this.refreshBtn = document.getElementById('refreshBtn');
        // this.newTabBtn = document.getElementById('newTabBtn'); // Removed as it doesn't exist
        this.bookmarkBtn = document.getElementById('bookmarkBtn');
        this.historyBtn = document.getElementById('historyBtn');
        this.settingsBtn = document.getElementById('settingsBtn');
        this.urlInput = document.getElementById('urlInput');
        this.goBtn = document.getElementById('goBtn');
        
        // Status elements
        this.connectionStatus = document.getElementById('connectionStatus');
        this.browserStatus = document.getElementById('browserStatus') || document.createElement('div'); // fallback
        this.currentResolution = document.getElementById('currentResolution') || document.createElement('div'); // fallback
        this.loadingProgress = document.getElementById('loadingProgress') || document.createElement('div'); // fallback
        
        // Overlays
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.errorOverlay = document.getElementById('errorOverlay');
        this.errorText = document.getElementById('errorText');
        this.retryBtn = document.getElementById('retryBtn');
        
        // Modals (with safe fallbacks)
        this.settingsModal = document.getElementById('settingsModal') || document.createElement('div');
        this.bookmarksModal = document.getElementById('bookmarksModal') || document.createElement('div');
        this.historyModal = document.getElementById('historyModal') || document.createElement('div');
        this.resolutionSelect = document.getElementById('resolutionSelect') || document.createElement('select');
        this.applyResolution = document.getElementById('applyResolution') || document.createElement('button');
        
        // Canvas
        this.canvas = document.getElementById('vncCanvas');
    }
    
    setupEventListeners() {
        // Navigation controls
        this.backBtn.addEventListener('click', () => this.sendBrowserCommand('back'));
        this.forwardBtn.addEventListener('click', () => this.sendBrowserCommand('forward'));
        this.refreshBtn.addEventListener('click', () => this.sendBrowserCommand('refresh'));
        
        // Tab controls
        document.getElementById('newTabBarBtn').addEventListener('click', () => this.createNewTab());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
        
        // Enhanced controls
        this.bookmarkBtn.addEventListener('click', () => this.addBookmark());
        this.historyBtn.addEventListener('click', () => this.showHistory());
        this.settingsBtn.addEventListener('click', () => this.showSettings());
        
        // URL input
        this.urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.navigate();
            }
        });
        
        this.goBtn.addEventListener('click', () => this.navigate());
        
        // Settings controls (safe event binding)
        if (this.applyResolution && this.applyResolution.addEventListener) {
            this.applyResolution.addEventListener('click', () => this.changeResolution());
        }
        
        // Modal close buttons (safe event binding)
        const closeSettings = document.getElementById('closeSettings');
        const closeBookmarks = document.getElementById('closeBookmarks');
        const closeHistory = document.getElementById('closeHistory');
        
        if (closeSettings) closeSettings.addEventListener('click', () => this.hideModal('settings'));
        if (closeBookmarks) closeBookmarks.addEventListener('click', () => this.hideModal('bookmarks'));
        if (closeHistory) closeHistory.addEventListener('click', () => this.hideModal('history'));
        
        // Close modals when clicking outside (safe)
        [this.settingsModal, this.bookmarksModal, this.historyModal].forEach(modal => {
            if (modal && modal.addEventListener) {
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) {
                        modal.style.display = 'none';
                    }
                });
            }
        });
        
        // Retry button (safe)
        if (this.retryBtn) {
            this.retryBtn.addEventListener('click', () => {
                this.hideError();
                this.startVNCConnection();
            });
        }
        
        // Window resize
        window.addEventListener('resize', () => {
            this.resizeCanvas();
        });
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
        
        this.vncClient.onCommandResult = (result) => {
            this.handleCommandResult(result);
        };
        
        // Connect to VNC
        this.vncClient.connect();
        
        // Render test pattern initially
        this.vncClient.renderTestPattern();
        
        // Initialize tabs
        this.tabs = new Map();
        this.activeTabId = 0;
        this.nextTabId = 1;
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
                case 'h':
                    e.preventDefault();
                    this.showHistory();
                    break;
                case 'l':
                    e.preventDefault();
                    this.urlInput.focus();
                    this.urlInput.select();
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
        
        // Tab switching with Ctrl+Number
        if ((e.ctrlKey || e.metaKey) && e.key >= '1' && e.key <= '9') {
            e.preventDefault();
            const tabIndex = parseInt(e.key) - 1;
            this.switchToTabByIndex(tabIndex);
        }
    }
    
    createNewTab() {
        this.sendMessage({
            type: 'browser_command',
            command: 'new_tab'
        });
    }
    
    closeCurrentTab() {
        if (this.tabs.size <= 1) return; // Don't close the last tab
        
        this.sendMessage({
            type: 'browser_command',
            command: 'close_tab',
            tab_id: this.activeTabId
        });
    }
    
    switchToTab(tabId) {
        this.sendMessage({
            type: 'browser_command',
            command: 'switch_tab',
            tab_id: tabId
        });
    }
    
    switchToTabByIndex(index) {
        const tabIds = Array.from(this.tabs.keys()).sort((a, b) => a - b);
        if (index < tabIds.length) {
            this.switchToTab(tabIds[index]);
        }
    }
    
    updateTabsUI(tabsInfo) {
        const tabBar = document.getElementById('tabBar');
        const newTabBtn = document.getElementById('newTabBarBtn');
        
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
    
    closeTab(tabId) {
        this.sendMessage({
            type: 'browser_command',
            command: 'close_tab',
            tab_id: tabId
        });
    }
    
    sendMessage(message) {
        if (this.vncClient && this.vncClient.connected) {
            this.vncClient.sendMessage(message);
        }
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
    
    handleCommandResult(result) {
        if (result.success) {
            console.log(`Command ${result.command} executed successfully`);
            
            // Update UI based on command
            switch (result.command) {
                case 'navigate':
                    this.updateBrowserStatus('Navigating...');
                    break;
                case 'back':
                case 'forward':
                    this.updateBrowserStatus('Navigation completed');
                    break;
                case 'refresh':
                    this.updateBrowserStatus('Page refreshed');
                    break;
                case 'new_tab':
                    this.updateBrowserStatus('New tab opened');
                    break;
            }
        } else {
            console.error(`Command ${result.command} failed:`, result.error);
            this.updateBrowserStatus(`Error: ${result.error}`);
        }
    }
    
    sendBrowserCommand(command, data = {}) {
        if (!this.connected || !this.vncClient) {
            this.showError('Not connected to browser');
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
        const url = this.urlInput.value.trim();
        if (!url) return;
        
        this.currentUrl = url;
        this.sendBrowserCommand('navigate', { url: url });
        this.updateBrowserStatus(`Navigating to ${url}`);
    }
    
    updateConnectionStatus(status) {
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
        console.log('Updating browser status:', status);
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
    
    // Enhanced features methods
    addBookmark() {
        if (!this.connected || !this.vncClient) {
            this.showError('Not connected to browser');
            return;
        }
        
        this.vncClient.sendMessage({
            type: 'add_bookmark'
        });
    }
    
    showHistory() {
        if (!this.connected || !this.vncClient) {
            this.showError('Not connected to browser');
            return;
        }
        
        this.vncClient.sendMessage({
            type: 'get_history'
        });
        this.historyModal.style.display = 'block';
    }
    
    showSettings() {
        this.settingsModal.style.display = 'block';
    }
    
    hideModal(modalType) {
        switch(modalType) {
            case 'settings':
                this.settingsModal.style.display = 'none';
                break;
            case 'bookmarks':
                this.bookmarksModal.style.display = 'none';
                break;
            case 'history':
                this.historyModal.style.display = 'none';
                break;
        }
    }
    
    changeResolution() {
        const newResolution = this.resolutionSelect.value;
        if (!this.connected || !this.vncClient) {
            this.showError('Not connected to browser');
            return;
        }
        
        this.vncClient.sendMessage({
            type: 'change_resolution',
            resolution: newResolution
        });
        
        this.currentResolution.textContent = newResolution;
        this.hideModal('settings');
    }
    
    populateBookmarks(bookmarks) {
        const container = document.getElementById('bookmarksList');
        if (!container) return;
        container.innerHTML = '';
        
        if (bookmarks.length === 0) {
            container.innerHTML = '<p style="color: #666; text-align: center; padding: 20px;">No bookmarks yet</p>';
            return;
        }
        
        bookmarks.forEach(bookmark => {
            const item = document.createElement('div');
            item.className = 'list-item';
            item.innerHTML = `
                <div class="list-item-title">${bookmark.title || 'Untitled'}</div>
                <div class="list-item-url">${bookmark.url}</div>
            `;
            item.addEventListener('click', () => {
                this.urlInput.value = bookmark.url;
                this.navigate();
                this.hideModal('bookmarks');
            });
            container.appendChild(item);
        });
    }
    
    populateHistory(history) {
        const container = document.getElementById('historyList');
        if (!container) return;
        container.innerHTML = '';
        
        if (history.length === 0) {
            container.innerHTML = '<p style="color: #666; text-align: center; padding: 20px;">No history yet</p>';
            return;
        }
        
        history.reverse().forEach(url => {
            const item = document.createElement('div');
            item.className = 'list-item';
            item.innerHTML = `
                <div class="list-item-title">${this.getDomainFromUrl(url)}</div>
                <div class="list-item-url">${url}</div>
            `;
            item.addEventListener('click', () => {
                this.urlInput.value = url;
                this.navigate();
                this.hideModal('history');
            });
            container.appendChild(item);
        });
    }
    
    getDomainFromUrl(url) {
        try {
            return new URL(url).hostname;
        } catch {
            return url;
        }
    }
    
    showLoadingProgress() {
        this.loadingProgress.style.display = 'block';
        this.updateBrowserStatus('Loading...');
    }
    
    hideLoadingProgress() {
        this.loadingProgress.style.display = 'none';
    }

    resizeCanvas() {
        const container = this.canvas.parentElement;
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
    window.app = new BrowserApp();
    
    // Initial canvas resize
    setTimeout(() => {
        window.app.resizeCanvas();
    }, 100);
});

// Handle keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl+R or F5 for refresh
    if ((e.ctrlKey && e.key === 'r') || e.key === 'F5') {
        e.preventDefault();
        // Don't refresh the page, refresh the remote browser instead
        if (window.app && window.app.connected) {
            window.app.sendBrowserCommand('refresh');
        }
    }
    
    // Ctrl+T for new tab
    if (e.ctrlKey && e.key === 't') {
        e.preventDefault();
        if (window.app && window.app.connected) {
            window.app.sendBrowserCommand('new_tab');
        }
    }
    
    // Alt+Left for back
    if (e.altKey && e.key === 'ArrowLeft') {
        e.preventDefault();
        if (window.app && window.app.connected) {
            window.app.sendBrowserCommand('back');
        }
    }
    
    // Alt+Right for forward
    if (e.altKey && e.key === 'ArrowRight') {
        e.preventDefault();
        if (window.app && window.app.connected) {
            window.app.sendBrowserCommand('forward');
        }
    }
});
