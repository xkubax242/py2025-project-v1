import os
import csv
import json
import zipfile
from datetime import datetime, timedelta
from typing import Optional, Iterator, Dict

class Logger:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as cfg_file:
            config = json.load(cfg_file)

        self.log_dir = config['log_dir']
        self.archive_dir = os.path.join(self.log_dir, 'archive')
        self.filename_pattern = config['filename_pattern']
        self.buffer_limit = config['buffer_size']
        self.rotation_hours = config['rotate_every_hours']
        self.max_file_size_bytes = config['max_size_mb'] * 1024 * 1024
        self.rotation_line_limit = config.get('rotate_after_lines')
        self.retention_days = config['retention_days']

        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.archive_dir, exist_ok=True)

        self._buffer = []
        self._file = None
        self._csv_writer = None
        self._current_log_path = None
        self._log_start_time = None
        self._lines_written = 0



    def start(self):
        self._log_start_time = datetime.now()
        self._current_log_path = os.path.join(
            self.log_dir, self._log_start_time.strftime(self.filename_pattern)
        )
        file_exists = os.path.isfile(self._current_log_path)

        self._file = open(self._current_log_path, 'a', newline='')
        self._csv_writer = csv.writer(self._file)

        if not file_exists:
            self._csv_writer.writerow(['timestamp', 'sensor_id', 'value', 'unit'])



    def stop(self):
        self._flush_buffer()
        if self._file:
            self._file.close()
            self._file = None



    def log_reading(self, sensor_id: str, timestamp: datetime, value: float, unit: str):
        self._buffer.append([timestamp.isoformat(), sensor_id, value, unit])
        if len(self._buffer) >= self.buffer_limit:
            self._flush_buffer()
            self._evaluate_rotation()



    def read_logs(
        self,
        start: datetime,
        end: datetime,
        sensor_id: Optional[str] = None
    ) -> Iterator[Dict]:
        def _read_csv_file(path):
            with open(path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row_time = datetime.fromisoformat(row['timestamp'])
                    if start <= row_time <= end:
                        if sensor_id is None or row['sensor_id'] == sensor_id:
                            yield {
                                'timestamp': row_time,
                                'sensor_id': row['sensor_id'],
                                'value': float(row['value']),
                                'unit': row['unit']
                            }



        def _read_zip_file(path):
            with zipfile.ZipFile(path) as archive:
                for member in archive.namelist():
                    with archive.open(member) as file:
                        content = file.read().decode().splitlines()
                        reader = csv.DictReader(content)
                        for row in reader:
                            row_time = datetime.fromisoformat(row['timestamp'])
                            if start <= row_time <= end:
                                if sensor_id is None or row['sensor_id'] == sensor_id:
                                    yield {
                                        'timestamp': row_time,
                                        'sensor_id': row['sensor_id'],
                                        'value': float(row['value']),
                                        'unit': row['unit']
                                    }


        for filename in os.listdir(self.log_dir):
            if filename.endswith('.csv'):
                yield from _read_csv_file(os.path.join(self.log_dir, filename))
        for filename in os.listdir(self.archive_dir):
            if filename.endswith('.zip'):
                yield from _read_zip_file(os.path.join(self.archive_dir, filename))


    def _flush_buffer(self):
        if self._file and self._buffer:
            self._csv_writer.writerows(self._buffer)
            self._lines_written += len(self._buffer)
            self._buffer.clear()
            self._file.flush()


    def _evaluate_rotation(self):
        rotate = False
        elapsed_time = datetime.now() - self._log_start_time
        file_size = os.path.getsize(self._current_log_path)
        if elapsed_time >= timedelta(hours=self.rotation_hours):
            rotate = True
        elif file_size >= self.max_file_size_bytes:
            rotate = True
        elif self.rotation_line_limit and self._lines_written >= self.rotation_line_limit:
            rotate = True
        if rotate:
            self._rotate_log()



    def _rotate_log(self):
        self.stop()
        self._compress_log()
        self._remove_old_archives()
        self.start()


    def _compress_log(self):
        archive_filename = os.path.basename(self._current_log_path) + '.zip'
        archive_path = os.path.join(self.archive_dir, archive_filename)

        with zipfile.ZipFile(archive_path, 'w', compression=zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(self._current_log_path, arcname=os.path.basename(self._current_log_path))
        os.remove(self._current_log_path)


    def _remove_old_archives(self):
        now = datetime.now()
        for archive_file in os.listdir(self.archive_dir):
            full_path = os.path.join(self.archive_dir, archive_file)
            if os.path.isfile(full_path):
                modified_time = datetime.fromtimestamp(os.path.getmtime(full_path))
                if (now - modified_time).days > self.retention_days:
                    os.remove(full_path)
