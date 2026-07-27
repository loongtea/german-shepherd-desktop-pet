import ctypes
import json
import math
import random
import sys
import time
from ctypes import wintypes
from pathlib import Path


APP_NAME = "ShepherdPetAlpha"
FRAME_MS = 120
CLICK_DRAG_THRESHOLD = 8
LOOK_DEADZONE = 30
LOOK_RADIUS = 180
SAD_AFTER_SECONDS = 60

WS_POPUP = 0x80000000
WS_EX_LAYERED = 0x00080000
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
ULW_ALPHA = 0x00000002
AC_SRC_OVER = 0
AC_SRC_ALPHA = 1
DIB_RGB_COLORS = 0
PM_REMOVE = 0x0001
WM_DESTROY = 0x0002
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_MOUSEMOVE = 0x0200
WM_RBUTTONUP = 0x0205
WM_COMMAND = 0x0111
MF_STRING = 0x00000000
TPM_RIGHTBUTTON = 0x0002
TPM_RETURNCMD = 0x0100
ID_EXIT = 1001
EXIT_MESSAGE = "稼轩还想下次继续和你玩哦~"
RANDOM_IDLE_STATES = ("idle-random-3", "idle-random-6", "idle-random-7", "idle-random-8")

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class SIZE(ctypes.Structure):
    _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ("BlendOp", ctypes.c_byte),
        ("BlendFlags", ctypes.c_byte),
        ("SourceConstantAlpha", ctypes.c_byte),
        ("AlphaFormat", ctypes.c_byte),
    ]


user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = wintypes.LPARAM
user32.CreateWindowExW.restype = wintypes.HWND
user32.CreatePopupMenu.restype = wintypes.HMENU
user32.AppendMenuW.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_size_t, wintypes.LPCWSTR]
user32.TrackPopupMenu.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.HWND, ctypes.c_void_p]
user32.TrackPopupMenu.restype = wintypes.UINT
user32.DestroyMenu.argtypes = [wintypes.HMENU]
user32.MessageBoxW.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.UINT]
user32.UpdateLayeredWindow.argtypes = [
    wintypes.HWND,
    wintypes.HDC,
    ctypes.POINTER(POINT),
    ctypes.POINTER(SIZE),
    wintypes.HDC,
    ctypes.POINTER(POINT),
    wintypes.COLORREF,
    ctypes.POINTER(BLENDFUNCTION),
    wintypes.DWORD,
]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", POINT),
    ]


WNDPROC = ctypes.WINFUNCTYPE(wintypes.LPARAM, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)


class WNDCLASS(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HCURSOR),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


def app_dir():
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def cursor_position():
    point = POINT()
    user32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y


def loword(value):
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def signed_lparam(value):
    bits = ctypes.sizeof(wintypes.LPARAM) * 8
    mask = (1 << bits) - 1
    value &= mask
    sign = 1 << (bits - 1)
    return value - (1 << bits) if value & sign else value


