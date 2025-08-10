# Overview

Firefox VNC Remote Desktop System using noVNC. This project provides remote desktop access to a Firefox browser running on a virtual display through noVNC client. The system integrates Firefox browser with VNC server and noVNC web client for complete remote browsing capabilities.

# User Preferences

- Preferred communication style: Simple, everyday language (Arabic)
- Project organization: Keep project clean and organized without adding unnecessary files
- Browser preference: Firefox with full noVNC features and capabilities

# System Architecture

## Frontend Architecture
- **Pure HTML5/JavaScript Implementation**: Built using modern ES6 modules with no external framework dependencies
- **Canvas-Based Rendering**: Uses HTML5 Canvas API for efficient 2D graphics rendering and display management
- **Modular Design**: Core functionality separated into independent modules (Display, Keyboard, WebSocket, etc.)
- **Mobile-First Approach**: Responsive design with touch gesture support for mobile devices

## Core Library Structure
- **RFB Module**: Main client implementation handling VNC protocol communication
- **Display Module**: Canvas-based rendering system with viewport management and scaling
- **Input Handling**: Separate modules for keyboard and gesture input with cross-platform compatibility
- **WebSocket Layer**: Custom WebSocket wrapper with buffering and binary data support
- **Encoding Decoders**: Pluggable architecture supporting multiple VNC encodings (Raw, Hextile, Tight, ZRLE, etc.)

## Protocol Implementation
- **VNC Protocol Support**: Full RFB (Remote Framebuffer) protocol implementation
- **Multiple Authentication Methods**: VNC authentication, RSA-AES authentication, and legacy crypto support
- **Compression Support**: Built-in deflate/inflate for bandwidth optimization using Pako library
- **Modern Encoding Support**: H.264 video codec support through WebCodecs API

## Internationalization
- **Localization System**: JSON-based translation files with runtime language detection
- **Multi-language Support**: Support for 15+ languages with automatic browser language detection
- **Dynamic Loading**: Translations loaded asynchronously based on user preferences

## Build System
- **ES6 to ES5 Conversion**: Babel-based transpilation for older browser compatibility
- **Module Bundling**: Custom build system for creating standalone library versions
- **Testing Framework**: Karma + Mocha test suite with browser automation

# External Dependencies

## Core Libraries
- **Pako**: Zlib compression/decompression library for encoding support
- **WebCodecs API**: Browser-native H.264 video decoding (when available)

## Development Dependencies
- **Babel**: ES6 to ES5 transpilation with preset-env configuration
- **Karma**: Test runner with browser automation support
- **Mocha/Chai/Sinon**: Testing framework with assertions and mocking capabilities
- **ESLint**: Code linting and style enforcement
- **Commander.js**: CLI argument parsing for build tools

## Browser APIs
- **WebSocket**: Primary communication transport layer
- **RTCDataChannel**: Alternative transport for WebRTC scenarios
- **Canvas 2D**: Graphics rendering and image manipulation
- **Clipboard API**: Copy/paste functionality integration
- **Fullscreen API**: Full-screen mode support
- **Pointer Events**: Modern pointer input handling

## Build Tools
- **Node.js**: Build system runtime environment
- **fs-extra**: Enhanced file system operations for build scripts
- **JSDOM**: Server-side DOM implementation for testing