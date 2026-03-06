import subprocess
import time
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import ctypes
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCK_FILE  = os.path.join(SCRIPT_DIR, ".running.lock")
ENV_FILE   = os.path.join(SCRIPT_DIR, ".env")

# ── Anti double-instance ──────────────────────────────────────────────────────
if os.path.exists(LOCK_FILE):
    try:
        with open(LOCK_FILE) as f:
            pid = int(f.read().strip())
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            sys.exit()
    except:
        pass

with open(LOCK_FILE, "w") as f:
    f.write(str(os.getpid()))

atexit_registered = False
import atexit
atexit.register(lambda: os.remove(LOCK_FILE) if os.path.exists(LOCK_FILE) else None)

# ── Setup .env if missing ─────────────────────────────────────────────────────
if not os.path.exists(ENV_FILE):
    setup_script = os.path.join(SCRIPT_DIR, "setup.py")
    if os.path.exists(setup_script):
        python_exe = sys.executable.replace("pythonw.exe", "python.exe")
        subprocess.run([python_exe, setup_script], cwd=SCRIPT_DIR)
    if not os.path.exists(ENV_FILE):
        sys.exit()

load_dotenv(ENV_FILE)
USERNAME = os.getenv("ESSEC_USERNAME")
PASSWORD = os.getenv("ESSEC_PASSWORD")

# ── Popup "WiFi not detected" (5 seconds) ────────────────────────────────────
def show_no_wifi_popup():
    root = tk.Tk()
    root.title("ESSEC WiFi")
    root.geometry("300x100")
    root.resizable(False, False)
    root.attributes("-topmost", True)
    tk.Label(root, text="⚠️ ESSEC STUDENT not detected",
             font=("Arial", 11, "bold"), fg="#c0392b").pack(pady=15)
    bar = ttk.Progressbar(root, length=260, mode="determinate", maximum=50)
    bar.pack()
    def countdown(i=50):
        if i <= 0:
            root.destroy()
            return
        bar["value"] = 50 - i
        root.after(100, countdown, i - 1)
    countdown()
    root.mainloop()

# ── Network checks ────────────────────────────────────────────────────────────
def force_wifi_scan():
    """Force Windows to rescan WiFi networks via WlanScan API."""
    try:
        wlanapi = ctypes.windll.wlanapi
        hClient = ctypes.c_void_p()
        dwVersion = ctypes.c_ulong()
        wlanapi.WlanOpenHandle(2, None, ctypes.byref(dwVersion), ctypes.byref(hClient))

        # Get interface list
        class WLAN_INTERFACE_INFO(ctypes.Structure):
            _fields_ = [("InterfaceGuid", ctypes.c_byte * 16),
                        ("strInterfaceDescription", ctypes.c_wchar * 256),
                        ("isState", ctypes.c_uint)]

        class WLAN_INTERFACE_INFO_LIST(ctypes.Structure):
            _fields_ = [("dwNumberOfItems", ctypes.c_ulong),
                        ("dwIndex", ctypes.c_ulong),
                        ("InterfaceInfo", WLAN_INTERFACE_INFO * 64)]

        pIfList = ctypes.POINTER(WLAN_INTERFACE_INFO_LIST)()
        wlanapi.WlanEnumInterfaces(hClient, None, ctypes.byref(pIfList))

        if pIfList and pIfList.contents.dwNumberOfItems > 0:
            guid = pIfList.contents.InterfaceInfo[0].InterfaceGuid
            wlanapi.WlanScan(hClient, ctypes.byref((ctypes.c_byte * 16)(*guid)), None, None, None)
            time.sleep(2)  # Wait for scan results

        wlanapi.WlanFreeMemory(pIfList)
        wlanapi.WlanCloseHandle(hClient, None)
    except:
        time.sleep(2)  # Fallback wait

