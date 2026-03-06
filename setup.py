import subprocess
import os
import sys
import tkinter as tk
from tkinter import messagebox

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE   = os.path.join(SCRIPT_DIR, ".env")
ICON_FILE  = os.path.join(SCRIPT_DIR, "icon.ico")

def find_pythonw():
    candidate = sys.executable.replace("python.exe", "pythonw.exe")
    if os.path.exists(candidate):
        return candidate
    for path in [
        r"C:\Python312\pythonw.exe",
        r"C:\Python311\pythonw.exe",
        r"C:\Python310\pythonw.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python310\pythonw.exe"),
    ]:
        if os.path.exists(path):
            return path
    return None

def create_shortcut(pythonw_exe):
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    shortcut_path = os.path.join(desktop, "ESSEC WiFi.lnk")
    target = os.path.join(SCRIPT_DIR, "essec_wifi_login.pyw")
    icon = ICON_FILE if os.path.exists(ICON_FILE) else pythonw_exe

    ps_script = f"""
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut('{shortcut_path}')
$sc.TargetPath = '{pythonw_exe}'
$sc.Arguments = '"{target}"'
$sc.WorkingDirectory = '{SCRIPT_DIR}'
$sc.IconLocation = '{icon}'
$sc.Save()
"""
    subprocess.run(
        ["powershell", "-Command", ps_script],
        capture_output=True, text=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    return shortcut_path if os.path.exists(shortcut_path) else None

def run_setup():
    root = tk.Tk()
    root.title("ESSEC WiFi - Setup")
    root.geometry("380x220")
    root.resizable(False, False)
    root.attributes("-topmost", True)

    result = {"username": None, "password": None}

    tk.Label(root, text="ESSEC WiFi Setup",
             font=("Arial", 13, "bold")).pack(pady=12)
    tk.Label(root, text="Enter your ESSEC credentials to continue.",
             font=("Arial", 9), fg="gray").pack()

    frame_user = tk.Frame(root)
    frame_user.pack(pady=5, padx=30, fill="x")
    tk.Label(frame_user, text="BID:", width=12, anchor="w").pack(side=tk.LEFT)
    entry_user = tk.Entry(frame_user, width=25)
    entry_user.pack(side=tk.LEFT)

    frame_pass = tk.Frame(root)
    frame_pass.pack(pady=5, padx=30, fill="x")
    tk.Label(frame_pass, text="Password:", width=12, anchor="w").pack(side=tk.LEFT)
    entry_pass = tk.Entry(frame_pass, width=22, show="*")
    entry_pass.pack(side=tk.LEFT)

    def toggle():
        entry_pass.config(show="" if entry_pass.cget("show") == "*" else "*")
        btn_eye.config(text="🙈" if entry_pass.cget("show") == "" else "👁")
    btn_eye = tk.Button(frame_pass, text="👁", command=toggle,
                        relief="flat", cursor="hand2")
    btn_eye.pack(side=tk.LEFT, padx=2)

    def on_save():
        u = entry_user.get().strip()
        p = entry_pass.get().strip()
        if not u or not p:
            messagebox.showerror("Error", "Please fill in all fields.")
            return
        result["username"] = u
        result["password"] = p
        root.destroy()

    def on_cancel():
        root.destroy()
        sys.exit()

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=15)
    tk.Button(btn_frame, text="Save", width=12, bg="#4CAF50",
              fg="white", command=on_save).pack(side=tk.LEFT, padx=8)
    tk.Button(btn_frame, text="Cancel", width=12, bg="#f44336",
              fg="white", command=on_cancel).pack(side=tk.LEFT, padx=8)

    root.mainloop()
    return result

if __name__ == "__main__":
    config = run_setup()
    if not config["username"]:
        sys.exit()

    # Créer le .env avec les identifiants
    with open(ENV_FILE, "w") as f:
        f.write(f"ESSEC_USERNAME={config['username']}\n")
        f.write(f"ESSEC_PASSWORD={config['password']}\n")

    # Créer le raccourci sur le bureau
    pythonw = find_pythonw()
    shortcut = None
    if pythonw:
        shortcut = create_shortcut(pythonw)

    if shortcut:
        messagebox.showinfo("✅ Setup complete",
            "Credentials saved!\n\n"
            "A shortcut 'ESSEC WiFi' was created on your Desktop.\n"
            "Pin it to the taskbar:\n"
            "Right-click → Pin to taskbar")
    else:
        messagebox.showwarning("⚠️ Warning",
            "Credentials saved but shortcut could not be created.\n\n"
            "Create it manually from the application folder.")
