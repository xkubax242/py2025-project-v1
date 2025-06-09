import socket
import threading
import json
from network.config import load_config

class NetworkServer:
    def __init__(self, port: int = None):
        config = load_config()
        self.port = port or config.get("port", 5000)
        self.host = config.get("host", "0.0.0.0")



    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.bind((self.host, self.port))
            server_sock.listen()
            print(f"[SERWER] Nasłuchiwanie na {self.host}:{self.port}")



            while True:
                client_socket, addr = server_sock.accept()
                print(f"[SERWER] Połączenie od klienta: {addr}")
                threading.Thread(target=self._handle_client, args=(client_socket,), daemon=True).start()



    def _handle_client(self, client_socket):
        with client_socket:
            try:
                data_chunks = []
                while True:
                    chunk = client_socket.recv(1024)
                    if not chunk:
                        break
                    data_chunks.append(chunk)
                    if b"\n" in chunk:
                        break
                data = b"".join(data_chunks)
                decoded = data.decode("utf-8").strip()
                payload = json.loads(decoded)
                print("[SERWER] Odebrano dane:")
                for k, v in payload.items():
                    print(f"  {k}: {v}")
                client_socket.sendall(b"ACK\n")
            except json.JSONDecodeError as e:
                print(f"[SERWER] Błąd dekodowania JSON: {e}")
            except Exception as e:
                print(f"[SERWER] Błąd podczas obsługi klienta: {e}")
