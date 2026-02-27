import cv2
from config_utils import DEFAULT_CONFIG


def draw_config_overlay(frame, config, config_lines, width, height):
    y_offset = 25
    for line in config_lines:
        cv2.putText(
            frame,
            line,
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )
        y_offset += 22

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
    cv2.putText(
        frame,
        f"y_min: {y_min}",
        (10, max(20, y_min_px - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 0, 255),
        2
    )
    cv2.putText(
        frame,
        f"y_max: {y_max}",
        (10, min(height - 10, y_max_px + 20)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 0, 255),
        2
    )
    cv2.putText(
        frame,
        f"x_min: {x_min}",
        (max(10, x_min_px + 8), 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 0, 255),
        2
    )
    cv2.putText(
        frame,
        f"x_max: {x_max}",
        (min(width - 120, x_max_px - 80), 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 0, 255),
        2
    )
