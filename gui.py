import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import socket
import json
from datetime import datetime, timedelta
from collections import defaultdict, deque
from network.config import load_config
from sensors.temperature_sensor import TemperatureSensor
from sensors.humidity_sensor import HumiditySensor
from sensors.pressure_sensor import PressureSensor
from sensors.light_sensor import LightSensor
from logger import Logger


class GUIApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("Serwer TCP - Panel Sterowania")

        self.config = load_config()
        self.port_var = tk.StringVar(value=str(self.config.get("port", 5000)))

        self.server_thread = None
        self.server_running = False
        self.sensor_loop_running = False
        self.sensor_thread = None
        self.sensor_data = {}
        self.sensor_history = defaultdict(deque)
        self.lock = threading.Lock()


        self.logger = Logger("config.json")
        self.logger.start()


        self._build_ui()


        self.sensors = [
            TemperatureSensor('temp_01', frequency=1),
            HumiditySensor('hum_01', frequency=1),
            PressureSensor('press_01', frequency=1),
            LightSensor('light_01', frequency=1),
        ]


        self._start_updating_gui()

    def _build_ui(self):

        top_frame = ttk.Frame(self.root)
        top_frame.pack(pady=10, padx=10, fill="x")

        ttk.Label(top_frame, text="Port TCP:").pack(side="left")
        self.port_entry = ttk.Entry(top_frame, textvariable=self.port_var, width=10)
        self.port_entry.pack(side="left", padx=5)

        self.start_button = ttk.Button(top_frame, text="Start", command=self.start_server)
        self.start_button.pack(side="left", padx=5)

        self.stop_button = ttk.Button(top_frame, text="Stop", command=self.stop_server, state="disabled")
        self.stop_button.pack(side="left", padx=5)


        columns = ("sensor", "value", "unit", "timestamp", "avg_1h", "avg_12h")
        headers = {
            "sensor": "Czujnik",
            "value": "Wartość",
            "unit": "Jednostka",
            "timestamp": "Czas pomiaru",
            "avg_1h": "Śr. z 1h",
            "avg_12h": "Śr. z 12h"
        }
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, anchor="center", width=120)
        self.tree.pack(padx=10, pady=10, fill="both", expand=True)


        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        self.status_label.pack(fill="x", padx=10, pady=(0, 5))
        self._update_status("Serwer zatrzymany.")

    def _update_status(self, message):
        self.status_var.set(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def start_server(self):
        try:
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("Błąd", "Nieprawidłowy numer portu.")
            return

        self.server_running = True
        self.server_thread = threading.Thread(target=self._run_server, args=(port,), daemon=True)
        self.server_thread.start()

        self.sensor_loop_running = True
        self.sensor_thread = threading.Thread(target=self._sensor_loop, daemon=True)
        self.sensor_thread.start()

        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self._update_status(f"Serwer i czujniki uruchomione na porcie {port}.")

    def stop_server(self):
        self.server_running = False
        self.sensor_loop_running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self._update_status("Serwer i czujniki zatrzymane.")

    def _run_server(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                s.listen()
                while self.server_running:
                    s.settimeout(1.0)
                    try:
                        client_socket, addr = s.accept()
                        threading.Thread(target=self._handle_client, args=(client_socket,), daemon=True).start()
                    except socket.timeout:
                        continue
            except Exception as e:
                self._update_status(f"Błąd serwera: {e}")
                messagebox.showerror("Błąd", f"Błąd serwera: {e}")
                self.stop_server()



    def _handle_client(self, client_socket):
        with client_socket:
            try:
                data = client_socket.recv(4096)
                decoded = data.decode("utf-8").strip()
                payload = json.loads(decoded)

                sensor_id = payload["sensor"]
                value = payload["value"]
                unit = payload["unit"]
                timestamp = datetime.fromisoformat(payload["timestamp"])

                with self.lock:
                    self.sensor_data[sensor_id] = (value, unit, timestamp)
                    self.sensor_history[sensor_id].append((timestamp, value))
                    self.logger.log_reading(sensor_id, timestamp, value, unit)

            except Exception as e:
                print(f"Błąd klienta: {e}")

    def _sensor_loop(self):
        while self.sensor_loop_running:
            now = datetime.now()
            for sensor in self.sensors:
                if sensor.active:
                    value = sensor.read_value()
                    with self.lock:
                        self.sensor_data[sensor.sensor_id] = (value, sensor.unit, now)
                        self.sensor_history[sensor.sensor_id].append((now, value))
                        self.logger.log_reading(sensor.sensor_id, now, value, sensor.unit)
            time.sleep(2)



    def _start_updating_gui(self):
        def update():
            with self.lock:
                self.tree.delete(*self.tree.get_children())
                for sensor_id, (value, unit, timestamp) in self.sensor_data.items():
                    avg_1h = self._compute_average(sensor_id, timedelta(hours=1))
                    avg_12h = self._compute_average(sensor_id, timedelta(hours=12))
                    self.tree.insert("", "end", values=(
                        sensor_id, f"{value:.2f}", unit, timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        f"{avg_1h:.2f}" if avg_1h is not None else "-",
                        f"{avg_12h:.2f}" if avg_12h is not None else "-"
                    ))
            self.root.after(3000, update)

        self.root.after(1000, update)

    def _compute_average(self, sensor_id, period):
        now = datetime.now()
        readings = self.sensor_history[sensor_id]
        values = [v for t, v in readings if now - t <= period]
        if not values:
            return None
        return sum(values) / len(values)


def main():
    root = tk.Tk()
    app = GUIApplication(root)

    def on_close():
        print("Zamykanie aplikacji...")
        app.stop_server()
        app.logger.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
