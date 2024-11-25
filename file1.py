import os
import socket
import threading
import struct
from math import ceil

# Constants
SERVER_PORT = 45000
MAXDATASIZE = 100
BACKLOG = 10
CHUNK_SIZE = 512 * 1024

EXIT = 1
REGISTER = 2
LOG_IN = 3
LOG_OUT = 4
CREATE_GROUP = 5
LIST_GROUP = 6
JOIN_GROUP = 7
LIST_GROUP_JOIN_REQ = 8
REPLY_JOIN_REQ = 9
UPLOAD_FILE = 10
LIST_FILE = 11
DOWNLOAD_FILE = 12
SHOW_DOWNLOAD = 13
LEAVE_GROUP = 14

DO_NOTHING = 9999
SHOW_ALL_INFO = 9998
SEND_MSG_TO_PEER = 9997


# Class Definitions
class FileInfo:
    def __init__(self, id, name, size):
        self.id = id
        self.name = name
        self.size = size
        self.bitmap_len = size // (512 * 1024)
        self.bitmap = [True] * self.bitmap_len


class GlobalInfo:
    def __init__(self):
        self.login_status = False
        self.curr_log_in_id = None
        self.user_name = ""
        self.sockfd = None
        self.files = {}
        self.curr_path = ""

    def add_file(self, file_id, file):
        self.files[file_id] = file


class UserInfo:
    def __init__(self, id):
        self.id = id
        self.login_status = False
        self.groups = []

    def add_group(self, grp_id):
        self.groups.append(grp_id)


# Global Objects
global_info = GlobalInfo()
local_users = {}


# Helper Functions
def get_new_file(id, name, size):
    return FileInfo(id, name, size)


def send_msg(sock, message):
    """Send a message to a socket, with a length header."""
    message = struct.pack("I", len(message)) + message.encode()
    sock.sendall(message)


def recv_msg(sock):
    """Receive a message from a socket."""
    try:
        header = sock.recv(4)
        if not header:
            return None
        msg_length = struct.unpack("I", header)[0]
        message = sock.recv(msg_length).decode()
        return message
    except Exception as e:
        print(f"Error receiving message: {e}")
        return None


def init_socket(ip, port):
    """Initialize a socket connection."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, int(port)))
        print(f"Connected to server at {ip}:{port}")
        return sock
    except socket.error as e:
        print(f"Socket error: {e}")
        return None


def server_thread_func():
    """Server thread handling peer-to-peer connections."""
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((global_info.curr_path, SERVER_PORT))
    server_sock.listen(BACKLOG)
    print(f"Server listening on port {SERVER_PORT}")

    while True:
        client_sock, addr = server_sock.accept()
        print(f"Accepted connection from {addr}")
        threading.Thread(target=peer_client_handler, args=(client_sock,)).start()


def peer_client_handler(client_sock):
    """Handle a peer client connection."""
    while True:
        recv_data = recv_msg(client_sock)
        if recv_data is None:
            break
        print(f"Received: {recv_data}")
        # Simulate a response
        send_msg(client_sock, f"Echo: {recv_data}")
    client_sock.close()


# Main Functionality
def main():
    tracker_ip = "127.0.0.1"
    tracker_port = "45000"
    sock = init_socket(tracker_ip, tracker_port)

    if not sock:
        return

    threading.Thread(target=server_thread_func, daemon=True).start()

    while True:
        user_input = input("Enter command: ")
        if user_input.lower() == "exit":
            send_msg(sock, "EXIT")
            break

        send_msg(sock, user_input)
        response = recv_msg(sock)
        if response:
            print(f"Server response: {response}")

    sock.close()


if __name__ == "__main__":
    main()
