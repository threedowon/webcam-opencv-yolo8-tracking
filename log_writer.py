import os
from datetime import datetime


class OrbbecLogger:
    def __init__(self, log_dir, line_limit=100_000):
        self.log_dir = log_dir
        self.line_limit = line_limit
        self._session_timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        self._file_index = 1
        self._log_path = self._create_log_path(for_rotation=False)
        self._line_count = 0

    def _create_log_path(self, for_rotation=False):
        os.makedirs(self.log_dir, exist_ok=True)
        if for_rotation:
            filename = f"Orbbec_log_{self._session_timestamp}_{self._file_index}"
        else:
            index = 1
            while True:
                filename = f"Orbbec_log_{self._session_timestamp}_{index}"
                path = os.path.join(self.log_dir, filename)
                if not os.path.exists(path):
                    self._file_index = index
                    return path
                index += 1
        path = os.path.join(self.log_dir, filename)
        return path

    def write(self, message):
        if self._line_count >= self.line_limit:
            self._file_index += 1
            self._log_path = self._create_log_path(for_rotation=True)
            self._line_count = 0
        timestamp = datetime.now().strftime("%Y.%m.%d-%H.%M.%S")
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
        self._line_count += 1
