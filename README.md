# Real-Time Communication System 2.0

A WhatsApp-like web application with real-time messaging and WebRTC voice calling.

## Features
- 🔐 User authentication (register/login)
- 💬 Real-time text messaging
- 📞 WebRTC voice calling
- 👥 Online user list
- 🎨 WhatsApp-inspired dark theme UI

## Setup Instructions

### 1. Install Python Dependencies
```cmd
pip install -r requirements.txt
```

### 2. Run the Application
```cmd
python app.py
```

The server will start on `http://127.0.0.1:5000`

### 3. Usage
1. Open your browser and go to `http://localhost:5000`
2. Register a new account
3. Login with your credentials
4. You'll see a WhatsApp-like interface
5. Open another browser window (or incognito) and register another user
6. Both users will appear in each other's online user list
7. Click on a user to start chatting
8. Click the "📞 Voice Call" button to initiate a voice call

## How It Works

### Text Messaging
- Uses Flask-SocketIO for real-time bidirectional communication
- Messages are sent directly between connected clients
- Online status is tracked in real-time

### Voice Calling
- Uses WebRTC for peer-to-peer voice communication
- Signaling is handled through Flask-SocketIO
- STUN server (Google's public STUN) for NAT traversal
- Direct audio streaming between browsers

## Browser Requirements
- Chrome, Firefox, Edge, or Safari (latest versions)
- Microphone access permission required for voice calls

## Legacy Socket Applications
The `socket_app/` directory contains the original TCP socket-based chat and voice servers. These are separate from the web application.

# Real-Time-Communication-System-2.0