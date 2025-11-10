# --- Client ---
import socket
import ssl
import threading
import os

# --- Receive Messages ---
def receive_messages(secure_socket):
    file_data = b""
    file_receiving = False
    filename = ""

    while True:
        try:
            data = secure_socket.recv(1024)
            if not data:
                print("Disconnected from server.")
                break

            # Detect start of file transfer
            if data.startswith(b"__FILE_START__"):
                parts = data.decode(errors="ignore").split(" ", 1)
                if len(parts) > 1:
                    filename = parts[1].strip()
                else:
                    filename = "unknown.txt"
                file_data = b""
                file_receiving = True
                print(f"[Receiving file: {filename}]")
                continue

            # Detect end of file transfer
            if data.startswith(b"__EOF__"):
                if filename:
                    save_path = f"received_{os.path.basename(filename)}"
                    with open(save_path, "wb") as f:
                        f.write(file_data)
                    print(f"[File saved successfully as '{save_path}']")
                else:
                    print("[Error: filename missing, file not saved]")
                file_receiving = False
                filename = ""
                file_data = b""
                continue

            # If receiving file data
            if file_receiving:
                file_data += data
            else:
                print(data.decode(errors="ignore"))

        except Exception as e:
            print("Connection lost:", e)
            break


# --- Send Messages ---
def send_messages(secure_socket):
    while True:
        msg = input()
        if msg.lower() == "/exit":
            secure_socket.send(msg.encode())
            secure_socket.close()
            break

        elif msg.startswith("/sendfile"):
            # parts = msg.split(" ", 2)
            # if len(parts) < 3:
            #     print("Usage: /sendfile <username> <filename>")
            #     continue

            # target_user, filename = parts[1], parts[2]
            # if not os.path.exists(filename):
            #     print("File not found.")
            #     continue

            # # --- Notify server about file start ---
            # secure_socket.send(f"/sendfile {target_user} {filename}".encode())

            # with open(filename, "rb") as f:
            #     secure_socket.send(b"__FILE_START__ " + os.path.basename(filename).encode())
            #     while True:
            #         chunk = f.read(1024)
            #         if not chunk:
            #             break
            #         secure_socket.send(chunk)
            #     secure_socket.send(b"__EOF__")
            parts = msg.split(" ", 2)
            if len(parts) < 3:
                print("Usage: /sendfile <username> <filename>")
                continue

            target_user, filename = parts[1], parts[2]
            if not os.path.exists(filename):
                print("File not found.")
                continue

            # Just tell server to send the file
            secure_socket.send(f"/sendfile {target_user} {filename}".encode())

            # print(f"[File '{filename}' sent to {target_user}]")

        else:
            secure_socket.send(msg.encode())

# --- Main Client ---
def start_client():
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE  # Accept self-signed certs

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    secure_client = context.wrap_socket(client, server_hostname="localhost")

    secure_client.connect(('localhost', 12346))
    print("[CONNECTED TO SERVER]")

    # --- Login ---
    print(secure_client.recv(1024).decode(), end="")
    username = input()
    secure_client.send(username.encode())

    print(secure_client.recv(1024).decode(), end="")
    password = input()
    secure_client.send(password.encode())

    print(secure_client.recv(1024).decode())

    # --- Threads ---
    threading.Thread(target=receive_messages, args=(secure_client,), daemon=True).start()
    send_messages(secure_client)

# --- Entry Point ---
if __name__ == "__main__":
    start_client()