class AlphaPet:
    def __init__(self):
        self.assets = app_dir() / "assets"
        self.manifest = json.loads((self.assets / "manifest.json").read_text(encoding="utf-8"))
        self.width = self.manifest["width"]
        self.height = self.manifest["height"]
        self.frames = {}
        self.hwnd = None
        self.x = max(20, user32.GetSystemMetrics(0) - self.width - 260)
        self.y = max(20, user32.GetSystemMetrics(1) - self.height - 160)
        self.dragging = False
        self.press = None
        self.window_at_press = None
        self.last_drag_x = None
        self.state = "idle"
        self.frame_index = 0
        self.one_shot = None
        self.last_run_state = "running-right"
        self.last_pointer_near = time.monotonic()
        self.last_interaction = time.monotonic()
        self.next_wave_at = self.pick_next_wave()
        self.wndproc = WNDPROC(self.handle_message)

    def pick_next_wave(self):
        return time.monotonic() + random.uniform(30, 90)

    def create_window(self):
        instance = kernel32.GetModuleHandleW(None)
        cls = WNDCLASS()
        cls.lpfnWndProc = self.wndproc
        cls.hInstance = instance
        cls.lpszClassName = APP_NAME
        user32.RegisterClassW(ctypes.byref(cls))
        self.hwnd = user32.CreateWindowExW(
            WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW,
            APP_NAME,
            APP_NAME,
            WS_POPUP,
            self.x,
            self.y,
            self.width,
            self.height,
            None,
            None,
            instance,
            None,
        )
        user32.ShowWindow(self.hwnd, 1)
        user32.UpdateWindow(self.hwnd)
        self.load_frames()

    def load_frames(self):
        raw_dir = self.assets / "raw"
        for state, files in self.manifest["states"].items():
            self.frames[state] = [self.make_bitmap((raw_dir / name).read_bytes()) for name in files]

    def make_bitmap(self, data):
        screen = user32.GetDC(None)
        memdc = gdi32.CreateCompatibleDC(screen)
        info = BITMAPINFO()
        info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        info.bmiHeader.biWidth = self.width
        info.bmiHeader.biHeight = -self.height
        info.bmiHeader.biPlanes = 1
        info.bmiHeader.biBitCount = 32
        bits = ctypes.c_void_p()
        hbmp = gdi32.CreateDIBSection(screen, ctypes.byref(info), DIB_RGB_COLORS, ctypes.byref(bits), None, 0)
        ctypes.memmove(bits, data, len(data))
        old = gdi32.SelectObject(memdc, hbmp)
        user32.ReleaseDC(None, screen)
        return memdc, hbmp, old

    def update_layer(self, frame):
        memdc, _hbmp, _old = frame
        screen = user32.GetDC(None)
        dst = POINT(self.x, self.y)
        src = POINT(0, 0)
        size = SIZE(self.width, self.height)
        blend = BLENDFUNCTION(AC_SRC_OVER, 0, 255, AC_SRC_ALPHA)
        user32.UpdateLayeredWindow(self.hwnd, screen, ctypes.byref(dst), ctypes.byref(size), memdc, ctypes.byref(src), 0, ctypes.byref(blend), ULW_ALPHA)
        user32.ReleaseDC(None, screen)

    def handle_message(self, hwnd, msg, wparam, lparam):
        if msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        if msg == WM_LBUTTONDOWN:
            self.press = cursor_position()
            self.window_at_press = (self.x, self.y)
            self.dragging = False
            self.last_drag_x = self.press[0]
            self.last_interaction = time.monotonic()
            user32.SetCapture(hwnd)
            return 0
        if msg == WM_MOUSEMOVE and self.press is not None:
            mx, my = cursor_position()
            dx = mx - self.press[0]
            dy = my - self.press[1]
            if not self.dragging and math.hypot(dx, dy) > CLICK_DRAG_THRESHOLD:
                self.dragging = True
                self.one_shot = None
            if self.dragging:
                self.x = self.window_at_press[0] + dx
                self.y = self.window_at_press[1] + dy
                step_dx = mx - (self.last_drag_x or mx)
                if abs(step_dx) >= 1:
                    self.last_run_state = "running-right" if step_dx > 0 else "running-left"
                self.last_drag_x = mx
                self.state = self.last_run_state
                self.last_interaction = time.monotonic()
            return 0
        if msg == WM_LBUTTONUP:
            was_dragging = self.dragging
            self.dragging = False
            self.press = None
            self.window_at_press = None
            user32.ReleaseCapture()
            self.last_interaction = time.monotonic()
            if not was_dragging:
                self.start_one_shot("jumping")
            return 0
        if msg == WM_RBUTTONUP:
            self.show_context_menu(hwnd)
            return 0
        if msg == WM_COMMAND:
            if wparam & 0xFFFF == ID_EXIT:
                self.exit_with_message(hwnd)
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, signed_lparam(lparam))

    def show_context_menu(self, hwnd):
        x, y = cursor_position()
        menu = user32.CreatePopupMenu()
        if not menu:
            return
        user32.AppendMenuW(menu, MF_STRING, ID_EXIT, "退出")
        user32.SetForegroundWindow(hwnd)
        command = user32.TrackPopupMenu(menu, TPM_RIGHTBUTTON | TPM_RETURNCMD, x, y, 0, hwnd, None)
        user32.DestroyMenu(menu)
        if command == ID_EXIT:
            self.exit_with_message(hwnd)

    def exit_with_message(self, hwnd):
        user32.MessageBoxW(hwnd, EXIT_MESSAGE, "稼轩", 0x00000040)
        user32.DestroyWindow(hwnd)

    def start_one_shot(self, state):
        self.one_shot = state
        self.state = state
        self.frame_index = 0

    def choose_state(self):
        now = time.monotonic()
        if self.dragging:
            return self.last_run_state

        mx, my = cursor_position()
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        distance = math.hypot(mx - cx, my - cy)
        if LOOK_DEADZONE < distance <= LOOK_RADIUS:
            self.last_pointer_near = now
            return "look"
        if now - self.last_pointer_near > SAD_AFTER_SECONDS and now - self.last_interaction > SAD_AFTER_SECONDS:
            return "waiting"
        if now >= self.next_wave_at and now - self.last_interaction > 8:
            self.next_wave_at = self.pick_next_wave()
            random_idle_state = random.choice(RANDOM_IDLE_STATES)
            self.start_one_shot(random_idle_state)
            return random_idle_state
        return "idle"

    def look_frame_index(self):
        mx, my = cursor_position()
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        angle = math.atan2(my - cy, mx - cx)
        return int(round(((angle + math.pi) / (2 * math.pi)) * 15)) % 16

    def tick(self):
        if self.one_shot:
            state = self.one_shot
            frame = self.frames[state][self.frame_index % len(self.frames[state])]
            self.update_layer(frame)
            self.frame_index += 1
            if self.frame_index >= len(self.frames[state]):
                self.one_shot = None
                self.frame_index = 0
                self.last_interaction = time.monotonic()
        else:
            new_state = self.choose_state()
            if new_state != self.state:
                self.state = new_state
                self.frame_index = 0
            if self.state == "look":
                frame = self.frames["look"][self.look_frame_index()]
            else:
                frames = self.frames[self.state]
                frame = frames[self.frame_index % len(frames)]
                self.frame_index += 1
            self.update_layer(frame)

    def run(self):
        self.create_window()
        msg = MSG()
        next_tick = 0
        while True:
            while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
                if msg.message == 0x0012:
                    return
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            now = time.monotonic()
            if now >= next_tick:
                self.tick()
                next_tick = now + FRAME_MS / 1000
            time.sleep(0.01)


if __name__ == "__main__":
    AlphaPet().run()
