# Web-Based Chromium Browser with VNC Access

## Overview

This project provides a web-based remote desktop solution that allows users to access and control a Chromium browser through a web interface. The system uses VNC (Virtual Network Computing) to stream the desktop display and provides browser controls through a WebSocket connection. Users can navigate websites, interact with web content, and control the browser remotely through their web browser.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes (August 10, 2025)

### Migration to Replit Environment
- Successfully migrated project from Replit Agent to standard Replit environment
- Fixed websockets API compatibility issues with version 15.0.1
- Resolved port conflicts by removing duplicate server configurations
- Fixed VNC client base64 decoding errors in vnc_client.js
- Updated browser manager to use unique Chrome user data directories
- Cleaned up Chrome processes and temporary data directories
- All services now running successfully: Xvfb, VNC server, Chromium browser, HTTP server, WebSocket server

## Recent Changes (August 10, 2025)

### Migration to Replit Environment
- Successfully migrated project from Replit Agent to standard Replit environment
- Fixed websockets API compatibility issues with version 15.0.1
- Resolved port conflicts by removing duplicate server configurations
- Fixed VNC client base64 decoding errors in vnc_client.js
- Updated browser manager to use unique Chrome user data directories
- Cleaned up Chrome processes and temporary data directories
- All services now running successfully: Xvfb, VNC server, Chromium browser, HTTP server, WebSocket server

## System Architecture

### Frontend Architecture
The frontend is built with vanilla JavaScript and uses a canvas-based VNC client for remote desktop rendering. The interface includes:
- Browser navigation controls (back, forward, refresh, new tab)
- Address bar for URL input
- Real-time VNC display through HTML5 canvas
- WebSocket connection for bidirectional communication
- Responsive design with modern CSS styling using Font Awesome icons

### Backend Architecture
The backend follows a modular Python architecture with three main components:

**Main Server (`main.py`)**
- Orchestrates all services and handles WebSocket connections
- Manages client connections and message routing
- Coordinates VNC server and browser lifecycle

**VNC Server Management (`vnc_server.py`)**
- Manages Xvfb virtual display server for headless operation
- Handles VNC server process lifecycle
- Configures display resolution and rendering options

**Browser Management (`browser_manager.py`)**
- Controls Chromium browser using Selenium WebDriver
- Manages browser options and security settings
- Handles navigation and browser state

### Communication Protocol
- WebSocket-based real-time communication between frontend and backend
- JSON message format for browser commands and status updates
- Canvas-based VNC rendering for display streaming

### Display and Graphics
- Virtual X11 display using Xvfb for headless operation
- VNC protocol for remote desktop access
- Canvas-based rendering in the web browser
- Configurable screen resolution (default: 1280x720)

### Process Management
- Subprocess management for external services (Xvfb, VNC server)
- Process cleanup and resource management
- Error handling and service recovery

## External Dependencies

### Core Technologies
- **Python 3** - Backend runtime environment
- **Selenium WebDriver** - Browser automation and control
- **Chromium/Chrome** - Target browser for remote access
- **WebSockets** - Real-time bidirectional communication
- **Xvfb** - Virtual framebuffer X11 server for headless operation
- **VNC Server** - Remote desktop protocol implementation

### Python Libraries
- `selenium` - Browser automation
- `websockets` - WebSocket server implementation
- `psutil` - Process and system monitoring
- `asyncio` - Asynchronous programming support

### Frontend Dependencies
- **Font Awesome** - Icon library for UI elements
- **HTML5 Canvas** - VNC display rendering
- **WebSocket API** - Real-time communication

### System Requirements
- X11 display system support
- VNC server software
- Chrome/Chromium browser installation
- Linux-based operating system (typical for VNC/Xvfb support)

### Network Configuration
- WebSocket server on port 8000
- VNC server on port 5900 (standard VNC port)
- HTTP server for static file serving
- Chrome remote debugging on port 9222