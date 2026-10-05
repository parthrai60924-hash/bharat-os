"""Bharat OS security: password lock screen, lockout, audit log, file integrity check.
Only a salted PBKDF2 hash is stored. The password itself is never saved."""
import os, json, time, hashlib, secrets, datetime
import tkinter as tk
from tkinter import messagebox
from .paths import DATA_DIR

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEC_FILE = os.path.join(DATA_DIR, "security.json")
AUDIT = os.path.join(DATA_DIR, "audit.log")
MANIFEST = os.path.join(DATA_DIR, "integrity.json")
ITER, MAX_TRIES = 200_000, 5


def _hash(pw, salt): return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, ITER).hex()
def _load():
    try:
        with open(SEC_FILE, encoding="utf-8") as f: return json.load(f)
    except Exception: return {}
def _save(d):
    with open(SEC_FILE, "w", encoding="utf-8") as f: json.dump(d, f)
    try: os.chmod(SEC_FILE, 0o600)
    except Exception: pass


def audit(event):
    try:
        with open(AUDIT, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S}  {event}\n")
    except Exception: pass


def has_password(): return "hash" in _load()


def set_password(pw):
    if len(pw) < 8: return False, "Use at least 8 characters."
    salt = secrets.token_bytes(16)
    _save({"salt": salt.hex(), "hash": _hash(pw, salt), "fails": 0, "locked_until": 0})
    audit("password set"); return True, "Password saved."


def verify(pw):
    d = _load()
    if time.time() < d.get("locked_until", 0):
        return False, f"Locked. Try again in {int(d['locked_until'] - time.time())}s."
    ok = secrets.compare_digest(_hash(pw, bytes.fromhex(d["salt"])), d["hash"])
    if ok:
        d["fails"] = 0; _save(d); audit("login OK"); return True, ""
    d["fails"] = d.get("fails", 0) + 1
    if d["fails"] >= MAX_TRIES:                      # 30s, 60s, 120s ... up to 1 hour
        d["locked_until"] = time.time() + min(3600, 30 * 2 ** (d["fails"] - MAX_TRIES))
    _save(d); audit(f"login FAILED ({d['fails']})")
    return False, "Wrong password."


def _digest(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""): h.update(chunk)
    return h.hexdigest()


def _files():
    for r, _, fs in os.walk(BASE):
        for n in fs:
            if n.endswith(".py"): yield os.path.join(r, n)


def update_manifest():
    m = {os.path.relpath(p, BASE): _digest(p) for p in _files()}
    with open(MANIFEST, "w", encoding="utf-8") as f: json.dump(m, f, indent=1)
    audit("integrity manifest updated"); return len(m)


def verify_files():
    """Return list of changed/missing OS files since the last manifest."""
    try:
        with open(MANIFEST, encoding="utf-8") as f: m = json.load(f)
    except Exception: return None
    bad = []
    for rel, h in m.items():
        p = os.path.join(BASE, rel)
        if not os.path.exists(p) or _digest(p) != h: bad.append(rel)
    return bad


def require_login(root):
    """Blocks until the right password is entered. Returns False if user quits."""
    first = not has_password()
    result = {"ok": False}
    win = tk.Toplevel(root); win.title("Bharat OS - Secure Login")
    win.configure(bg="#101114"); win.geometry("420x360")
    win.protocol("WM_DELETE_WINDOW", win.destroy)
    win.transient(root); win.grab_set()
    tk.Label(win, text="BHARAT OS", fg="#FF9933", bg="#101114", font=("Arial", 22, "bold")).pack(pady=(28, 4))
    tk.Label(win, text="Create your password" if first else "Enter your password",
             fg="white", bg="#101114", font=("Arial", 12)).pack(pady=(0, 14))
    e1 = tk.Entry(win, show="•", font=("Arial", 14), justify="center"); e1.pack(ipady=5, padx=50, fill="x")
    e2 = None
    if first:
        e2 = tk.Entry(win, show="•", font=("Arial", 14), justify="center")
        e2.pack(ipady=5, padx=50, fill="x", pady=8)
        tk.Label(win, text="(type it again to confirm)", fg="#888", bg="#101114").pack()
    msg = tk.Label(win, text="", fg="#ff6b6b", bg="#101114", wraplength=340); msg.pack(pady=8)

    def go(_e=None):
        if first:
            if e1.get() != e2.get(): msg.config(text="Passwords do not match."); return
            ok, m = set_password(e1.get())
            if not ok: msg.config(text=m); return
        else:
            ok, m = verify(e1.get())
            if not ok: msg.config(text=m); e1.delete(0, "end"); return
        result["ok"] = True; win.destroy()

    tk.Button(win, text="Create & Enter" if first else "Unlock", command=go, bg="#138808",
              fg="white", relief="flat", font=("Arial", 12, "bold")).pack(ipadx=24, ipady=5, pady=6)
    win.bind("<Return>", go); e1.focus_set()
    root.wait_window(win)
    bad = verify_files() if result["ok"] else None
    if bad:
        messagebox.showwarning("Security", "These OS files changed since last check:\n\n" + "\n".join(bad[:10]))
    return result["ok"]
