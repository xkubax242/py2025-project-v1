import socket
import json
import time
from typing import Optional
from network.config import load_config

class NetworkClient:
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None,
                 timeout: Optional[float] = None, retries: Optional[int] = None, logger=None):
        config = load_config()
        self.host = host or config["host"]
        self.port = port or config["port"]
        self.timeout = timeout or config.get("timeout", 5.0)
        self.retries = retries or config.get("retries", 3)
        self.logger = logger
        self.sock = None

    def connect(self):
        try:
            self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
            if self.logger:
                self.logger.log_reading("network", time.time(), 0, "Połączono z serwerem")
        except Exception as e:
            if self.logger:
                self.logger.log_reading("network", time.time(), 0, f"Błąd połączenia: {e}")
            raise

    def send(self, data: dict) -> bool:
        payload = self._serialize(data)

        for attempt in range(self.retries):
            try:
                self.sock.sendall(payload + b"\n")
                ack = self.sock.recv(1024).strip()
                if ack == b"ACK":
                    if self.logger:
                        self.logger.log_reading("network", time.time(), 0, "Potwierdzenie ACK otrzymane")
                    return True
            except Exception as e:
                if self.logger:
                    self.logger.log_reading("network", time.time(), 0, f"Błąd wysyłania: {e}")
                self.connect()

        if self.logger:
            self.logger.log_reading("network", time.time(), 0, "Nie udało się wysłać danych po kilku próbach")
        return False

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None
            if self.logger:
                self.logger.log_reading("network", time.time(), 0, "Zamknięto połączenie z serwerem")

    def _serialize(self, data: dict) -> bytes:
        return json.dumps(data).encode("utf-8")

    def _deserialize(self, raw: bytes) -> dict:
        return json.loads(raw.decode("utf-8"))
