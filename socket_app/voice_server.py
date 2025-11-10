import socket
import ssl
import threading
import sqlite3
import pyaudio  # <-- audio support

# ==========================
# CONFIGURATION
# ==========================
HOST = "0.0.0.0"
PORT = 50007
DB_PATH = "../instance/db.sqlite"

clients = {}         # username -> connection
rooms = {}           # room_name -> {usernames}
user_rooms = {}      # username -> room_name
lock = threading.Lock()

# ==========================
# SSL CONTEXT
# ==========================
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile="server.crt", keyfile="server.key")


# ==========================
# DATABASE AUTHENTICATION
# ==========================
def authenticate_user(username):
    """Check if username exists in SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


# ==========================
# ROOM BROADCAST FUNCTION
# ==========================
def broadcast_in_room(sender, data):
    """Send audio data to all users in the same room except the sender"""
    room = user_rooms.get(sender)
    if not room:
        return

    with lock:
        for user in rooms.get(room, []):
            if user != sender and user in clients:
                try:
                    clients[user].sendall(data)
                except:
                    pass


# ==========================
# CLIENT HANDLER
# ==========================
def handle_client(conn, addr):
    try:
        username = conn.recv(1024).decode().strip()
        print(f"[AUTH] {addr} is trying to connect as '{username}'")

        if not authenticate_user(username):
            conn.sendall(b"[AUTH ERROR] Invalid username.")
            conn.close()
            print(f"[DENIED] {addr} — invalid username")
            return

        with lock:
            clients[username] = conn
        print(f"[CONNECTED] {username} ({addr})")

        conn.sendall(b"[AUTH OK] Connected to voice server.\nUse /call <user> or /join <room>.")

        while True:
            data = conn.recv(4096)
            if not data:
                break

            if data.startswith(b"/"):  # command mode
                cmd_str = data.decode(errors='ignore').strip()
                cmd = cmd_str.split(" ", 2)

                if cmd[0] == "/call" and len(cmd) == 2:
                    target = cmd[1]
                    if target in clients and target != username:
                        room = f"private_{username}_{target}"
                        with lock:
                            rooms[room] = {username, target}
                            user_rooms[username] = room
                            user_rooms[target] = room
                        clients[target].sendall(f"[CALL REQUEST] {username} started a call.".encode())
                        conn.sendall(f"[CALL STARTED] with {target}".encode())
                    else:
                        conn.sendall(b"[ERROR] User not found or invalid.")

                elif cmd[0] == "/join" and len(cmd) == 2:
                    room = cmd[1]
                    with lock:
                        rooms.setdefault(room, set()).add(username)
                        user_rooms[username] = room
                    conn.sendall(f"[JOINED ROOM] {room}".encode())

                elif cmd[0] == "/leave":
                    with lock:
                        room = user_rooms.pop(username, None)
                        if room and room in rooms:
                            rooms[room].discard(username)
                            if not rooms[room]:
                                del rooms[room]
                    conn.sendall(b"[LEFT CALL]")

                else:
                    conn.sendall(b"[ERROR] Unknown command.")

            else:
                # Audio data (PyAudio stream)
                broadcast_in_room(username, data)

    except Exception as e:
        print(f"[!] Error with {addr}: {e}")

    finally:
        print(f"[-] {username} disconnected.")
        with lock:
            clients.pop(username, None)
            room = user_rooms.pop(username, None)
            if room and room in rooms:
                rooms[room].discard(username)
                if not rooms[room]:
                    del rooms[room]
        conn.close()


# ==========================
# SERVER MAIN LOOP
# ==========================
def main():
    bindsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bindsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    bindsock.bind((HOST, PORT))
    bindsock.listen(5)

    print(f"[SERVER] Listening securely on {HOST}:{PORT}")

    while True:
        raw_conn, addr = bindsock.accept()
        try:
            conn = context.wrap_socket(raw_conn, server_side=True)
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
        except ssl.SSLError as e:
            print(f"[SSL ERROR] {addr}: {e}")
            raw_conn.close()


if __name__ == "__main__":
    main()
