"""Real browser downloader: saves the official installer to your Downloads folder.
It downloads - it does NOT open a website. URLs are the vendors' own download links
(they can change; if one fails, the error is shown)."""
import os, sys, threading, subprocess, urllib.request
import tkinter as tk
from tkinter import ttk, messagebox

W, M, L = "win", "mac", "linux"
BROWSERS = {   # name: {platform: (url, filename)}
    "Google Chrome": {W: ("https://dl.google.com/chrome/install/ChromeStandaloneSetup64.exe", "ChromeSetup.exe"),
                      M: ("https://dl.google.com/chrome/mac/universal/stable/GGRO/googlechrome.dmg", "Chrome.dmg"),
                      L: ("https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb", "chrome.deb")},
    "Mozilla Firefox": {W: ("https://download.mozilla.org/?product=firefox-latest&os=win64&lang=en-US", "FirefoxSetup.exe"),
                        M: ("https://download.mozilla.org/?product=firefox-latest&os=osx&lang=en-US", "Firefox.dmg"),
                        L: ("https://download.mozilla.org/?product=firefox-latest&os=linux64&lang=en-US", "firefox.tar.xz")},
    "Microsoft Edge": {W: ("https://go.microsoft.com/fwlink/?linkid=2109047&Channel=Stable&language=en", "EdgeSetup.exe")},
    "Brave": {W: ("https://laptop-updates.brave.com/latest/winx64", "BraveSetup.exe"),
              M: ("https://laptop-updates.brave.com/latest/osx", "Brave.dmg")},
    "Opera": {W: ("https://net.geo.opera.com/opera/stable/windows", "OperaSetup.exe")},
}
PLAT = W if sys.platform.startswith("win") else M if sys.platform == "darwin" else L
DEST = os.path.join(os.path.expanduser("~"), "Downloads", "Bharat_OS")


def download(url, path, progress, cancel):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "BharatOS/4.0"})
    with urllib.request.urlopen(req, timeout=30) as r, open(path + ".part", "wb") as f:
        total = int(r.headers.get("Content-Length") or 0); got = 0
        while not cancel.is_set():
            b = r.read(65536)
            if not b: break
            f.write(b); got += len(b); progress(got, total)
    if cancel.is_set():
        os.remove(path + ".part"); raise RuntimeError("cancelled")
    os.replace(path + ".part", path)


def open_downloader(parent):
    win = tk.Toplevel(parent); win.title("Bharat OS - Browser Downloads")
    win.geometry("560x420"); win.configure(bg="#202228")
    tk.Label(win, text=f"Download a browser  (saves to {DEST})", bg="#202228", fg="white",
             font=("Arial", 11, "bold")).pack(pady=10)
    for name, plats in BROWSERS.items():
        row = tk.Frame(win, bg="#292c33"); row.pack(fill="x", padx=14, pady=4)
        tk.Label(row, text=name, bg="#292c33", fg="white", width=16, anchor="w",
                 font=("Arial", 11)).pack(side="left", padx=8, pady=8)
        bar = ttk.Progressbar(row, length=200); bar.pack(side="left", padx=6)
        status = tk.Label(row, text="", bg="#292c33", fg="#aaa", width=12); status.pack(side="left")
        if PLAT not in plats:
            status.config(text="not for " + PLAT); continue
        url, fn = plats[PLAT]; path = os.path.join(DEST, fn)
        btn = tk.Button(row, text="Download", bg="#138808", fg="white", relief="flat")
        btn.pack(side="right", padx=8)

        def start(url=url, path=path, bar=bar, status=status, btn=btn):
            cancel = threading.Event(); btn.config(text="Cancel", command=cancel.set)
            def prog(g, t):
                win.after(0, lambda: (bar.config(value=(g * 100 / t) if t else 0),
                                      status.config(text=f"{g // 1048576} MB")))
            def work():
                try:
                    download(url, path, prog, cancel)
                    win.after(0, lambda: (status.config(text="Done ✔"), btn.config(
                        text="Install", command=lambda: install(path))))
                except Exception as e:
                    win.after(0, lambda: (status.config(text="Failed"), btn.config(
                        text="Retry", command=start), messagebox.showerror("Download", str(e), parent=win)))
            threading.Thread(target=work, daemon=True).start()
        btn.config(command=start)

    def install(path):
        if messagebox.askyesno("Install", f"Run this installer?\n{path}", parent=win):
            if PLAT == W: os.startfile(path)
            else: subprocess.Popen(["open" if PLAT == M else "xdg-open", path])
