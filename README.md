# ESSEC WiFi Auto-Login

Automatically connects to **ESSEC STUDENT** and fills in your credentials on the captive portal.

---

## First-time setup

1. Run `install.bat` as administrator
   - Installs Python if not already installed
   - Installs required dependencies (selenium, python-dotenv)
   - Opens the setup window to enter your credentials
2. A shortcut **"ESSEC WiFi"** is created on your Desktop
3. Right-click the shortcut → **Pin to taskbar**

---

## Daily use

Click the **ESSEC WiFi** shortcut in your taskbar.

- If ESSEC STUDENT is detected → connects and opens the portal with your credentials pre-filled
- If ESSEC STUDENT is not detected → a notification appears for 5 seconds then closes automatically
- If already connected with internet → closes immediately, nothing to do

---

## Files

| File | Description |
|------|-------------|
| `essec_wifi_login.pyw` | Main script |
| `setup.py` | Credentials configuration |
| `install.bat` | First-time installer |
| `chromedriver.exe` | Chrome driver (must match your Chrome version) |
| `geckodriver.exe` | Firefox driver (must match your Firefox version) |
| `.env` | Your credentials (auto-generated, do not share) |
| `icon.ico` | Taskbar icon (optional) |

---

## Troubleshooting

**The shortcut stopped working after moving the folder**
→ Run `install.bat` again to recreate the shortcut with the correct paths.

**Wrong credentials**
→ The portal will show a login error. Click "Yes" to update your credentials, or run `setup.py` manually.

**Chrome/Firefox driver error**
→ Download the driver matching your browser version:
- Chrome: https://googlechromelabs.github.io/chrome-for-testing/#stable
- Firefox: https://github.com/mozilla/geckodriver/releases

**ESSEC STUDENT not detected even when on campus**
→ Click the shortcut again — Windows WiFi scan cache may have been stale.

---

## Notes

- Your credentials are stored locally in `.env` — never share this file
- The app requires Chrome or Firefox to be installed
- If you move the folder, run `install.bat` again
