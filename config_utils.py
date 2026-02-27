import json
import os
import sys


DEFAULT_CONFIG = {
    "ip": "127.0.0.1",
    "port_out": 8000,
    "port_in": 8001,
    "usb": 0,
    "max_det": 1,
    "x_min": 0.0,
    "x_max": 1.0,
    "y_min": 0.0,
    "y_max": 1.0,
    "camera_open_wait_min": 1,
    "read_fail_max": 10,
    "read_fail_retry_sec": 0.5,
    "log_dir": "C:\\imfine\\apps\\Orbbec\\Log"
}


def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)


def load_config():
    config_path = os.path.join(get_base_dir(), "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            for key, value in DEFAULT_CONFIG.items():
                config.setdefault(key, value)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    else:
        config = DEFAULT_CONFIG.copy()
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    return config


def build_config_lines(config):
    return [
        f"ip: {config.get('ip', DEFAULT_CONFIG['ip'])}",
        f"port_out: {config.get('port_out', DEFAULT_CONFIG['port_out'])}",
        f"port_in: {config.get('port_in', DEFAULT_CONFIG['port_in'])}",
        f"usb: {config.get('usb', DEFAULT_CONFIG['usb'])}",
        f"max_det: {config.get('max_det', DEFAULT_CONFIG['max_det'])}",
        f"x_min: {config.get('x_min', DEFAULT_CONFIG['x_min'])}",
        f"x_max: {config.get('x_max', DEFAULT_CONFIG['x_max'])}",
        f"y_min: {config.get('y_min', DEFAULT_CONFIG['y_min'])}",
        f"y_max: {config.get('y_max', DEFAULT_CONFIG['y_max'])}",
        f"camera_open_wait_min: {config.get('camera_open_wait_min', DEFAULT_CONFIG['camera_open_wait_min'])}",
        f"read_fail_max: {config.get('read_fail_max', DEFAULT_CONFIG['read_fail_max'])}",
        f"read_fail_retry_sec: {config.get('read_fail_retry_sec', DEFAULT_CONFIG['read_fail_retry_sec'])}",
        f"log_dir: {config.get('log_dir', DEFAULT_CONFIG['log_dir'])}"
    ]
