import subprocess
from typing import Tuple


def get_current_screen_resolution() -> Tuple[int, int]:
    try:
        v = subprocess.run(["xrandr"], capture_output=True, text=True)
        for line in v.stdout.splitlines():
            if "*" in line:
                res = line.strip().split(" ")[0].split("x")
                return int(res[0]), int(res[1])
    except Exception:
        return 1920, 1080


def calculate_coords_to_centre_window(screen_resolution: Tuple[int, int], window_width: int, window_height: int) -> Tuple[int, int]:
    x = (screen_resolution[0]//2)-(window_width//2)
    y = (screen_resolution[1]//2)-(window_height//2)
    return x, y