def is_connected():
    result = subprocess.run(
        ["netsh", "wlan", "show", "interfaces"],
        capture_output=True, text=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    return "ESSEC STUDENT" in result.stdout

def is_network_available():
    """Check with forced rescan to avoid stale cache."""
    force_wifi_scan()
    result = subprocess.run(
        ["netsh", "wlan", "show", "networks"],
        capture_output=True, text=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    if "ESSEC STUDENT" in result.stdout:
        return True
    if is_connected():
        return True
    return False

def has_internet():
    try:
        import urllib.request
        response = urllib.request.urlopen(
            "http://www.msftconnecttest.com/connecttest.txt", timeout=3)
        return response.read() == b"Microsoft Connect Test"
    except:
        return False

def wait_for_portal(timeout=3):
    """Wait for network to stabilize after connection.
    Returns True if captive portal needed, False if internet already works."""
    start = time.time()
    while time.time() - start < timeout:
        if has_internet():
            return False
        time.sleep(1)
    return True

def connect_to_wifi():
    if is_connected():
        return True
    profile_xml = """<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>ESSEC STUDENT</name>
    <SSIDConfig><SSID><name>ESSEC STUDENT</name></SSID></SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM><security><authEncryption>
        <authentication>open</authentication>
        <encryption>none</encryption>
        <useOneX>false</useOneX>
    </authEncryption></security></MSM>
</WLANProfile>"""
    profile_path = os.path.join(SCRIPT_DIR, "essec_profile.xml")
    with open(profile_path, "w") as f:
        f.write(profile_xml)
    subprocess.run(
        ["netsh", "wlan", "add", "profile", f"filename={profile_path}"],
        capture_output=True, text=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    result = subprocess.run(
        ["netsh", "wlan", "connect", "name=ESSEC STUDENT"],
        capture_output=True, text=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    return "successfully" in result.stdout.lower()

# ── Selenium driver ───────────────────────────────────────────────────────────
def create_driver():
    try:
        from selenium.webdriver.chrome.service import Service as ChromeService
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--ignore-certificate-errors")
        for path in [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]:
            if os.path.exists(path):
                options.binary_location = path
                break
        return webdriver.Chrome(
            service=ChromeService(
                executable_path=os.path.join(SCRIPT_DIR, "chromedriver.exe")),
            options=options
        )
    except:
        pass

    try:
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        from selenium.webdriver.firefox.service import Service as FirefoxService
        options = FirefoxOptions()
        options.add_argument("--headless")
        for path in [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        ]:
            if os.path.exists(path):
                options.binary_location = path
                break
        return webdriver.Firefox(
            service=FirefoxService(
                executable_path=os.path.join(SCRIPT_DIR, "geckodriver.exe")),
            options=options
        )
    except:
        pass

    raise Exception("No compatible browser found (Chrome or Firefox required)")

# ── Captive portal ────────────────────────────────────────────────────────────
def open_and_fill_portal():
    driver = create_driver()
    try:
        driver.get("http://www.msftconnecttest.com/redirect")
        wait = WebDriverWait(driver, 30)
        try:
            popup = driver.find_element(By.ID, "portal-session-timeout-popup")
            if popup.is_displayed():
                driver.find_element(By.ID, "ui_session_timeout_retry_button").click()
                time.sleep(2)
        except:
            pass

        username_field = wait.until(
            EC.presence_of_element_located((By.ID, "user.username"))
        )
        username_field.clear()
        username_field.send_keys(USERNAME)
        password_field = driver.find_element(By.ID, "user.password")
        password_field.clear()
        password_field.send_keys(PASSWORD)

        # Submit
        driver.find_element(By.ID, "ui_login_signon_button").click()

        # Detect login failure — error message appears on bad credentials
        try:
            error = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "ui_login_error_message"))
            )
            if error.is_displayed():
                driver.quit()
                if messagebox.askyesno("Login failed",
                    "Incorrect credentials.\nDo you want to update them?"):
                    setup_script = os.path.join(SCRIPT_DIR, "setup.py")
                    python_exe = sys.executable.replace("pythonw.exe", "python.exe")
                    subprocess.run([python_exe, setup_script], cwd=SCRIPT_DIR)
                return
        except:
            pass  # No error message = login likely succeeded

        try:
            WebDriverWait(driver, 15).until_not(
                EC.title_contains("ESSEC BUSINESS SCHOOL")
            )
        except:
            pass

    finally:
        try:
            driver.quit()
        except:
            pass

# ── Main ──────────────────────────────────────────────────────────────────────
if not is_network_available():
    show_no_wifi_popup()
    sys.exit()

if is_connected() and has_internet():
    sys.exit()

if not USERNAME or not PASSWORD:
    messagebox.showerror("Error",
        "Missing credentials.\nRun setup.py to configure.")
    sys.exit()

if connect_to_wifi():
    needs_portal = wait_for_portal(timeout=1)
    if needs_portal:
        open_and_fill_portal()
else:
    messagebox.showerror("Error", "Could not connect to ESSEC STUDENT.")