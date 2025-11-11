# Quick Start Guide

## Start the WhatsApp-like Web App

1. **Run the server:**
```cmd
python app.py
```

2. **Open your browser:**
   - Go to `http://localhost:5000`

3. **Create two users for testing:**
   - **Browser 1 (Normal):** Register as "alice" with password "1234"
   - **Browser 2 (Incognito/Private):** Register as "bob" with password "1234"

4. **Test the features:**
   - Both users will see each other in the sidebar
   - Click on a user to start chatting
   - Type messages and press Enter or click Send
   - Click "📞 Voice Call" to start a voice call
   - Accept the call in the other browser
   - Click the red X button to end the call

## Features

### Text Chat
- Real-time messaging between users
- See who's online in the sidebar
- WhatsApp-like dark theme interface

### Voice Calls
- Click the voice call button to initiate
- Peer-to-peer WebRTC audio streaming
- Accept/reject incoming calls
- End call anytime

## Troubleshooting

**Microphone not working?**
- Allow microphone permission when browser asks
- Check browser settings for microphone access

**User not appearing in list?**
- Make sure both users are logged in
- Refresh the page

**Call not connecting?**
- Check firewall settings
- Ensure both browsers support WebRTC (Chrome, Firefox, Edge, Safari)

## Notes
- This uses WebRTC for direct peer-to-peer voice communication
- No audio is stored on the server
- Works best on local network or with proper STUN/TURN configuration for internet use
