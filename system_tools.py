"""Wi-Fi, Bluetooth, India region and file search. Uses the host OS's own tools."""
import os, sys, subprocess, threading, datetime, webbrowser
import tkinter as tk
from tkinter import ttk, messagebox

WIN, MAC = sys.platform.startswith("win"), sys.platform == "darwin"


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=15).stdout.strip() or "(nothing found)"
    except Exception as e:
        return f"Not available here: {e}"


def wifi_list():
    if WIN: return run(["netsh", "wlan", "show", "networks"])
    if MAC: return "Use Open Wi-Fi Settings."
    return run(["nmcli", "-f", "SSID,SIGNAL,SECURITY", "dev", "wifi"])


def bt_list():
    if WIN: return run(["powershell", "-NoProfile", "-Command",
                        "Get-PnpDevice -Class Bluetooth | Format-Table Status,FriendlyName -AutoSize | Out-String"])
    if MAC: return run(["system_profiler", "SPBluetoothDataType"])
    return run(["bluetoothctl", "devices"])


def open_os_settings(page):
    try:
        if WIN: os.startfile({"wifi": "ms-settings:network-wifi", "bt": "ms-settings:bluetooth",
                              "region": "ms-settings:regionlanguage"}[page])
        elif MAC: subprocess.Popen(["open", "x-apple.systempreferences:"])
        else: subprocess.Popen(["gnome-control-center", {"wifi": "wifi", "bt": "bluetooth", "region": "region"}[page]])
    except Exception as e:
        messagebox.showinfo("Settings", f"Could not open: {e}")


def ist_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30)))


def open_system(parent):
    win = tk.Toplevel(parent); win.title("Bharat OS - System"); win.geometry("680x500"); win.configure(bg="#202228")
    nb = ttk.Notebook(win); nb.pack(fill="both", expand=True, padx=8, pady=8)

    def text_tab(title, getter, page):
        f = tk.Frame(nb, bg="#202228"); nb.add(f, text=title)
        box = tk.Text(f, bg="#15161a", fg="white", font=("Consolas", 10)); box.pack(fill="both", expand=True, padx=6, pady=6)
        def scan():
            box.delete("1.0", "end"); box.insert("end", "Scanning...")
            def w():
                out = getter(); win.after(0, lambda: (box.delete("1.0", "end"), box.insert("end", out)))
            threading.Thread(target=w, daemon=True).start()
        bar = tk.Frame(f, bg="#202228"); bar.pack(fill="x")
        for t, c in (("Scan", scan), (f"Open {title} Settings", lambda: open_os_settings(page))):
            tk.Button(bar, text=t, command=c, bg="#292c33", fg="white", relief="flat").pack(side="left", padx=6, pady=6)
        scan()
    text_tab("Wi-Fi", wifi_list, "wifi"); text_tab("Bluetooth", bt_list, "bt")

    # India / region
    r = tk.Frame(nb, bg="#202228"); nb.add(r, text="India")
    clock = tk.Label(r, bg="#202228", fg="#FF9933", font=("Arial", 26, "bold")); clock.pack(pady=24)
    tk.Label(r, text="Indian Standard Time (UTC+5:30)\nLanguages: हिन्दी, বাংলা, தமிழ், తెలుగు, मराठी, ગુજરાતી, ಕನ್ನಡ, മലയാളം, ਪੰਜਾਬੀ, English",
             bg="#202228", fg="white", wraplength=560, font=("Arial", 11)).pack()
    tk.Button(r, text="Open Region & Language Settings", command=lambda: open_os_settings("region"),
              bg="#138808", fg="white", relief="flat").pack(pady=16, ipadx=10, ipady=4)
    def tick(): clock.config(text=ist_now().strftime("%H:%M:%S  %d %b %Y")); win.after(1000, tick)
    tick()

    # Search
    s = tk.Frame(nb, bg="#202228"); nb.add(s, text="Search")
    q = tk.Entry(s, font=("Arial", 12)); q.pack(fill="x", padx=8, pady=8, ipady=4)
    lst = tk.Listbox(s, bg="#15161a", fg="white", font=("Consolas", 10)); lst.pack(fill="both", expand=True, padx=8)
    cancel = {"n": 0}
    def search(_e=None):
        cancel["n"] += 1; me = cancel["n"]; lst.delete(0, "end"); term = q.get().lower().strip()
        if not term: return
        def w():
            n = 0
            for root_, dirs, files in os.walk(os.path.expanduser("~")):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for name in files:
                    if me != cancel["n"] or n >= 300: return
                    if term in name.lower():
                        n += 1; p = os.path.join(root_, name); win.after(0, lambda p=p: lst.insert("end", p))
        threading.Thread(target=w, daemon=True).start()
    def open_sel(_e=None):
        if lst.curselection():
            p = lst.get(lst.curselection()[0])
            os.startfile(p) if WIN else subprocess.Popen(["open" if MAC else "xdg-open", p])
    q.bind("<Return>", search); lst.bind("<Double-1>", open_sel)
    tk.Button(s, text="Search the web instead", bg="#292c33", fg="white", relief="flat",
              command=lambda: webbrowser.open("https://www.google.com/search?q=" + q.get())).pack(pady=6)
