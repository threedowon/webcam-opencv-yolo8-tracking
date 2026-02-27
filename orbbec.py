import os
import sys
import cv2
import ctypes
import random
import time
import threading
from collections import deque
from ultralytics import YOLO
from pythonosc import udp_client, dispatcher, osc_server
from config_utils import DEFAULT_CONFIG, load_config, build_config_lines, get_base_dir
from log_writer import OrbbecLogger

config = load_config()

# 빌드 버전 (version.txt, Shift+S로 화면 표시)
def _load_build_version():
    try:
        base = sys._MEIPASS if getattr(sys, "frozen", False) else get_base_dir()
        path = os.path.join(base, "version.txt")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                line = (f.read() or "").strip().split("#")[0].strip()
                if line:
                    return "v" + line
    except Exception:
        pass
    return "v0.0.0"

BUILD_VERSION = _load_build_version()
# OpenCV 내부 카메라 에러 로그 콘솔 스팸 억제
cv2.setLogLevel(0)
logger = OrbbecLogger(config.get("log_dir", DEFAULT_CONFIG["log_dir"]))
log_history = deque(maxlen=12)

def log(message):
    logger.write(message)
    log_history.append(message)


had_error = False


def send_error(message):
    global had_error
    had_error = True
    log(f"[ERROR] {message}")
    try:
        osc.send_message("/error", message)
    except Exception:
        pass

# 카메라 열기 (시작 프로그램/부팅 직후 늦게 올라올 수 있으므로 재시도)
CAMERA_OPEN_WAIT_SEC = config.get("camera_open_wait_min", 1) * 60
usb_index = config.get("usb", 0)


def connect_camera():
    """카메라 연결: MSMF 백엔드 고정"""
    cap = cv2.VideoCapture(usb_index, cv2.CAP_MSMF)
    if cap.isOpened():
        log(f"[READY] Camera opened (usb={usb_index}, backend=MSMF)")
    return cap


cap = connect_camera()
open_start = time.time()
while not cap.isOpened():
    if time.time() - open_start > CAMERA_OPEN_WAIT_SEC:
        break
    logger.write("[WAIT] Waiting for camera...")
    time.sleep(1)
    cap.release()
    cap = connect_camera()
if cap.isOpened():
    time.sleep(0.5)

model = YOLO('yolov8s.pt')
osc = udp_client.SimpleUDPClient(
    config.get("ip", "127.0.0.1"),
    config.get("port_out", config.get("port", 8000))
)
ready_received = False


def handle_ready(address, *args):
    global ready_received
    if len(args) != 1 or not isinstance(args[0], bool):
        return
    prev_ready = ready_received
    ready_received = args[0]
    state = "ON" if ready_received else "OFF"
    log(f"[READY] {state}")
    if ready_received and not prev_ready:
        try:
            osc.send_message("/ready", [])
            log("[SEND] /ready")
        except Exception:
            pass


listen_port = config.get("port_in", 8001)
osc_dispatcher = dispatcher.Dispatcher()
osc_dispatcher.map("/ready", handle_ready)
osc_server_instance = osc_server.ThreadingOSCUDPServer(
    ("0.0.0.0", listen_port),
    osc_dispatcher
)
osc_thread = threading.Thread(
    target=osc_server_instance.serve_forever,
    daemon=True
)
osc_thread.start()
log(f"[READY] listening on {listen_port}")

# 카메라가 끝까지 안 열리면 종료
if not cap.isOpened():
    send_error("Camera open failed")
    print("[ERROR] Camera open failed. Check USB and config (usb index).")
    sys.exit(1)

log("[START] Orbbec tracking started")
try:
    osc.send_message("/start", [])
    log("[SEND] /start")
except Exception:
    pass


sending = False
last_send_time = 0.0
SEND_INTERVAL = 0.3  # 초
show_config = False
config_lines = build_config_lines(config)
active_ids = set()
show_log = False
fail_count = 0
MAX_FAIL = 5  # 연속 5프레임 실패해야 재연결

