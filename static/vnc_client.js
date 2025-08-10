/**
 * VNC Client for handling remote desktop connection
 */
class VNCClient {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.websocket = null;
        this.connected = false;
        this.imageData = null;
        
        // Mouse and keyboard state
        this.mouseButtons = 0;
        this.lastMouseX = 0;
        this.lastMouseY = 0;
        
        // Setup event listeners
        this.setupEventListeners();
    }
    
    connect() {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.hostname}:8000/ws`;
        
        console.log('Connecting to:', wsUrl);
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            console.log('WebSocket connected');
            this.connected = true;
            this.onConnectionChange('connected');
            // Start periodic screenshots to show browser content
            this.startPeriodicScreenshots();
            // Request initial screenshot
            setTimeout(() => this.requestScreenCapture(), 1000);
        };
        
        this.websocket.onmessage = (event) => {
            this.handleMessage(event.data);
        };
        
        this.websocket.onclose = () => {
            console.log('WebSocket disconnected');
            this.connected = false;
            this.stopPeriodicScreenshots();
            this.onConnectionChange('disconnected');
            
            // Auto-reconnect after 3 seconds
            setTimeout(() => {
                if (!this.connected) {
                    this.connect();
                }
            }, 3000);
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.onConnectionChange('error');
        };
    }
    
    disconnect() {
        this.stopPeriodicScreenshots();
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        this.connected = false;
    }
    
    handleMessage(data) {
        try {
            const message = JSON.parse(data);
            
            switch (message.type) {
                case 'vnc_data':
                    console.log('Received VNC data');
                    this.displayScreenshot(message.data);
                    break;
                case 'screenshot':
                    this.displayScreenshot(message.data);
                    // Update page info if available
                    if (message.url && window.app) {
                        window.app.urlInput.value = message.url;
                        if (message.loading) {
                            window.app.showLoadingProgress();
                        } else {
                            window.app.hideLoadingProgress();
                        }
                    }
                    break;
                case 'bookmarks_list':
                    if (window.app) {
                        window.app.populateBookmarks(message.bookmarks);
                        window.app.bookmarksModal.style.display = 'block';
                    }
                    break;
                case 'history_list':
                    if (window.app) {
                        window.app.populateHistory(message.history);
                    }
                    break;
                case 'tabs_updated':
                    if (window.app) {
                        window.app.updateTabsUI(message.tabs);
                        window.app.activeTabId = message.active_tab;
                    }
                    break;
                case 'success':
                    console.log('Command success:', message.message);
                    if (message.message.includes('Bookmark added') && window.app) {
                        window.app.updateBrowserStatus('Bookmark added successfully');
                    }
                    break;
                case 'info':
                    console.log('Info:', message.message);
                    if (window.app) {
                        window.app.updateBrowserStatus(message.message);
                    }
                    break;
                case 'error':
                    console.error('Server error:', message.message);
                    this.onError(message.message);
                    break;
                case 'command_result':
                    this.onCommandResult(message);
                    break;
                case 'status':
                    console.log('Status update:', message.message);
                    break;
            }
        } catch (error) {
            console.error('Error parsing message:', error);
        }
    }
    
    displayScreenshot(base64Data) {
        try {
            if (!base64Data) return;
            
            const img = new Image();
            img.onload = () => {
                // Clear canvas and draw image
                this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
                this.ctx.drawImage(img, 0, 0, this.canvas.width, this.canvas.height);
                console.log('Screenshot displayed successfully');
            };
            
            img.onerror = () => {
                console.error('Failed to load screenshot image');
                this.renderTestPattern();
            };
            
            // Set image source - handle both direct base64 and data URLs
            if (base64Data.startsWith('data:')) {
                img.src = base64Data;
            } else {
                img.src = `data:image/png;base64,${base64Data}`;
            }
            
        } catch (error) {
            console.error('Error displaying screenshot:', error);
            this.renderTestPattern();
        }
    }

    requestScreenCapture() {
        // Request a screen capture from the server
        if (this.connected && this.websocket.readyState === WebSocket.OPEN) {
            this.sendMessage({
                type: 'screen_request'
            });
        }
    }
    
    startPeriodicScreenshots() {
        // Request screenshots every 2 seconds to keep display updated
        if (this.screenshotInterval) {
            clearInterval(this.screenshotInterval);
        }
        
        this.screenshotInterval = setInterval(() => {
            if (this.connected) {
                this.requestScreenCapture();
            }
        }, 2000);
    }
    
    stopPeriodicScreenshots() {
        if (this.screenshotInterval) {
            clearInterval(this.screenshotInterval);
            this.screenshotInterval = null;
        }
    }
    
    sendMessage(message) {
        if (this.connected && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(message));
        }
    }
    
    sendMouseEvent(x, y, buttonMask) {
        // Convert canvas coordinates to VNC coordinates
        const rect = this.canvas.getBoundingClientRect();
        const scaleX = 1280 / rect.width;
        const scaleY = 720 / rect.height;
        
        const vncX = Math.floor(x * scaleX);
        const vncY = Math.floor(y * scaleY);
        
        // Create VNC mouse event (simplified)
        const mouseEvent = new Uint8Array(6);
        mouseEvent[0] = 5; // PointerEvent message type
        mouseEvent[1] = buttonMask;
        mouseEvent[2] = (vncX >> 8) & 0xFF;
        mouseEvent[3] = vncX & 0xFF;
        mouseEvent[4] = (vncY >> 8) & 0xFF;
        mouseEvent[5] = vncY & 0xFF;
        
        // Send as base64
        const base64Data = btoa(String.fromCharCode.apply(null, mouseEvent));
        this.sendMessage({
            type: 'vnc_input',
            data: base64Data
        });
    }
    
    sendKeyEvent(key, down) {
        // Create VNC key event (simplified)
        const keyEvent = new Uint8Array(8);
        keyEvent[0] = 4; // KeyEvent message type
        keyEvent[1] = down ? 1 : 0;
        keyEvent[2] = 0; // padding
        keyEvent[3] = 0; // padding
        
        // Convert key to keysym (simplified mapping)
        let keysym = key.charCodeAt(0);
        if (key.length === 1) {
            keysym = key.charCodeAt(0);
        } else {
            // Special keys mapping
            const specialKeys = {
                'Enter': 0xFF0D,
                'Backspace': 0xFF08,
                'Tab': 0xFF09,
                'Escape': 0xFF1B,
                'ArrowUp': 0xFF52,
                'ArrowDown': 0xFF54,
                'ArrowLeft': 0xFF51,
                'ArrowRight': 0xFF53
            };
            keysym = specialKeys[key] || 0;
        }
        
        keyEvent[4] = (keysym >> 24) & 0xFF;
        keyEvent[5] = (keysym >> 16) & 0xFF;
        keyEvent[6] = (keysym >> 8) & 0xFF;
        keyEvent[7] = keysym & 0xFF;
        
        // Send as base64
        const base64Data = btoa(String.fromCharCode.apply(null, keyEvent));
        this.sendMessage({
            type: 'vnc_input',
            data: base64Data
        });
    }
    
    setupEventListeners() {
        // Mouse events
        this.canvas.addEventListener('mousedown', (e) => {
            e.preventDefault();
            const rect = this.canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            this.mouseButtons |= (1 << e.button);
            this.sendMouseEvent(x, y, this.mouseButtons);
            this.lastMouseX = x;
            this.lastMouseY = y;
        });
        
        this.canvas.addEventListener('mouseup', (e) => {
            e.preventDefault();
            const rect = this.canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            this.mouseButtons &= ~(1 << e.button);
            this.sendMouseEvent(x, y, this.mouseButtons);
        });
        
        this.canvas.addEventListener('mousemove', (e) => {
            e.preventDefault();
            const rect = this.canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            this.sendMouseEvent(x, y, this.mouseButtons);
            this.lastMouseX = x;
            this.lastMouseY = y;
        });
        
        // Keyboard events
        this.canvas.addEventListener('keydown', (e) => {
            e.preventDefault();
            this.sendKeyEvent(e.key, true);
        });
        
        this.canvas.addEventListener('keyup', (e) => {
            e.preventDefault();
            this.sendKeyEvent(e.key, false);
        });
        
        // Make canvas focusable
        this.canvas.tabIndex = 0;
        
        // Focus canvas on click
        this.canvas.addEventListener('click', () => {
            this.canvas.focus();
        });
        
        // Context menu
        this.canvas.addEventListener('contextmenu', (e) => {
            e.preventDefault();
        });
    }
    
    // Event handlers (to be overridden)
    onConnectionChange(status) {
        console.log('Connection status:', status);
    }
    
    onError(message) {
        console.error('VNC error:', message);
    }
    
    onCommandResult(result) {
        console.log('Command result:', result);
    }
    
    // Render a test pattern when no VNC data is available
    renderTestPattern() {
        this.ctx.fillStyle = '#1a1a1a';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw grid
        this.ctx.strokeStyle = '#333';
        this.ctx.lineWidth = 1;
        
        for (let x = 0; x < this.canvas.width; x += 50) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, this.canvas.height);
            this.ctx.stroke();
        }
        
        for (let y = 0; y < this.canvas.height; y += 50) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(this.canvas.width, y);
            this.ctx.stroke();
        }
        
        // Draw text
        this.ctx.fillStyle = '#fff';
        this.ctx.font = '24px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.fillText('VNC Remote Desktop', this.canvas.width / 2, this.canvas.height / 2 - 20);
        
        this.ctx.font = '16px Arial';
        this.ctx.fillStyle = '#ccc';
        this.ctx.fillText('Loading browser...', this.canvas.width / 2, this.canvas.height / 2 + 20);
        
        // Request actual screenshot when connected
        setTimeout(() => {
            this.requestScreenCapture();
        }, 1000);
    }
}
