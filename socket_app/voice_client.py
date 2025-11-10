import socket
import ssl
import threading
import pyaudio

# ==========================
# CONFIGURATION
# ==========================
SERVER_IP = "localhost"   # Change to your server’s IP
SERVER_PORT = 50007

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

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
    """Record microphone audio and send it to the server."""
    while True:
        try:
            data = stream_in.read(CHUNK, exception_on_overflow=False)
            with send_lock:
                wrapped.sendall(data)
        except Exception as e:
            print("[Send error]:", e)
            break


def receive_audio():
    """Receive audio and control messages from the server."""
    while True:
        try:
            data = wrapped.recv(4096)
            if not data:
                break
            # Control messages
            if data.startswith(b"["):
                print(data.decode())
            else:
                stream_out.write(data)
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
