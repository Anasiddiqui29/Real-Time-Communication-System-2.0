#---Server---
import socket
import ssl
import threading
import os

# --- User Database ---
users = {
    "anas": "1234",
    "abdullah": "1234",
    "ali":"1234",
    "hasan": "1234"
}

# --- Active Clients ---
clients = {}  # username -> (conn, addr)

# --- Handle Each Client ---
def handle_client(secure_client, addr):
    print(f"[NEW CONNECTION] {addr}")
    username = None

    try:
        secure_client.send("Enter username: ".encode())
        username = secure_client.recv(1024).decode().strip()
        secure_client.send("Enter password: ".encode())
        password = secure_client.recv(1024).decode().strip()

        # Authentication
        if username not in users or users[username] != password:
            secure_client.send("Invalid credentials. Disconnecting...".encode())
            secure_client.close()
            return

        # Successful login
        secure_client.send(f"Login successful!\nWelcome, {username}!\n".encode())
        clients[username] = (secure_client, addr)
        print(f"[LOGIN] {username} from {addr}")

        # Broadcast join
        broadcast(f"📢 {username} joined the chat!", username)

        while True:
            data = secure_client.recv(1024).decode()
            if not data:
                break

            if data.lower() == "/list":
                online = "\n".join([f"- {u}" for u in clients.keys()])
                secure_client.send(f"Online Users:\n{online}".encode())

            elif data.startswith("/sendfile"):
                parts = data.split(" ", 2)
                if len(parts) < 3:
                    secure_client.send("Usage: /sendfile <username> <filename>".encode())
                    continue

                target_user, filename = parts[1], parts[2]
                if target_user not in clients:
                    secure_client.send("User not online.".encode())
                    continue

                if not os.path.exists(filename):
                    secure_client.send("File not found.".encode())
                    continue

                target_conn, _ = clients[target_user]
                target_conn.send(f"__FILE_START__ {os.path.basename(filename)}".encode())

                with open(filename, "rb") as f:
                    while chunk := f.read(1024):
                        target_conn.send(chunk)

                target_conn.send(b"__EOF__")
                secure_client.send(f"File '{filename}' sent to {target_user}".encode())

            elif data.lower() == "/exit":
                break

            # else:
                # broadcast(f"[{username}] {data}", username)

            elif data.startswith("/msg"):
                parts = data.split(" " , 2)
                if len(parts) < 3:
                    secure_client.send("Usage: /msg <username> <message>".encode())
                    continue 
                    
                target_user , message = parts[1] , parts[2]
                if target_user not in clients:
                    secure_client.send(f"User '{target_user}' not online.".encode())
                    continue

                target_conn , _ = clients[target_user]
                try:
                    target_conn.send(f"[Private from {username}] {message}".encode())
                    secure_client.send(f"[Private to {target_user}] {message}".encode())
                except:
                    secure_client.send("Failed to send message".encode())   

            else:
                broadcast(f"[{username}] {data}", username)             

    except Exception as e:
        print(f"[ERROR] {addr}: {e}")

    finally:
        if username and username in clients:
            del clients[username]
            broadcast(f"🚪 {username} left the chat.", username)
        secure_client.close()
        print(f"[DISCONNECTED] {addr}")

# --- Broadcast Message to All ---
def broadcast(message, sender_username):
    for user, (conn, _) in clients.items():
        if user != sender_username:
            try:
                conn.send(message.encode())
            except:
                pass

# --- Main Server Function ---
def start_server():
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 12346))
    server.listen(5)
    print("[SERVER STARTED] Secure Chatroom Active...")

    while True:
        client_socket, addr = server.accept()
        secure_client = context.wrap_socket(client_socket, server_side=True)
        threading.Thread(target=handle_client, args=(secure_client, addr)).start()

# --- Entry Point ---
if __name__ == "__main__":
    start_server()