try:
    while True:
        # 1. 카메라가 열려 있지 않으면 재연결
        if not cap.isOpened():
            log("[WAIT] Camera not connected. Reconnecting in 2s...")
            time.sleep(2)
            cap = connect_camera()
            continue

        # 2. 프레임 읽기
        ret, frame = cap.read()

        # 3. 신호 끊김 또는 프레임 없음
        if not ret or frame is None:
            fail_count += 1
            log(f"[WARN] Frame read failed ({fail_count}/{MAX_FAIL})")
            if fail_count >= MAX_FAIL:
                log("[WAIT] Signal lost. Reconnecting...")
                cap.release()
                time.sleep(2)
                cap = connect_camera()
                fail_count = 0
            continue
        fail_count = 0  # 성공하면 리셋

        try:
            height, width = frame.shape[:2]

            results = model.track(
                frame,
                classes=[0],
                conf=0.6,
                iou=0.5,
                max_det=config.get("max_det", 5),
                persist=True,
                verbose=False,
                tracker="bytetrack.yaml",
            )

            current_ids = set()
            for box in results[0].boxes:
                x, y, w, h = box.xywh[0].tolist()
                conf = box.conf[0].item()

                if 80 < w < 300 and 150 < h < 500:
                    norm_x = x / width
                    norm_y = y / height
                    x_min = config.get("x_min", DEFAULT_CONFIG["x_min"])
                    x_max = config.get("x_max", DEFAULT_CONFIG["x_max"])
                    y_min = config.get("y_min", DEFAULT_CONFIG["y_min"])
                    y_max = config.get("y_max", DEFAULT_CONFIG["y_max"])
                    if x_max <= x_min:
                        continue
                    if norm_x < x_min or norm_x > x_max:
                        continue
                    if norm_y < y_min or norm_y > y_max:
                        continue
                    norm_x = (norm_x - x_min) / (x_max - x_min)

                    track_id = None
                    if box.id is not None and len(box.id) > 0:
                        track_id = int(box.id[0].item())
                    if track_id is None:
                        continue
                    current_ids.add(track_id)

                    if ready_received:
                        message = f"p{track_id}, Head, {norm_x}, {norm_y}"
                        osc.send_message("/update", message)
                        log(f"[SEND] /update {message}")

                    cv2.rectangle(
                        frame,
                        (int(x - w / 2), int(y - h / 2)),
                        (int(x + w / 2), int(y + h / 2)),
                        (0, 255, 0), 2
                    )
                    cv2.putText(
                        frame,
                        f"p{track_id}",
                        (int(x - w / 2), max(15, int(y - h / 2) - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2
                    )

            exited_ids = active_ids - current_ids
            for track_id in exited_ids:
                out_id = f"p{track_id}"
                if ready_received:
                    osc.send_message("/out", out_id)
                    log(f"[SEND] /out {out_id}")
            active_ids = current_ids

            if sending and ready_received:
                now = time.time()
                if now - last_send_time >= SEND_INTERVAL:
                    test_x = random.random()
                    test_y = random.random()
                    message = f"p1, Head, {test_x}, {test_y}"
                    osc.send_message("/update", message)
                    log(f"[AUTO] /update {message}")
                    print(f"[AUTO] /update {message}")
                    last_send_time = now

            if show_config:
                y_min = config.get("y_min", DEFAULT_CONFIG["y_min"])
                y_max = config.get("y_max", DEFAULT_CONFIG["y_max"])
                y_min_px = max(0, min(height - 1, int(y_min * height)))
                y_max_px = max(0, min(height - 1, int(y_max * height)))
                if y_min_px > y_max_px:
                    y_min_px, y_max_px = y_max_px, y_min_px
                x_min = config.get("x_min", DEFAULT_CONFIG["x_min"])
                x_max = config.get("x_max", DEFAULT_CONFIG["x_max"])
                x_min_px = max(0, min(width - 1, int(x_min * width)))
                x_max_px = max(0, min(width - 1, int(x_max * width)))
                if x_min_px > x_max_px:
                    x_min_px, x_max_px = x_max_px, x_min_px
                overlay = frame.copy()
                cv2.rectangle(
                    overlay,
                    (x_min_px, y_min_px),
                    (x_max_px, y_max_px),
                    (0, 0, 0),
                    -1
                )
                cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
                cv2.rectangle(
                    frame,
                    (x_min_px, y_min_px),
                    (x_max_px, y_max_px),
                    (0, 0, 255),
                    2
                )

            if show_log:
                log_lines = list(log_history)
                if log_lines:
                    line_height = 22
                    padding = 10
                    box_height = padding * 2 + line_height * len(log_lines)
                    box_width = width - 20
                    overlay = frame.copy()
                    cv2.rectangle(
                        overlay,
                        (10, 10),
                        (10 + box_width, 10 + box_height),
                        (0, 0, 0),
                        -1
                    )
                    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
                    y_offset = 10 + padding + line_height - 6
                    for line in log_lines:
                        cv2.putText(
                            frame,
                            line,
                            (20, y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.55,
                            (255, 255, 255),
                            1
                        )
                        y_offset += line_height

            bar_height = 0
            if show_config:
                line_height = 22
                padding = 10
                bar_height = padding * 2 + line_height * len(config_lines)
            display_frame = cv2.copyMakeBorder(
                frame,
                bar_height,
                0,
                0,
                0,
                cv2.BORDER_CONSTANT,
                value=(0, 0, 0)
            )
            if show_config and bar_height > 0:
                y_offset = padding + line_height - 6
                for line in config_lines:
                    cv2.putText(
                        display_frame,
                        line,
                        (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 255),
                        2
                    )
                    y_offset += line_height

            ready_text = "ready : true" if ready_received else "ready : false"
            ready_color = (0, 255, 0) if ready_received else (0, 0, 255)
            # 좌측 하단 고정 배치 (해상도 변경 시에도 안 사라지도록)
            ready_x = 10
            ready_y = max(24, display_frame.shape[0] - 12)
            version_x = 10
            version_y = max(20, ready_y - 24)
            cv2.putText(
                display_frame,
                BUILD_VERSION,
                (version_x, version_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )
            cv2.putText(
                display_frame,
                ready_text,
                (ready_x, ready_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                ready_color,
                2
            )

            cv2.imshow('OrbbecTracker', display_frame)

            key = cv2.waitKey(1) & 0xFF
            shift_down = (ctypes.windll.user32.GetAsyncKeyState(0x10) & 0x8000) != 0

            if key == ord('!'):
                sending = not sending
                state = "START" if sending else "STOP"
                print(f"[AUTO SEND] {state}")
                log(f"[AUTO SEND] {state}")
                if not sending:
                    osc.send_message("/out", "p1")
                    log("[SEND] /out p1")
            if key == ord('s') or key == ord('S'):
                show_config = not show_config
            if key == ord('d') or key == ord('D'):
                show_log = not show_log
            if key == 27:
                if shift_down:
                    break
        except Exception as e:
            log(f"[WAIT] Error: {e}. Reconnecting in 2s...")
            cap.release()
            time.sleep(2)
            cap = connect_camera()
except Exception as exc:
    send_error(str(exc))
finally:
    if sending and ready_received:
        osc.send_message("/out", "p1")
        log("[SEND] /out p1")
    if ready_received:
        for track_id in active_ids:
            out_id = f"p{track_id}"
            osc.send_message("/out", out_id)
            log(f"[SEND] /out {out_id}")
    if not had_error:
        try:
            osc.send_message("/close", [])
            log("[SEND] /close")
        except Exception:
            pass
    cap.release()
    cv2.destroyAllWindows()
    log("[STOP] Orbbec tracking stopped")
