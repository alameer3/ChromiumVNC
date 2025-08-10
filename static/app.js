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
        this.newTabBtn = document.getElementById('newTabBtn');
        this.bookmarkBtn = document.getElementById('bookmarkBtn');
        this.historyBtn = document.getElementById('historyBtn');
        this.settingsBtn = document.getElementById('settingsBtn');
        this.urlInput = document.getElementById('urlInput');
        this.goBtn = document.getElementById('goBtn');
        
        // Status elements
        this.connectionStatus = document.getElementById('connectionStatus');
        this.browserStatus = document.getElementById('browserStatus');
        this.currentResolution = document.getElementById('currentResolution');
        this.loadingProgress = document.getElementById('loadingProgress');
        
        // Overlays
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.errorOverlay = document.getElementById('errorOverlay');
        this.errorText = document.getElementById('errorText');
        this.retryBtn = document.getElementById('retryBtn');
        
        // Modals
        this.settingsModal = document.getElementById('settingsModal');
        this.bookmarksModal = document.getElementById('bookmarksModal');
        this.historyModal = document.getElementById('historyModal');
        this.resolutionSelect = document.getElementById('resolutionSelect');
        this.applyResolution = document.getElementById('applyResolution');
        
        // Canvas
        this.canvas = document.getElementById('vncCanvas');
    }
    
    setupEventListeners() {
        // Navigation controls
        this.backBtn.addEventListener('click', () => this.sendBrowserCommand('back'));
        this.forwardBtn.addEventListener('click', () => this.sendBrowserCommand('forward'));
        this.refreshBtn.addEventListener('click', () => this.sendBrowserCommand('refresh'));
        this.newTabBtn.addEventListener('click', () => this.sendBrowserCommand('new_tab'));
        
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
        
        // Settings controls
        this.applyResolution.addEventListener('click', () => this.changeResolution());
        
        // Modal close buttons
        document.getElementById('closeSettings').addEventListener('click', () => this.hideModal('settings'));
        document.getElementById('closeBookmarks').addEventListener('click', () => this.hideModal('bookmarks'));
        document.getElementById('closeHistory').addEventListener('click', () => this.hideModal('history'));
        
        // Close modals when clicking outside
        [this.settingsModal, this.bookmarksModal, this.historyModal].forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.style.display = 'none';
                }
            });
        });
        
        // Retry button
        this.retryBtn.addEventListener('click', () => {
            this.hideError();
            this.startVNCConnection();
        });
        
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
        this.browserStatus.textContent = status;
    }
    
    enableControls(enabled) {
        this.backBtn.disabled = !enabled;
        this.forwardBtn.disabled = !enabled;
        this.refreshBtn.disabled = !enabled;
        this.newTabBtn.disabled = !enabled;
        this.urlInput.disabled = !enabled;
        this.goBtn.disabled = !enabled;
    }
    
    showLoading() {
        this.loadingOverlay.style.display = 'flex';
    }
    
    hideLoading() {
        this.loadingOverlay.style.display = 'none';
    }
    
    showError(message) {
        this.errorText.textContent = message;
        this.errorOverlay.style.display = 'flex';
        this.hideLoading();
    }
    
    hideError() {
        this.errorOverlay.style.display = 'none';
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
    const app = new BrowserApp();
    
    // Initial canvas resize
    setTimeout(() => {
        app.resizeCanvas();
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
