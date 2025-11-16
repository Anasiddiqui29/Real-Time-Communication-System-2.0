import socket
import ssl
import threading
import pyaudio
import sys
sys.path.append('..')
from encryption import AESCipher

# ==========================
# CONFIGURATION
# ==========================
SERVER_IP = "localhost"   # Change to your server's IP
SERVER_PORT = 50007

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# ==========================
# AES ENCRYPTION
# ==========================
cipher = AESCipher("RealTimeCommunicationSystem2024SecureKey")

# ==========================
# AUDIO STREAMS
# ==========================
audio = pyaudio.PyAudio()
stream_in = audio.open(format=FORMAT, channels=CHANNELS,
                       rate=RATE, input=True, frames_per_buffer=CHUNK)
stream_out = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, output=True, frames_per_buffer=CHUNK)

# ==========================
# SOCKET + SSL SETUP
# ==========================
raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
raw_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE  # For testing only — disable in production

wrapped = context.wrap_socket(raw_sock, server_hostname="localhost")
wrapped.connect((SERVER_IP, SERVER_PORT))

# ==========================
# AUTHENTICATION
# ==========================
username = input("Enter your username: ").strip()
wrapped.sendall(username.encode())
print("[+] Connected securely to voice server.")
print("Waiting for authentication response...\n")

auth_response = wrapped.recv(1024).decode()
print(auth_response)
if "[AUTH ERROR]" in auth_response:
    print("[x] Authentication failed. Closing connection.")
    wrapped.close()
    exit()

# ==========================
# THREADS
# ==========================
send_lock = threading.Lock()

def send_audio():
    """Record microphone audio, encrypt it, and send to the server."""
    while True:
        try:
            data = stream_in.read(CHUNK, exception_on_overflow=False)
            # Encrypt audio data
            encrypted_data = cipher.encrypt_bytes(data)
            # Send length prefix + encrypted data
            packet = len(encrypted_data).to_bytes(4, 'big') + encrypted_data
            with send_lock:
                wrapped.sendall(packet)
        except Exception as e:
            print("[Send error]:", e)
            break


def receive_audio():
    """Receive encrypted audio and control messages from the server."""
    buffer = b""
    while True:
        try:
            data = wrapped.recv(4096)
            if not data:
                break
            
            # Control messages
            if data.startswith(b"["):
                print(data.decode())
            else:
                # Encrypted audio data with length prefix
                buffer += data
                
                # Process complete packets
                while len(buffer) >= 4:
                    packet_len = int.from_bytes(buffer[:4], 'big')
                    if len(buffer) >= 4 + packet_len:
                        encrypted_audio = buffer[4:4+packet_len]
                        buffer = buffer[4+packet_len:]
                        
                        try:
                            # Decrypt audio
                            decrypted_audio = cipher.decrypt_bytes(encrypted_audio)
                            stream_out.write(decrypted_audio)
                        except Exception as e:
                            print(f"[Decryption error]: {e}")
                    else:
                        break
        except Exception as e:
            print("[Receive error]:", e)
            break


def command_input():
    """Send chat/command messages to the server (/call, /join, /leave)."""
    while True:
        try:
            cmd = input()
            if cmd:
                with send_lock:
                    wrapped.sendall(cmd.encode())
        except Exception as e:
            print("[Command error]:", e)
            break


# ==========================
# THREAD LAUNCH
# ==========================
threading.Thread(target=send_audio, daemon=True).start()
threading.Thread(target=receive_audio, daemon=True).start()
threading.Thread(target=command_input, daemon=True).start()

print("Available Commands:")
print("  /call <username>  - start a private call")
print("  /join <roomname>  - join a group call")
print("  /leave            - leave the current call\n")

# ==========================
# KEEP ALIVE
# ==========================
try:
    while True:
        pass
except KeyboardInterrupt:
    print("\n[QUIT]")
finally:
    wrapped.close()
    stream_in.stop_stream(); stream_in.close()
    stream_out.stop_stream(); stream_out.close()
    audio.terminate()
