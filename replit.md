# VNC Chromium Remote Desktop System

## Overview

This project provides a remote desktop solution using VNC to access a Chromium browser running on a virtual display. Users can access a full Chromium browser remotely through their web browser using the noVNC client.

## User Preferences

- Preferred communication style: Arabic language with simple, everyday language
- Interface preference: Arabic RTL interface design
- Technical level: Non-technical user friendly

## System Architecture

### Frontend Architecture
- **noVNC Web Client**: HTML5 VNC client for browser-based remote access
- **Arabic Web Interface**: Custom RTL Arabic HTML interface (vnc_arabic.html)
- **HTTP Server**: Python SimpleHTTPRequestHandler serving files on port 5000

### Backend Architecture
- **VNC Server**: x11vnc serving remote desktop on port 5900
- **Virtual Display**: Xvfb providing virtual X11 display :1 (1280x720x24)
- **Chromium Browser**: Running on virtual display with optimized headless settings
- **Process Management**: Python launcher with graceful cleanup and signal handling

### Core Components
1. **vnc_launcher.py**: Main system launcher with Arabic interface
2. **noVNC/**: Complete noVNC client library
3. **vnc_arabic.html**: Custom Arabic interface for VNC access

## Current Status (August 10, 2025)

### Working Services
- ✅ Xvfb virtual display on :1 (1280x720x24)
- ✅ x11vnc server on port 5900
- ✅ Chromium browser with Google.com loaded
- ✅ HTTP server on port 5000
- ✅ Arabic web interface with RTL support

### URLs
- **Main Interface**: http://localhost:5000/vnc_arabic.html
- **Direct noVNC**: http://localhost:5000/noVNC/vnc_lite.html?host=localhost&port=5900
- **External Access**: https://repl-url.replit.dev/vnc_arabic.html

## External Dependencies

### System Dependencies
- Chromium browser (/nix/store path)
- x11vnc (VNC server)
- Xvfb (Virtual X11 display)

### Python Dependencies
- websockets (for WebSocket proxy)
- Standard library: subprocess, threading, http.server

### Third-Party Services
- noVNC: HTML5 VNC client library
- None required for basic operation

## Architecture Decisions

### Why This Approach
- **Portability**: Works on any browser without client installation
- **Security**: VNC only listens on localhost
- **Simplicity**: Single Python script manages all services
- **User Experience**: Arabic interface for better accessibility

### Performance Optimizations
- Virtual display optimized for web browsing
- Chromium configured with minimal resource usage
- Background process cleanup on exit

---

*Last updated: August 10, 2025 - System fully operational*