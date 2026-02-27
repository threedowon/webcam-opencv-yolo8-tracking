import ctypes
import os

from config_utils import get_base_dir


def set_app_user_model_id(app_id):
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        return True
    except Exception:
        return False


def apply_window_icon(window_title, icon_filename="lotte.ico"):
    # Applies icon to window/taskbar if possible.
    icon_path = os.path.join(get_base_dir(), icon_filename)
    if not os.path.exists(icon_path):
        return False
    user32 = ctypes.windll.user32
    hicon = user32.LoadImageW(
        None,
        icon_path,
        1,  # IMAGE_ICON
        0,
        0,
        0x00000010  # LR_LOADFROMFILE
    )
    if not hicon:
        return False
    hwnd = user32.FindWindowW(None, window_title)
    if not hwnd:
        return False
    WM_SETICON = 0x0080
    ICON_BIG = 1
    ICON_SMALL = 0
    user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
    user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
    return True
