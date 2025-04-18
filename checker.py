import pyperclip
from pynput import keyboard
from datetime import datetime
import pygetwindow as gw
from time import sleep
import threading
import psutil
from bleak import BleakScanner
import asyncio
import requests
import os

SERVER = "__REMOTE_SERVER__"
STUDENT_ID = "__STUDENT_ID__"
SUBJECT_CODE = "__SUBJECT_CODE__"
TOKEN = "__TOKEN__"
LOG_DIR = "local_logs"
TIMEOUT = 10

stop_event = threading.Event()
time_interval = 10
keywords = ["chatgpt", "google", "stackoverflow"]

def short_time():
    return datetime.now().strftime("%y%m%d:%H%M%S")

def send_log(log_type, content):
    payload = {
        "student_id": STUDENT_ID,
        "subject_code": SUBJECT_CODE,
        "log_type": log_type,
        "content": content,
        "token": TOKEN
    }
    try:
        requests.post(f"{SERVER}/log_event", json=payload, timeout=TIMEOUT)
    except:
        pass

    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, f"{log_type}.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{short_time()}] {content}\n")


def on_press(key):
    if key in {keyboard.Key.ctrl, keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r}:
        send_log("keyboard", f"Special key pressed: {key}")
        send_log("critical", f"Suspicious key: {key}")

def monitor_clipboard():
    recent = ""
    while not stop_event.is_set():
        try:
            clip = pyperclip.paste()
            if clip != recent:
                short_clip = clip[:100]
                send_log("clipboard", short_clip)
                if len(clip) >= 30:
                    send_log("critical", f"Long clipboard content: {clip}")
                recent = clip
        except:
            pass
        sleep(time_interval)

def check_tab_keywords(title):
    for keyword in keywords:
        if keyword.lower() in title.lower():
            return True
    return False

def track_window():
    prev_title = ""
    while not stop_event.is_set():
        try:
            win = gw.getActiveWindow()
            if win:
                title = win.title
                if title != prev_title:
                    send_log("tab", f"Tab changed: {title}")
                    if check_tab_keywords(title):
                        send_log("critical", f"Suspicious tab: {title}")
                    prev_title = title
        except:
            pass
        sleep(time_interval)

def get_drives():
    drives = []
    for p in psutil.disk_partitions():
        if 'removable' in p.opts:
            drives.append(p.device)
    return drives

def monitor_usb():
    prev = get_drives()
    while not stop_event.is_set():
        cur = get_drives()
        added = set(cur) - set(prev)
        removed = set(prev) - set(cur)
        for d in added:
            send_log("usb", f"USB connected: {d}")
        for d in removed:
            send_log("usb", f"USB disconnected: {d}")
        prev = cur
        sleep(1)

async def scan_bluetooth():
    found = set()
    while not stop_event.is_set():
        devices = await BleakScanner.discover()
        for d in devices:
            if d.address not in found:
                send_log("bluetooth", f"Bluetooth: {d.name} ({d.address})")
                found.add(d.address)
        await asyncio.sleep(time_interval)

def bluetooth_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(scan_bluetooth())
    loop.close()

def heartbeat_loop():
    while not stop_event.is_set():
        try:
            requests.post(f"{SERVER}/heartbeat", json={
                "student_id": STUDENT_ID,
                "subject_code": SUBJECT_CODE
            }, timeout=TIMEOUT)
        except:
            pass
        sleep(10)


if __name__ == "__main__":
    print(f"Monitoring started for {STUDENT_ID} ({SUBJECT_CODE})")
    keyboard.Listener(on_press=on_press).start()
    threading.Thread(target=monitor_clipboard).start()
    threading.Thread(target=track_window).start()
    threading.Thread(target=monitor_usb).start()
    threading.Thread(target=bluetooth_thread).start()
    threading.Thread(target=heartbeat_loop).start()

