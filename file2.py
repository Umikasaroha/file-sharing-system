import socket
import threading
import struct
from collections import defaultdict

# Constants
PORT = 45000
BACKLOG = 10
ESC = '\x1b'

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
LEAVE_GROUP = 14


class PeerInfo:
    def __init__(self, peer_id, username, password, ip, port):
        self.peer_id = peer_id
        self.login_status = False
        self.username = username
        self.password = password
        self.ip = ip
        self.port = port
        self.files = []
        self.own_groups = []
        self.other_groups = []

    def add_file(self, file_id):
        self.files.append(file_id)

    def add_own_group(self, group_id):
        self.own_groups.append(group_id)

    def add_other_group(self, group_id):
        self.other_groups.append(group_id)


class GroupInfo:
    def __init__(self, group_id, leader_id):
        self.group_id = group_id
        self.leader_id = leader_id
        self.members = []
        self.pending_requests = []

    def add_member(self, peer_id):
        self.members.append(peer_id)

    def add_request(self, peer_id):
        self.pending_requests.append(peer_id)


class FileInfo:
    def __init__(self, file_id, filename, size):
        self.file_id = file_id
        self.filename = filename
        self.size = size
        self.peers = []

    def add_peer(self, peer_id):
        self.peers.append(peer_id)


class TrackerDatabase:
    def __init__(self):
        self.next_peer_id = 1
        self.next_file_id = 1
        self.next_group_id = 1

        self.peers = {}  # peer_id -> PeerInfo
        self.groups = {}  # group_id -> GroupInfo
        self.files = {}  # file_id -> FileInfo
        self.file_name_to_id = {}  # filename -> file_id
        self.ip_port_to_peers = defaultdict(list)

    def register_peer(self, username, password, ip, port):
        peer_id = self.next_peer_id
        self.next_peer_id += 1
        peer = PeerInfo(peer_id, username, password, ip, port)
        self.peers[peer_id] = peer
        self.ip_port_to_peers[(ip, port)].append(peer_id)
        return peer_id

    def login_peer(self, peer_id, password):
        peer = self.peers.get(peer_id)
        if peer and peer.password == password:
            peer.login_status = True
            return True
        return False

    def logout_peer(self, peer_id):
        peer = self.peers.get(peer_id)
        if peer:
            peer.login_status = False
            return True
        return False

    def create_group(self, leader_id):
        group_id = self.next_group_id
        self.next_group_id += 1
        group = GroupInfo(group_id, leader_id)
        self.groups[group_id] = group
        return group_id


def recv_message(sock):
    try:
        header = sock.recv(4)
        if not header:
            return None
        length = struct.unpack("I", header)[0]
        message = sock.recv(length).decode()
        return message
    except Exception as e:
        print(f"Error receiving message: {e}")
        return None


def send_message(sock, message):
    try:
        encoded_message = message.encode()
        header = struct.pack("I", len(encoded_message))
        sock.sendall(header + encoded_message)
    except Exception as e:
        print(f"Error sending message: {e}")


def handle_client(sock, addr, database):
    print(f"Connection established with {addr}")
    while True:
        message = recv_message(sock)
        if not message:
            break

        response = f"Echo: {message}"  # Replace with actual logic.
        send_message(sock, response)
    sock.close()
    print(f"Connection with {addr} closed.")


def tracker_server(host, port, database):
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((host, port))
    server_sock.listen(BACKLOG)
    print(f"Tracker server listening on {host}:{port}")

    while True:
        client_sock, addr = server_sock.accept()
        threading.Thread(target=handle_client, args=(client_sock, addr, database)).start()


if __name__ == "__main__":
    db = TrackerDatabase()
    tracker_server("0.0.0.0", PORT, db)
