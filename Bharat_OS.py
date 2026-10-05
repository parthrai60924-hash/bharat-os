"""
BHARAT OS  -  MyOS desktop + Nova Store (merged)
Atmanirbhar Bharat

Run:      python Bharat_OS.py
Needs:    Python 3.10+  (tkinter comes with Python)
Optional: pip install pillow     (for the wallpaper image + window logo)

Keep wp7231692.jpg (or india_background.jpg) in the SAME folder as this file.
It is used as the OS wallpaper and the Store background.

Install / Open inside Nova Store are simulated, Open launches the app's website.
"Continue with Google" is a LOCAL profile flow. It never asks for or stores
a real Google password.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json, os, re, hashlib, secrets, threading, webbrowser
import urllib.parse, urllib.request, colorsys, subprocess, platform
import datetime, math
from bharat import security, downloader, system_tools
from bharat.paths import DATA_DIR

try:
    from PIL import Image, ImageTk, ImageDraw, ImageEnhance
except Exception:
    Image = ImageTk = ImageDraw = ImageEnhance = None

# ============================================================
# PATHS / BRAND
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(DATA_DIR, "nova_store_data.json")
ICON_DIR = os.path.join(DATA_DIR, "icons")
WALLPAPERS = [os.path.join(BASE_DIR, n) for n in
              ("wp7231692.jpg", "india_background.jpg", "india_background.png")]

OS_NAME = "Bharat OS"
APP_VERSION = "4.0"

SAFFRON, GREEN, CHAKRA = "#FF9933", "#138808", "#1c2fd6"
QUOTE_HI = "Apna hunar, apni takneek, apna ujjwal digital bhavishya"
QUOTE_EN = ("Atmanirbhar Bharat — empowering Indian ideas, inspiring Indian "
            "innovation, and building a brighter digital future.")

# OS colours
BG, TASKBAR, WINDOW, BUTTON, TEXT, ACCENT = (
    "#101114", "#15171b", "#202228", "#292c33", "#ffffff", "#4f8cff")

root = None          # Tk root (the OS)
STORE = None         # Nova Store window
ICON_IMG = None      # window / taskbar icon


# ============================================================
# LOGO  (Ashoka Chakra, drawn in code so it is always sharp)
# ============================================================
def draw_chakra(c, cx, cy, r, color=CHAKRA):
    c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color,
                  width=max(2, r * 0.11))
    hub = r * 0.13
    c.create_oval(cx - hub, cy - hub, cx + hub, cy + hub, fill=color, outline=color)
    for i in range(24):
        a = math.radians(i * 15)
        c.create_line(cx + math.cos(a) * hub, cy + math.sin(a) * hub,
                      cx + math.cos(a) * r * 0.86, cy + math.sin(a) * r * 0.86,
                      fill=color, width=max(1, r * 0.045))


def logo_canvas(parent, size, bg):
    c = tk.Canvas(parent, width=size, height=size, bg=bg, highlightthickness=0)
    c.create_oval(1, 1, size - 1, size - 1, fill="white", outline=SAFFRON,
                  width=max(2, size * 0.07))
    draw_chakra(c, size / 2, size / 2, size * 0.33)
    return c


def make_icon_image():
    """Chakra icon for the window title bar / taskbar (needs Pillow)."""
    if not Image:
        return None
    s = 128
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((3, 3, s - 3, s - 3), fill="white", outline=SAFFRON, width=8)
    c, r = s / 2, s * 0.33
    d.ellipse((c - r, c - r, c + r, c + r), outline=CHAKRA, width=6)
    d.ellipse((c - 7, c - 7, c + 7, c + 7), fill=CHAKRA)
    for i in range(24):
        a = math.radians(i * 15)
        d.line((c + math.cos(a) * 8, c + math.sin(a) * 8,
                c + math.cos(a) * r * .88, c + math.sin(a) * r * .88),
               fill=CHAKRA, width=2)
    return ImageTk.PhotoImage(im)


# ============================================================
# APP CATALOG  (290+ apps)
# ============================================================
CATALOG = """
Arattai|Communication|Made-in-India messenger from Zoho with chats and calls
Sandes|Communication|Government of India instant messaging app
WhatsApp|Communication|Chat, voice and video calls with friends and family
Telegram|Communication|Fast cloud-based messaging with channels and groups
Signal|Communication|Privacy-focused encrypted messenger
Truecaller|Communication|Caller ID, spam blocking and call management
JioMeet|Communication|Video meetings and conferencing
Zoho Cliq|Communication|Team chat for work
Google Meet|Communication|Video calls and meetings
Skype|Communication|Calls and chat across devices
Zoom|Communication|Video meetings and webinars
Discord|Communication|Voice, video and text communities
Slack|Communication|Team messaging and collaboration
Microsoft Teams|Communication|Chat, meetings and collaboration
Zoho Meeting|Communication|Online meetings and webinars
JioSphere|Browsers|Indian browser by Jio with built-in tools
Epic Privacy Browser|Browsers|Private browser with tracker blocking
Google Chrome|Browsers|Fast popular web browser
Mozilla Firefox|Browsers|Open-source browser
Brave|Browsers|Browser with ad and tracker blocking
Microsoft Edge|Browsers|Microsoft browser with sync and reading tools
Samsung Internet|Browsers|Browser with add-ons and secure mode
DuckDuckGo|Browsers|Private search and browsing
Zoho Mail|Email|Ad-free business and personal email from India
Gmail|Email|Google email with smart inbox
Outlook|Email|Email, calendar and contacts
Proton Mail|Email|Encrypted email
Yahoo Mail|Email|Email with large storage
Rediffmail|Email|Indian email service
Titan Mail|Email|Business email for small companies
PhonePe|Payments|UPI payments, recharges and bill pay
Google Pay|Payments|UPI payments and rewards
Paytm|Payments|UPI, wallet, bills and tickets
BHIM|Payments|UPI payment app by NPCI
Amazon Pay|Payments|UPI and wallet
CRED|Payments|Credit card bill payments
MobiKwik|Payments|Wallet, UPI and bills
Freecharge|Payments|Recharge and UPI payments
Navi|Payments|UPI and financial services
Airtel Thanks|Payments|Recharges, payments and offers
JioFinance|Payments|Payments and money services
My FASTag|Payments|FASTag balance and recharge
Flipkart|Shopping|Indian e-commerce marketplace
Amazon Shopping|Shopping|Shop millions of products
Myntra|Shopping|Fashion and lifestyle
Meesho|Shopping|Shopping and reselling
Ajio|Shopping|Fashion brands and trends
Nykaa|Shopping|Beauty and wellness products
JioMart|Shopping|Grocery and daily essentials
BigBasket|Shopping|Online grocery delivery
Blinkit|Shopping|Groceries delivered quickly
Zepto|Shopping|Quick grocery delivery
Swiggy Instamart|Shopping|Quick commerce
Tata Neu|Shopping|Tata group super app
Snapdeal|Shopping|Value shopping marketplace
FirstCry|Shopping|Baby and kids products
Lenskart|Shopping|Eyeglasses and sunglasses
Purplle|Shopping|Beauty and personal care
Urban Company|Shopping|Home services
Croma|Shopping|Electronics and appliances
ONDC Buyer|Shopping|Open network for digital commerce
Swiggy|Food|Food delivery and dining
Zomato|Food|Food delivery and restaurant discovery
EatSure|Food|Multi-brand food ordering
Domino's India|Food|Pizza ordering
magicpin|Food|Food offers and cashback
District|Food|Dining, movies and events
IRCTC Rail Connect|Travel|Book Indian Railways tickets
Ola|Travel|Cab and auto rides
Uber|Travel|Ride booking
Rapido|Travel|Bike taxi, auto and cab rides
Namma Yatri|Travel|Auto and cab rides
redBus|Travel|Bus ticket booking
MakeMyTrip|Travel|Flights, hotels and holidays
Goibibo|Travel|Flights, hotels and buses
ixigo|Travel|Trains, flights and travel
Cleartrip|Travel|Flights and hotels
EaseMyTrip|Travel|Flights and hotel deals
Yatra|Travel|Travel booking
OYO|Travel|Hotel booking
AbhiBus|Travel|Bus tickets
Google Maps|Travel|Maps and navigation
Mappls MapmyIndia|Travel|Indian maps and navigation
UTS on Mobile|Travel|Railway ticketing
Delhi Metro Sarthi|Travel|Delhi Metro information
JioHotstar|Entertainment|Movies, shows and live cricket
Netflix|Entertainment|Streaming shows and films
Prime Video|Entertainment|Amazon streaming service
SonyLIV|Entertainment|TV shows, movies and sports
ZEE5|Entertainment|Indian regional shows and movies
YouTube|Entertainment|Videos, shorts and live streams
MX Player|Entertainment|Video player and streaming
Aha|Entertainment|Telugu and Tamil streaming
Sun NXT|Entertainment|South Indian entertainment
BookMyShow|Entertainment|Movie and event tickets
Hoichoi|Entertainment|Bengali streaming
Eros Now|Entertainment|Bollywood entertainment
Twitch|Entertainment|Live streaming for gamers
JioSaavn|Music|Indian music streaming
Gaana|Music|Bollywood and regional music
Spotify|Music|Music and podcasts
Wynk Music|Music|Music streaming
YouTube Music|Music|Music and videos
Apple Music|Music|Streaming music
Hungama Music|Music|Music and videos
Amazon Music|Music|Music and podcasts
Kuku FM|Music|Audio stories and podcasts
PhysicsWallah|Education|Exam preparation and classes
Unacademy|Education|Live classes
Vedantu|Education|Online tutoring
Khan Academy|Education|Free learning
DIKSHA|Education|Government school learning platform
SWAYAM|Education|Free online courses
NPTEL|Education|Engineering and science courses
Duolingo|Education|Language learning
Testbook|Education|Government exam preparation
Adda247|Education|Bank, SSC and state exam preparation
Coursera|Education|University courses and certificates
Google Classroom|Education|Assignments and class management
Doubtnut|Education|Question solving and learning
BYJU'S|Education|Learning app for school students
Dailyhunt|News|News in Indian languages
Inshorts|News|News in short format
Times of India|News|Indian news and updates
Hindustan Times|News|National and world news
The Hindu|News|News and analysis
NDTV|News|Live news and videos
India Today|News|News and current affairs
The Indian Express|News|News and explained stories
Aaj Tak|News|Hindi live news
Google News|News|Personalized news feed
DigiLocker|Government|Store and share official documents
UMANG|Government|Government services in one app
mAadhaar|Government|Aadhaar services
Aarogya Setu|Government|Government health services
CoWIN|Government|Vaccination records and certificates
MyGov|Government|Citizen engagement platform
Income Tax India|Government|Income tax services
GST Suvidha|Government|GST services
mParivahan|Government|Vehicle and licence details
DigiYatra|Government|Paperless airport entry
e-Shram|Government|Worker registration
PM-KISAN|Government|Farmer scheme information
mPassport Seva|Government|Passport services
Bhashini|Government|Translation and speech in Indian languages
Kisan Suvidha|Government|Weather, market prices and farm advice
Zoho Writer|Productivity|Word processor
Zoho Notebook|Productivity|Notes and media
Zoho Sheet|Productivity|Spreadsheets and charts
Zoho Books|Productivity|Accounting for small businesses
Zoho Projects|Productivity|Project management
Google Drive|Productivity|Cloud storage and sharing
Microsoft 365|Productivity|Office applications
WPS Office|Productivity|Office suite
Notion|Productivity|Notes and planning
Todoist|Productivity|Tasks and reminders
Trello|Productivity|Boards for tasks and teams
Google Calendar|Productivity|Calendar and events
Google Keep|Productivity|Notes and checklists
Evernote|Productivity|Notes and web clipper
Files by Google|Productivity|File management and cleanup
ShareChat|Social|Indian regional-language social network
Instagram|Social|Photos, reels and stories
Facebook|Social|Social network
X|Social|Posts and conversations
Twitter|Social|Social networking platform
LinkedIn|Social|Professional networking
Snapchat|Social|Camera, chat and stories
Pinterest|Social|Ideas and inspiration
Pratilipi|Social|Indian-language stories
Threads|Social|Text conversations from Instagram
Reddit|Social|Communities and discussions
Quora|Social|Questions and answers
Tumblr|Social|Blogs and creative communities
Bluesky|Social|Open social network
Moj|Social|Short videos made in India
Josh|Social|Short videos and creators
Practo|Health|Doctor booking and consultations
Tata 1mg|Health|Medicines and lab services
PharmEasy|Health|Medicine delivery
Apollo 24|Health|Doctor consultations
HealthifyMe|Health|Fitness and nutrition
cult.fit|Health|Workouts and fitness
Google Fit|Health|Activity and heart points
Headspace|Health|Meditation and sleep
Calm|Health|Sleep, meditation and relaxation
Medibuddy|Health|Doctor and health checkups
Zerodha Kite|Finance|Stock trading platform
Groww|Finance|Stocks and mutual funds
Upstox|Finance|Trading and investing
Angel One|Finance|Stocks and investments
INDmoney|Finance|Track and invest
ET Money|Finance|Mutual funds and money tracking
Paytm Money|Finance|Mutual funds and stocks
Policybazaar|Finance|Insurance marketplace
Dhan|Finance|Trading tools
HDFC Bank MobileBanking|Finance|HDFC Bank mobile banking
SBI YONO|Finance|SBI banking and services
ICICI iMobile Pay|Finance|ICICI banking
Axis Mobile|Finance|Axis Bank mobile banking
Kotak Mobile Banking|Finance|Kotak banking
Ludo King|Games|Classic board game
Carrom Pool|Games|Multiplayer carrom
BGMI|Games|Battle royale game
Free Fire MAX|Games|Battle royale
Subway Surfers|Games|Endless runner
Chess.com|Games|Play and learn chess
Lichess|Games|Free open-source chess
Candy Crush Saga|Games|Match-three puzzle
Real Cricket|Games|Cricket game
World Cricket Championship|Games|Cricket simulation
Temple Run 2|Games|Endless running adventure
Hill Climb Racing|Games|Physics driving game
Minecraft|Games|Build and explore blocky worlds
Roblox|Games|Play millions of user-made games
Clash of Clans|Games|Build a village and battle
Call of Duty Mobile|Games|Shooter on mobile
Asphalt 9|Games|Arcade racing
Stumble Guys|Games|Multiplayer party knockout
8 Ball Pool|Games|Online pool
Sudoku|Games|Classic number puzzle
Angry Birds 2|Games|Slingshot puzzle fun
Pokemon GO|Games|Explore the real world and catch creatures
IMD Mausam|Utilities|Weather forecasts from IMD
Google Translate|Utilities|Translate between 100+ languages
Google Lens|Utilities|Search what you see
Adobe Acrobat Reader|Utilities|View and sign PDFs
CamScanner|Utilities|Scan documents to PDF
VLC|Utilities|Plays almost any media file
Bitwarden|Utilities|Open-source password manager
Speedtest|Utilities|Test your internet speed
Google Authenticator|Utilities|Two-step verification codes
SHAREit|Utilities|Fast file sharing
Google Photos|Photo & Video|Backup and organise photos
Snapseed|Photo & Video|Powerful photo editor
Canva|Photo & Video|Design posters, reels and more
PicsArt|Photo & Video|Photo and video editor
InShot|Photo & Video|Video editor and maker
Adobe Lightroom|Photo & Video|Pro photo editing
VN Video Editor|Photo & Video|Free video editor
"""

CAT_EMOJI = {
    "Communication": "💬", "Browsers": "🌐", "Email": "✉", "Payments": "💳",
    "Shopping": "🛒", "Food": "🍔", "Travel": "🚕", "Entertainment": "🎬",
    "Music": "🎵", "Education": "📚", "News": "📰", "Government": "🏛",
    "Productivity": "💼", "Social": "👥", "Health": "❤", "Finance": "💰",
    "Games": "🎮", "Utilities": "🧰", "Photo & Video": "📷",
}
KIDS_HIDDEN = {"Games", "Social"}

DOMAINS = {
    "WhatsApp": "whatsapp.com", "Telegram": "telegram.org", "Signal": "signal.org",
    "Truecaller": "truecaller.com", "Zoom": "zoom.us", "Discord": "discord.com",
    "Google Meet": "meet.google.com", "Google Chrome": "google.com",
    "Mozilla Firefox": "mozilla.org", "Brave": "brave.com",
    "Microsoft Edge": "microsoft.com", "DuckDuckGo": "duckduckgo.com",
    "Gmail": "gmail.com", "Outlook": "outlook.com", "PhonePe": "phonepe.com",
    "Google Pay": "pay.google.com", "Paytm": "paytm.com", "BHIM": "bhimupi.org.in",
    "Amazon Shopping": "amazon.in", "Flipkart": "flipkart.com", "Myntra": "myntra.com",
    "Meesho": "meesho.com", "Nykaa": "nykaa.com", "JioMart": "jiomart.com",
    "Swiggy": "swiggy.com", "Zomato": "zomato.com", "Uber": "uber.com",
    "Ola": "olacabs.com", "Rapido": "rapido.bike", "Netflix": "netflix.com",
    "YouTube": "youtube.com", "Spotify": "spotify.com", "JioSaavn": "jiosaavn.com",
    "Google Maps": "maps.google.com", "Instagram": "instagram.com",
    "Facebook": "facebook.com", "X": "x.com", "Twitter": "twitter.com",
    "LinkedIn": "linkedin.com", "Snapchat": "snapchat.com",
    "Pinterest": "pinterest.com", "Threads": "threads.net", "Reddit": "reddit.com",
    "Quora": "quora.com", "Tumblr": "tumblr.com", "Bluesky": "bsky.app",
    "ShareChat": "sharechat.com", "Moj": "mojapp.in", "Josh": "myjosh.in",
    "DigiLocker": "digilocker.gov.in", "UMANG": "umang.gov.in", "MyGov": "mygov.in",
    "Bhashini": "bhashini.gov.in", "Google Drive": "drive.google.com",
    "Microsoft 365": "microsoft.com", "Notion": "notion.so", "Slack": "slack.com",
    "Trello": "trello.com", "Canva": "canva.com", "Google Photos": "photos.google.com",
    "Google Translate": "translate.google.com", "Google Calendar": "calendar.google.com",
    "Google Keep": "keep.google.com", "PhysicsWallah": "pw.live",
    "Unacademy": "unacademy.com", "Coursera": "coursera.org",
    "Khan Academy": "khanacademy.org", "Zerodha Kite": "zerodha.com",
    "Groww": "groww.in", "Upstox": "upstox.com", "SBI YONO": "sbi.co.in",
    "ICICI iMobile Pay": "icicibank.com", "Ludo King": "ludoking.com",
    "Chess.com": "chess.com", "Lichess": "lichess.org", "Twitch": "twitch.tv",
    "Minecraft": "minecraft.net", "Roblox": "roblox.com", "Zoho Mail": "zoho.com/mail",
    "IRCTC Rail Connect": "irctc.co.in", "MakeMyTrip": "makemytrip.com",
    "BookMyShow": "bookmyshow.com", "Inshorts": "inshorts.com",
}

THEMES = {
    "Light": dict(bg="#f8faf9", side="#eef3f1", card="#ffffff", text="#17221d",
                  muted="#66736c", accent="#138a52", border="#d8e1dc", input="#edf2ef",
                  sel="#d5eee2", btn2="#e5ebe8", blue="#1976d2", orange="#f59e0b",
                  green="#138a52"),
    "Dark": dict(bg="#101512", side="#171e1a", card="#1b241f", text="#edf7f0",
                 muted="#9daaa2", accent="#25a965", border="#334139", input="#222c26",
                 sel="#234332", btn2="#2a342e", blue="#4b9cf5", orange="#f6ad2e",
                 green="#25a965"),
}

DEFAULTS = dict(theme="Light", columns=3, sort="Name", ratings=True, auto_update=True,
                wifi_only=True, notifications=True, require_signin=False,
                remember=True, kids=False, pin_salt="", pin_hash="")


# ============================================================
# HELPERS
# ============================================================
def safe_name(name):
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def hash_pw(password, salt_hex):
    return hashlib.pbkdf2_hmac("sha256", password.encode(),
                               bytes.fromhex(salt_hex), 120000).hex()


def parse_catalog():
    apps, seen = [], set()
    for line in CATALOG.strip().splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 3 or parts[0] in seen:
            continue
        seen.add(parts[0])
        name, cat, desc = parts
        h = sum(ord(c) * (i + 1) for i, c in enumerate(name))
        r, g, b = colorsys.hsv_to_rgb((h % 360) / 360, 0.55, 0.78)
        apps.append(dict(name=name, category=cat, desc=desc,
                         rating=round(3.9 + (h % 10) / 11, 1),
                         color="#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))))
    return sorted(apps, key=lambda a: a["name"].lower())


APPS = parse_catalog()
CATEGORIES = sorted({a["category"] for a in APPS})


LOG_FILE = os.path.join(DATA_DIR, "Bharat_OS_error.log")


def log_error(where=""):
    """Write the current exception to Bharat_OS_error.log (and the console)."""
    import traceback
    text = traceback.format_exc()
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"--- {datetime.datetime.now()}  [{where}]\n{text}\n")
    except Exception:
        pass
    print(text)
    return text


def open_web(domain_or_url):
    url = domain_or_url if domain_or_url.startswith("http") else "https://" + domain_or_url
    webbrowser.open(url)


# ---------- OS hooks used by Nova Store ----------
def os_install(app):
    """Hook: connect to a real package manager here."""
    return True


def os_launch(app):
    """Open the app's website. Apps with no website show a message."""
    domain = DOMAINS.get(app["name"])
    if domain:
        open_web(domain)
    else:
        open_web("https://www.google.com/search?q=" +
                 urllib.parse.quote(app["name"] + " official site"))


# ============================================================
# NOVA STORE  (a window inside Bharat OS)
# ============================================================
class Store(tk.Toplevel):

    def __init__(self, master):
        super().__init__(master)
        self.title("Nova Store — Made for India")
        self.geometry("1180x740")
        self.minsize(960, 620)
        if ICON_IMG:
            try:
                self.iconphoto(False, ICON_IMG)
            except Exception:
                pass

        self.data = self.load_data()
        self.settings = {**DEFAULTS, **self.data.get("settings", {})}
        self.user = self.data.get("current") if self.settings["remember"] else None
        if self.user not in self.data.get("accounts", {}):
            self.user = None

        self.installed = set()
        self.load_installed()
        self.progress, self.btns, self.bars = {}, {}, {}
        self.nav, self.page, self.detail_app = "All Apps", "list", None
        self.img_cache, self.scrollers = {}, []
        self._gen = 0
        self._silent = False
        self.nav_buttons = {}
        self.bg_photo = None

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.on_search())

        self.apply_theme()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # smooth mouse wheel (Windows/Mac + Linux)
        self.bind("<MouseWheel>", self.on_wheel)
        self.bind("<Button-4>", self.on_wheel)
        self.bind("<Button-5>", self.on_wheel)

        self.build_layout()
        self.show_page()
        if self.settings["require_signin"] and not self.user:
            self.after(500, self.login_dialog)

    # ---------------- small widget helpers ----------------
    def lbl(self, parent, text, size=10, bold=False, fg="text", bg="bg", **kw):
        T = self.T
        return tk.Label(parent, text=text, fg=T.get(fg, fg), bg=T.get(bg, bg),
                        font=("Segoe UI", size, "bold" if bold else "normal"), **kw)

    def btn(self, parent, text, cmd, bg="btn2", fg="text", size=10, bold=False, **kw):
        T = self.T
        return tk.Button(parent, text=text, command=cmd, relief="flat", cursor="hand2",
                         bg=T.get(bg, bg), fg=T.get(fg, fg), activebackground=T["sel"],
                         activeforeground=T["text"],
                         font=("Segoe UI", size, "bold" if bold else "normal"), **kw)

    def entry(self, parent, var, show="", size=11):
        T = self.T
        return tk.Entry(parent, textvariable=var, show=show, font=("Segoe UI", size),
                        bg=T["input"], fg=T["text"], insertbackground=T["text"],
                        relief="flat")

    def pill(self, parent, text, command, danger=False):
        return self.btn(parent, text, command,
                        bg="#d93025" if danger else "btn2",
                        fg="white" if danger else "text",
                        size=9, bold=True, padx=16, pady=6)

    # ---------------- data ----------------
    def load_data(self):
        default = {"accounts": {}, "guest_installed": [], "current": None, "settings": {}}
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                default.update(loaded)
        except Exception:
            pass
        return default

    def save_data(self):
        if self.user in self.data["accounts"]:
            self.data["accounts"][self.user]["installed"] = sorted(self.installed)
        else:
            self.data["guest_installed"] = sorted(self.installed)
        self.data["current"] = self.user if self.settings["remember"] else None
        self.data["settings"] = self.settings
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception:
            pass

    def load_installed(self):
        if self.user in self.data["accounts"]:
            self.installed = set(self.data["accounts"][self.user].get("installed", []))
        else:
            self.installed = set(self.data.get("guest_installed", []))

    def on_close(self):
        global STORE
        self.save_data()
        STORE = None
        self.destroy()

    # ---------------- theme ----------------
    def apply_theme(self):
        self.T = THEMES.get(self.settings["theme"], THEMES["Light"])
        self.configure(bg=self.T["bg"])

    def rebuild(self):
        for w in self.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass
        self.scrollers, self.img_cache = [], {}
        self.apply_theme()
        self.build_layout()
        self.show_page()

    # ---------------- accounts ----------------
    def sign_up(self, username, password):
        if not re.fullmatch(r"[a-z0-9_.]{3,30}", username):
            return False, "Username: 3-30 letters, numbers, _ or ."
        if len(password) < 4:
            return False, "Password must be at least 4 characters."
        if username in self.data["accounts"]:
            return False, "That username already exists."
        salt = secrets.token_hex(8)
        self.data["accounts"][username] = {"salt": salt, "hash": hash_pw(password, salt),
                                           "installed": []}
        return True, ""

    def sign_in(self, username, password):
        acc = self.data["accounts"].get(username)
        if not acc:
            return False, "Account not found."
        if hash_pw(password, acc["salt"]) != acc["hash"]:
            return False, "Wrong username or password."
        return True, ""

    def finish_sign_in(self, username):
        self.save_data()
        self.user = username
        self.load_installed()
        self.save_data()
        self.rebuild()
        self.toast(f"Signed in as {username}")

    def sign_out(self):
        self.save_data()
        self.user = None
        self.load_installed()
        self.save_data()
        self.rebuild()

    # ---------------- login dialog ----------------
    def login_dialog(self):
        T = self.T
        win = tk.Toplevel(self)
        win.title("Sign in to Nova Store")
        win.geometry("430x600")
        win.resizable(False, False)
        win.configure(bg=T["bg"])
        win.transient(self)

        logo_canvas(win, 90, T["bg"]).pack(pady=(24, 4))
        self.lbl(win, "Nova Store", 21, True).pack()
        self.lbl(win, "Bharat • Made for India", 10, True, "accent").pack(pady=(2, 2))
        self.lbl(win, "One account for all your apps", 10, fg="muted").pack(pady=(0, 14))

        tk.Button(win, text="  G   Continue with Google", relief="flat", bg="white",
                  fg="#202124", font=("Segoe UI", 10, "bold"), cursor="hand2",
                  command=lambda: self.google_dialog(win)).pack(fill="x", padx=40, ipady=7)
        self.lbl(win, "Local profile • your Google password is never requested",
                 8, fg="muted").pack(pady=(5, 10))
        ttk.Separator(win, orient="horizontal").pack(fill="x", padx=40, pady=4)

        u, p = tk.StringVar(), tk.StringVar()
        for label, var, show in (("Username", u, ""), ("Password", p, "•")):
            self.lbl(win, label, 9, fg="muted", anchor="w").pack(fill="x", padx=40, pady=(7, 2))
            self.entry(win, var, show).pack(fill="x", padx=40, ipady=7)

        remember = tk.BooleanVar(value=self.settings["remember"])
        tk.Checkbutton(win, text="Keep me signed in", variable=remember, bg=T["bg"],
                       fg=T["text"], selectcolor=T["input"], activebackground=T["bg"],
                       activeforeground=T["text"]).pack(anchor="w", padx=36, pady=5)
        error = self.lbl(win, "", 9, fg="#d93025")
        error.pack()

        def go(mode):
            name = u.get().strip().lower()
            ok, msg = (self.sign_up if mode == "up" else self.sign_in)(name, p.get())
            if ok:
                self.settings["remember"] = remember.get()
                win.destroy()
                self.finish_sign_in(name)
            else:
                error.configure(text=msg)

        self.btn(win, "Sign in", lambda: go("in"), "accent", "white", bold=True
                 ).pack(fill="x", padx=40, pady=(5, 4), ipady=6)
        self.btn(win, "Create local account", lambda: go("up")
                 ).pack(fill="x", padx=40, pady=3, ipady=6)
        self.btn(win, "Continue as guest", win.destroy, "bg", "blue"
                 ).pack(pady=8)
        try:
            win.wait_visibility()
            win.grab_set()
        except Exception:
            pass

    def google_dialog(self, parent):
        T = self.T
        win = tk.Toplevel(parent)
        win.title("Google Account")
        win.geometry("390x300")
        win.configure(bg=T["bg"])
        win.transient(parent)
        self.lbl(win, "Google Account", 19, True).pack(pady=(30, 8))
        self.lbl(win, "Enter your email to create a local Nova profile.", 9,
                 fg="muted").pack()
        email = tk.StringVar()
        self.entry(win, email).pack(fill="x", padx=35, pady=20, ipady=8)

        def go():
            value = email.get().strip().lower()
            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
                messagebox.showerror("Google Account", "Please enter a valid email.",
                                     parent=win)
                return
            base = safe_name(value.split("@")[0])[:25] or "google_user"
            username, n = base, 1
            while username in self.data["accounts"]:
                username, n = f"{base}{n}", n + 1
            salt = secrets.token_hex(8)
            self.data["accounts"][username] = {
                "salt": salt, "hash": hash_pw(secrets.token_hex(16), salt), "installed": []}
            win.destroy()
            parent.destroy()
            self.finish_sign_in(username)
            self.toast(f"Google profile connected: {value}")

        self.btn(win, "Continue", go, "accent", "white", bold=True
                 ).pack(fill="x", padx=35, ipady=7)

    # ---------------- layout ----------------
    def build_layout(self):
        T = self.T
        self.nav_buttons = {}

        top = tk.Frame(self, bg=T["bg"])
        top.pack(fill="x")
        brand = tk.Frame(top, bg=T["bg"])
        brand.pack(side="left", padx=(18, 10), pady=10)
        logo_canvas(brand, 40, T["bg"]).pack(side="left")
        self.lbl(brand, "Nova Store", 17, True).pack(side="left", padx=8)

        # right side first so the search box takes the remaining width
        self.avatar = self.btn(top, self.user[0].upper() if self.user else "G",
                               self.account_menu, "accent", "white", 11, True, width=3)
        self.avatar.pack(side="right", padx=(5, 18))
        self.lbl(top, self.user or "Guest", 9, fg="muted").pack(side="right")
        self.lbl(top, "🇮🇳 India", 10, True, "accent").pack(side="right", padx=10)

        sb = tk.Frame(top, bg=T["input"])
        sb.pack(side="left", fill="x", expand=True, padx=15, pady=10)
        self.lbl(sb, "🔍", 11, fg="muted", bg="input").pack(side="left", padx=(10, 5))
        self.entry(sb, self.search_var).pack(side="left", fill="x", expand=True, ipady=8)

        # tricolour line
        tri = tk.Frame(self, height=3)
        tri.pack(fill="x")
        for col in (SAFFRON, "white", GREEN):
            tk.Frame(tri, bg=col, height=3).pack(side="left", fill="x", expand=True)

        body = tk.Frame(self, bg=T["bg"])
        body.pack(fill="both", expand=True)
        side = tk.Frame(body, bg=T["side"], width=240)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        # pinned bottom buttons (packed first so they never get pushed out)
        bottom = tk.Frame(side, bg=T["side"])
        bottom.pack(side="bottom", fill="x")
        tk.Frame(bottom, bg=T["border"], height=1).pack(fill="x", pady=4)
        self.nav_button(bottom, "Account", "👤  Account")
        self.nav_button(bottom, "Settings", "⚙  Settings")

        canvas = tk.Canvas(side, bg=T["side"], highlightthickness=0, yscrollincrement=18)
        canvas.pack(side="top", fill="both", expand=True)
        inner = tk.Frame(canvas, bg=T["side"])
        wid = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(wid, width=e.width))
        self.scrollers.append(canvas)

        kids = self.settings["kids"]
        cats = [c for c in CATEGORIES if not (kids and c in KIDS_HIDDEN)]
        total = len([a for a in APPS if not (kids and a["category"] in KIDS_HIDDEN)])
        self.nav_button(inner, "All Apps", f"🏠  All Apps  ({total})")
        self.nav_button(inner, "Installed", f"📦  Installed  ({len(self.installed)})")
        self.nav_button(inner, "Updates", "⬆  Updates")
        self.lbl(inner, "CATEGORIES", 8, True, "muted", "side", anchor="w"
                 ).pack(fill="x", padx=18, pady=(12, 3))
        for c in cats:
            n = sum(a["category"] == c for a in APPS)
            self.nav_button(inner, c, f"{CAT_EMOJI.get(c, '')}  {c}  ({n})")
        # extra space so the LAST category is never cut off
        tk.Frame(inner, bg=T["side"], height=70).pack(fill="x")

        self.content = tk.Frame(body, bg=T["bg"])
        self.content.pack(side="left", fill="both", expand=True)

    def nav_button(self, parent, key, label):
        T = self.T
        b = tk.Button(parent, text=label, anchor="w", relief="flat", bg=T["side"],
                      fg=T["text"], font=("Segoe UI", 10), padx=14, pady=6,
                      activebackground=T["sel"], activeforeground=T["text"],
                      cursor="hand2", command=lambda k=key: self.go(k))
        b.pack(fill="x")
        self.nav_buttons[key] = b

    def update_nav(self):
        for key, b in self.nav_buttons.items():
            try:
                b.configure(bg=self.T["sel"] if key == self.nav else self.T["side"])
            except tk.TclError:
                pass

    # ---------------- scrolling ----------------
    def scroll_area(self, bg):
        canvas = tk.Canvas(self.content, bg=bg, highlightthickness=0, yscrollincrement=18)
        sb = ttk.Scrollbar(self.content, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=bg)
        wid = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(wid, width=e.width))
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.scrollers = [s for s in self.scrollers if s.winfo_exists()]
        self.scrollers.append(canvas)
        return inner

    def on_wheel(self, event):
        try:
            w = self.winfo_containing(event.x_root, event.y_root)
        except Exception:
            return
        if getattr(event, "num", 0) == 4:
            d = -1
        elif getattr(event, "num", 0) == 5:
            d = 1
        else:
            d = -1 if event.delta > 0 else 1
        while w is not None:
            if w in self.scrollers:
                self.smooth(w, d)
                return
            w = w.master

    def smooth(self, w, d, steps=5):
        """Eased scroll: several small steps instead of one jump."""
        if steps <= 0:
            return
        try:
            w.yview_scroll(d, "units")
            self.after(10, lambda: self.smooth(w, d, steps - 1))
        except tk.TclError:
            pass

    # ---------------- misc ----------------
    def clear_content(self):
        self._gen += 1           # cancels any card batches still rendering
        for w in self.content.winfo_children():
            w.destroy()
        self.btns, self.bars = {}, {}
        self.update_nav()

    def toast(self, text):
        t = tk.Label(self, text=text, bg="#222", fg="white", font=("Segoe UI", 10),
                     padx=18, pady=10)
        t.place(relx=1, rely=1, x=-20, y=-20, anchor="se")
        self.after(2600, lambda: t.destroy() if t.winfo_exists() else None)

    def account_menu(self):
        m = tk.Menu(self, tearoff=0)
        m.add_command(label=f"Signed in as {self.user}" if self.user else "Guest",
                      state="disabled")
        m.add_separator()
        if self.user:
            m.add_command(label="Manage account", command=lambda: self.go("Account"))
            m.add_command(label="Sign out", command=self.sign_out)
        else:
            m.add_command(label="Sign in / Create account", command=self.login_dialog)
        m.add_command(label="Settings", command=lambda: self.go("Settings"))
        m.tk_popup(self.avatar.winfo_rootx() - 160,
                   self.avatar.winfo_rooty() + self.avatar.winfo_height())

    # ---------------- navigation ----------------
    def set_search(self, text):
        self._silent = True
        self.search_var.set(text)
        self._silent = False

    def on_search(self):
        if self._silent:
            return
        if self.page != "list":
            self.page, self.detail_app = "list", None
            if self.nav in ("Settings", "Account", "Updates"):
                self.nav = "All Apps"
        self.show_list()

    def go(self, key):
        self.set_search("")
        self.nav, self.detail_app = key, None
        self.page = {"Settings": "settings", "Account": "account",
                     "Updates": "updates"}.get(key, "list")
        self.show_page()

    def show_page(self):
        {"list": self.show_list,
         "detail": lambda: self.show_detail(self.detail_app),
         "settings": self.show_settings, "account": self.show_account,
         "updates": self.show_updates}[self.page]()

    # ---------------- icons ----------------
    def get_image(self, app, size):
        key = (app["name"], size)
        if key in self.img_cache:
            return self.img_cache[key]
        path = os.path.join(ICON_DIR, safe_name(app["name"]) + ".png")
        image = None
        if os.path.isfile(path):
            try:
                if Image:
                    im = Image.open(path).convert("RGBA")
                    t = max(20, size - int(size * 0.20))
                    image = ImageTk.PhotoImage(im.resize((t, t), Image.LANCZOS))
                else:
                    image = tk.PhotoImage(file=path)
            except Exception:
                image = None
        self.img_cache[key] = image
        return image

    def round_rect(self, c, x1, y1, x2, y2, r, **kw):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return c.create_polygon(pts, smooth=True, **kw)

    def icon_widget(self, parent, app, size, bg):
        c = tk.Canvas(parent, width=size, height=size, bg=bg, highlightthickness=0)
        img = self.get_image(app, size)
        if img:
            self.round_rect(c, 2, 2, size - 2, size - 2, size * .2, fill="white",
                            outline=self.T["border"])
            c.create_image(size // 2, size // 2, image=img)
            c.image = img
        else:
            self.round_rect(c, 2, 2, size - 2, size - 2, size * .2, fill=app["color"],
                            outline="")
            c.create_text(size / 2, size / 2, text=app["name"][0].upper(), fill="white",
                          font=("Segoe UI", int(size * .40), "bold"))
        return c

    # ---------------- filtering ----------------
    def filtered(self):
        apps = APPS
        if self.settings["kids"]:
            apps = [a for a in apps if a["category"] not in KIDS_HIDDEN]
        if self.nav == "Installed":
            apps = [a for a in apps if a["name"] in self.installed]
        elif self.nav in CATEGORIES:
            apps = [a for a in apps if a["category"] == self.nav]
        q = self.search_var.get().strip().lower()
        if q:
            apps = [a for a in apps if q in a["name"].lower() or q in a["desc"].lower()
                    or q in a["category"].lower()]
        if self.settings["sort"] == "Rating":
            apps = sorted(apps, key=lambda a: (-a["rating"], a["name"].lower()))
        return apps

    # ---------------- list view ----------------
    def show_list(self):
        self.page, self.detail_app = "list", None
        self.clear_content()
        T = self.T
        apps = self.filtered()
        inner = self.scroll_area(T["bg"])
        q = self.search_var.get().strip()
        title = f'Search results for "{q}"' if q else self.nav

        header = tk.Frame(inner, bg=T["bg"])
        header.pack(fill="x", padx=25, pady=(20, 0))
        self.lbl(header, title, 19, True).pack(anchor="w")
        extra = "  •  Parental controls ON" if self.settings["kids"] else ""
        self.lbl(header, f"{len(apps)} apps{extra}", 10, fg="muted"
                 ).pack(anchor="w", pady=(3, 12))

        banner = tk.Frame(inner, bg=T["card"], highlightbackground=SAFFRON,
                          highlightthickness=2)
        banner.pack(fill="x", padx=25, pady=(0, 15))
        bc = logo_canvas(banner, 52, T["card"])
        bc.pack(side="left", padx=15, pady=10)
        bt = tk.Frame(banner, bg=T["card"])
        bt.pack(side="left", fill="x", expand=True)
        self.lbl(bt, "Atmanirbhar Bharat  •  Self-reliant India", 12, True, "#d97706", "card"
                 ).pack(anchor="w", pady=(8, 1))
        self.lbl(bt, QUOTE_EN, 9, fg="muted", bg="card", wraplength=640, justify="left"
                 ).pack(anchor="w", pady=(0, 8))

        if not apps:
            self.lbl(inner, "Nothing here yet.", 12, fg="muted").pack(anchor="w", padx=25, pady=40)
            return

        grid = tk.Frame(inner, bg=T["bg"])
        grid.pack(fill="x", padx=15, pady=5)
        cols = self.settings["columns"]
        for c in range(cols):
            grid.grid_columnconfigure(c, weight=1, uniform="cards")
        tk.Frame(inner, bg=T["bg"], height=90).pack()   # bottom space: last card never clipped

        gen, BATCH = self._gen, 12

        def batch(i=0):
            # cards are created in small batches so the UI stays smooth
            if gen != self._gen or not grid.winfo_exists():
                return
            for k in range(i, min(i + BATCH, len(apps))):
                self.make_card(grid, apps[k]).grid(row=k // cols, column=k % cols,
                                                   padx=8, pady=8, sticky="ew")
            if i + BATCH < len(apps):
                self.after(8, lambda: batch(i + BATCH))

        batch()

    def make_card(self, parent, app):
        T = self.T
        card = tk.Frame(parent, bg=T["card"], height=165, highlightbackground=T["border"],
                        highlightthickness=1)
        card.pack_propagate(False)
        icon = self.icon_widget(card, app, 64, T["card"])
        icon.place(x=15, y=14)
        name = self.lbl(card, app["name"], 11, True, "text", "card", anchor="w", cursor="hand2")
        name.place(x=91, y=14, relwidth=1, width=-101)
        sub = app["category"] + (f"  •  ★ {app['rating']}" if self.settings["ratings"] else "")
        self.lbl(card, sub, 8, fg="muted", bg="card", anchor="w"
                 ).place(x=91, y=39, relwidth=1, width=-101)
        self.lbl(card, app["desc"], 8, fg="muted", bg="card", anchor="nw", justify="left",
                 wraplength=210).place(x=15, y=84, relwidth=1, width=-30, height=38)
        self.action_button(card, app, small=True).place(x=15, y=130)
        for w in (card, icon, name):
            w.bind("<Button-1>", lambda e, a=app: self.show_detail(a))
        return card

    # ---------------- install button ----------------
    def action_button(self, parent, app, small=False):
        b = tk.Button(parent, relief="flat", fg="white", cursor="hand2",
                      font=("Segoe UI", 8 if small else 10, "bold"),
                      padx=15 if small else 25, pady=3 if small else 6,
                      command=lambda a=app: self.on_action(a))
        self.btns.setdefault(app["name"], []).append(b)
        self.refresh_buttons(app["name"])
        return b

    def refresh_buttons(self, name):
        for b in self.btns.get(name, []):
            try:
                if name in self.progress:
                    b.configure(text=f"Installing {self.progress[name]}%",
                                state="disabled", bg="#9aa0a6")
                elif name in self.installed:
                    b.configure(text="Open", state="normal", bg=self.T["blue"])
                else:
                    b.configure(text="Install", state="normal", bg=self.T["accent"])
            except tk.TclError:
                pass

    def on_action(self, app):
        name = app["name"]
        if name in self.installed:
            os_launch(app)
            return
        if name in self.progress:
            return
        if self.settings["require_signin"] and not self.user:
            messagebox.showinfo("Sign in required", "Please sign in to install apps.")
            self.login_dialog()
            return
        self.progress[name] = 0
        self.refresh_buttons(name)
        self.after(120, lambda: self.tick(app))

    def tick(self, app):
        name = app["name"]
        if name not in self.progress:
            return
        self.progress[name] += 10
        pct = self.progress[name]
        bar = self.bars.get(name)
        if bar:
            try:
                bar["value"] = pct
            except tk.TclError:
                pass
        if pct >= 100:
            del self.progress[name]
            if os_install(app):
                self.installed.add(name)
                self.save_data()
                if self.settings["notifications"]:
                    self.toast(f"✓ {name} installed")
            self.refresh_buttons(name)
            self.refresh_installed_count()
            if self.page == "detail" and self.detail_app and self.detail_app["name"] == name:
                self.show_detail(app)
        else:
            self.refresh_buttons(name)
            self.after(150, lambda: self.tick(app))

    def refresh_installed_count(self):
        b = self.nav_buttons.get("Installed")
        if b:
            try:
                b.configure(text=f"📦  Installed  ({len(self.installed)})")
            except tk.TclError:
                pass

    def uninstall(self, app):
        if not messagebox.askyesno("Uninstall", f"Uninstall {app['name']}?"):
            return
        self.installed.discard(app["name"])
        self.save_data()
        self.refresh_installed_count()
        self.show_detail(app)

    # ---------------- detail ----------------
    def show_detail(self, app):
        self.page, self.detail_app = "detail", app
        self.clear_content()
        T = self.T
        inner = self.scroll_area(T["bg"])
        wrap = tk.Frame(inner, bg=T["bg"])
        wrap.pack(fill="x", padx=35, pady=25)
        self.btn(wrap, "← Back", self.show_list, "bg", "accent", bold=True).pack(anchor="w")

        head = tk.Frame(wrap, bg=T["bg"])
        head.pack(fill="x", pady=20)
        self.icon_widget(head, app, 130, T["bg"]).pack(side="left", padx=(0, 25))
        info = tk.Frame(head, bg=T["bg"])
        info.pack(side="left", fill="x")
        self.lbl(info, app["name"], 25, True).pack(anchor="w")
        self.lbl(info, app["category"], 11, True, "accent").pack(anchor="w", pady=(3, 5))
        if self.settings["ratings"]:
            self.lbl(info, "★" * int(round(app["rating"])) + f"  {app['rating']}", 11,
                     fg="#f59e0b").pack(anchor="w")

        row = tk.Frame(wrap, bg=T["bg"])
        row.pack(anchor="w", pady=10)
        self.action_button(row, app).pack(side="left")
        self.btn(row, "Uninstall", lambda: self.uninstall(app), padx=18, pady=6,
                 state="normal" if app["name"] in self.installed else "disabled"
                 ).pack(side="left", padx=10)
        self.btn(row, "Official website", lambda: self.open_official(app), padx=18, pady=6
                 ).pack(side="left")

        bar = ttk.Progressbar(wrap, length=400, maximum=100,
                              value=self.progress.get(app["name"], 0))
        bar.pack(anchor="w", pady=6)
        self.bars[app["name"]] = bar

        self.lbl(wrap, "About this app", 14, True).pack(anchor="w", pady=(25, 5))
        self.lbl(wrap, app["desc"] + ".", 11, fg="muted", justify="left",
                 wraplength=800).pack(anchor="w")
        self.lbl(wrap, "🇮🇳 Nova Store • Atmanirbhar Bharat\n"
                 "Install is simulated until connected to your OS package manager.",
                 9, fg="muted", justify="left").pack(anchor="w", pady=(30, 40))

    def open_official(self, app):
        d = DOMAINS.get(app["name"])
        open_web(d if d else "https://www.google.com/search?q=" +
                 urllib.parse.quote(app["name"] + " official site"))

    # ---------------- updates ----------------
    def show_updates(self):
        self.page = "updates"
        self.clear_content()
        T = self.T
        inner = self.scroll_area(T["bg"])
        self.lbl(inner, "Updates", 18, True).pack(anchor="w", padx=30, pady=(20, 5))
        status = self.lbl(inner, "Last checked: just now", 10, fg="muted")
        status.pack(anchor="w", padx=30)

        def check():
            status.configure(text="Checking for updates...")
            self.after(1200, lambda: status.configure(
                text="✓ All your apps are up to date") if status.winfo_exists() else None)

        self.pill(inner, "Check for updates", check).pack(anchor="w", padx=30, pady=12)
        self.lbl(inner, "Auto-update apps: " + ("ON" if self.settings["auto_update"] else "OFF"),
                 9, fg="muted").pack(anchor="w", padx=30)
        self.lbl(inner, "Installed apps", 13, True).pack(anchor="w", padx=30, pady=(25, 6))
        inst = [a for a in APPS if a["name"] in self.installed]
        if not inst:
            self.lbl(inner, "No apps installed yet.", 11, fg="muted").pack(anchor="w", padx=30)
        for app in inst:
            r = tk.Frame(inner, bg=T["card"], highlightbackground=T["border"],
                         highlightthickness=1)
            r.pack(fill="x", padx=30, pady=4)
            self.icon_widget(r, app, 46, T["card"]).pack(side="left", padx=10, pady=8)
            self.lbl(r, app["name"], 10, True, "text", "card").pack(side="left")
            self.lbl(r, "Up to date", 9, fg="muted", bg="card").pack(side="right", padx=14)
        tk.Frame(inner, bg=T["bg"], height=60).pack()

    # ---------------- account page ----------------
    def show_account(self):
        self.page = "account"
        self.clear_content()
        T = self.T
        inner = self.scroll_area(T["bg"])
        self.lbl(inner, "Account", 18, True).pack(anchor="w", padx=30, pady=(20, 12))
        box = tk.Frame(inner, bg=T["card"], highlightbackground=T["border"], highlightthickness=1)
        box.pack(fill="x", padx=30)
        self.lbl(box, self.user[0].upper() if self.user else "G", 28, True, "white", "accent",
                 width=3).pack(side="left", padx=20, pady=20)
        col = tk.Frame(box, bg=T["card"])
        col.pack(side="left")
        self.lbl(col, self.user or "Guest", 16, True, "text", "card").pack(anchor="w")
        self.lbl(col, f"{len(self.installed)} apps installed" +
                 ("" if self.user else "  •  not signed in"), 10, fg="muted", bg="card"
                 ).pack(anchor="w")
        bt = tk.Frame(inner, bg=T["bg"])
        bt.pack(anchor="w", padx=30, pady=18)
        if self.user:
            self.pill(bt, "Change password", self.change_password).pack(side="left", padx=4)
            self.pill(bt, "Sign out", self.sign_out).pack(side="left", padx=4)
            self.pill(bt, "Delete account", self.delete_account, True).pack(side="left", padx=4)
        else:
            self.pill(bt, "Sign in / Create account", self.login_dialog).pack(side="left")

    def change_password(self):
        if not self.user:
            return
        acc = self.data["accounts"][self.user]
        old = simpledialog.askstring("Change password", "Current password:", show="•", parent=self)
        if old is None:
            return
        if hash_pw(old, acc["salt"]) != acc["hash"]:
            messagebox.showerror("Nova Store", "Current password is wrong.")
            return
        new = simpledialog.askstring("Change password", "New password:", show="•", parent=self)
        if not new or len(new) < 4:
            messagebox.showwarning("Nova Store", "Password must have at least 4 characters.")
            return
        acc["salt"] = secrets.token_hex(8)
        acc["hash"] = hash_pw(new, acc["salt"])
        self.save_data()
        self.toast("Password updated")

    def delete_account(self):
        if not self.user or not messagebox.askyesno("Delete account", f"Delete '{self.user}'?"):
            return
        self.data["accounts"].pop(self.user, None)
        self.user = None
        self.load_installed()
        self.save_data()
        self.rebuild()

    # ---------------- settings ----------------
    def section(self, parent, title):
        T = self.T
        self.lbl(parent, title, 12, True, "accent").pack(anchor="w", padx=30, pady=(22, 6))
        box = tk.Frame(parent, bg=T["card"], highlightbackground=T["border"], highlightthickness=1)
        box.pack(fill="x", padx=30)
        return box

    def row(self, box, title, subtitle=""):
        T = self.T
        r = tk.Frame(box, bg=T["card"])
        r.pack(fill="x", padx=16, pady=10)
        left = tk.Frame(r, bg=T["card"])
        left.pack(side="left", fill="x", expand=True)
        self.lbl(left, title, 10, False, "text", "card").pack(anchor="w")
        if subtitle:
            self.lbl(left, subtitle, 8, fg="muted", bg="card", justify="left",
                     wraplength=600).pack(anchor="w")
        right = tk.Frame(r, bg=T["card"])
        right.pack(side="right")
        return right

    def toggle(self, parent, key, on_change=None):
        T = self.T
        b = tk.Button(parent, relief="flat", width=7, font=("Segoe UI", 8, "bold"), cursor="hand2")

        def paint():
            on = self.settings[key]
            b.configure(text="ON" if on else "OFF", bg=T["accent"] if on else T["btn2"],
                        fg="white" if on else T["text"])

        def click():
            self.settings[key] = not self.settings[key]
            paint()
            self.save_data()
            if on_change:
                on_change()

        b.configure(command=click)
        paint()
        b.pack()

    def segmented(self, parent, key, options, on_change=None):
        T = self.T
        frame = tk.Frame(parent, bg=T["card"])
        frame.pack()
        buttons = {}

        def paint():
            for o, b in buttons.items():
                sel = self.settings[key] == o
                b.configure(bg=T["accent"] if sel else T["btn2"], fg="white" if sel else T["text"])

        def pick(o):
            self.settings[key] = o
            paint()
            self.save_data()
            if on_change:
                on_change()

        for o in options:
            b = tk.Button(frame, text=str(o), width=7, relief="flat", cursor="hand2",
                          font=("Segoe UI", 8, "bold"), command=lambda o=o: pick(o))
            b.pack(side="left", padx=2)
            buttons[o] = b
        paint()

    def show_settings(self):
        self.page = "settings"
        self.clear_content()
        T = self.T
        inner = self.scroll_area(T["bg"])
        self.lbl(inner, "Settings", 18, True).pack(anchor="w", padx=30, pady=(20, 0))

        box = self.section(inner, "Account")
        right = self.row(box, self.user or "Guest",
                         "Signed in" if self.user else "Sign in to sync your Nova Store profile")
        (self.pill(right, "Sign out", self.sign_out) if self.user
         else self.pill(right, "Sign in", self.login_dialog)).pack()
        self.toggle(self.row(box, "Keep me signed in"), "remember")

        box = self.section(inner, "Appearance & browsing")
        self.segmented(self.row(box, "Theme", "Light or dark interface"), "theme",
                       ["Light", "Dark"], self.rebuild)
        self.segmented(self.row(box, "Apps per row"), "columns", [2, 3, 4], self.show_page)
        self.segmented(self.row(box, "Sort apps by"), "sort", ["Name", "Rating"])
        self.toggle(self.row(box, "Show ratings"), "ratings")

        box = self.section(inner, "Downloads & updates")
        self.toggle(self.row(box, "Auto-update apps"), "auto_update")
        self.toggle(self.row(box, "Update over Wi-Fi only"), "wifi_only")
        self.toggle(self.row(box, "Notifications"), "notifications")
        self.pill(self.row(box, "Updates"), "Open Updates", lambda: self.go("Updates")).pack()

        box = self.section(inner, "Security & family")
        self.toggle(self.row(box, "Require sign-in to install",
                             "Guests can browse but must sign in to install"), "require_signin")
        right = self.row(box, "Parental controls", "Hides Games and Social apps")
        on = self.settings["kids"]
        tk.Button(right, text="ON" if on else "OFF", width=7, relief="flat", cursor="hand2",
                  font=("Segoe UI", 8, "bold"), bg=T["accent"] if on else T["btn2"],
                  fg="white" if on else T["text"], command=self.toggle_kids).pack()

        box = self.section(inner, "Storage & data")
        right = self.row(box, "Download app icons", "Downloads website icons into the icons folder")
        self.dl_label = self.lbl(right, "", 8, fg="muted", bg="card")
        self.dl_label.pack(side="right", padx=5)
        self.pill(right, "Download", lambda: self.download_icons(self.dl_label)).pack(side="right")
        self.pill(self.row(box, "Icons folder", ICON_DIR), "Open folder", self.open_icon_folder).pack()
        self.pill(self.row(box, "Clear installed apps"), "Clear", self.clear_installed, True).pack()
        self.pill(self.row(box, "Reset settings"), "Reset", self.reset_settings, True).pack()

        box = self.section(inner, "About Nova Store")
        self.row(box, f"Nova Store {APP_VERSION}",
                 f"{len(APPS)} apps • {len(CATEGORIES)} categories • {len(self.installed)} installed")
        self.lbl(inner, "🇮🇳 " + QUOTE_EN, 10, True, "accent", wraplength=800, justify="left"
                 ).pack(anchor="w", padx=30, pady=(30, 60))

    # ---------------- parental controls ----------------
    def toggle_kids(self):
        if not self.settings["kids"]:
            pin = simpledialog.askstring("Parental controls", "Create a 4-digit PIN:",
                                         show="•", parent=self)
            if not pin:
                return
            if not (pin.isdigit() and len(pin) == 4):
                messagebox.showwarning("Nova Store", "PIN must contain exactly 4 digits.")
                return
            salt = secrets.token_hex(8)
            self.settings.update(kids=True, pin_salt=salt, pin_hash=hash_pw(pin, salt))
        else:
            pin = simpledialog.askstring("Parental controls", "Enter PIN:", show="•", parent=self)
            if pin is None:
                return
            if hash_pw(pin, self.settings["pin_salt"]) != self.settings["pin_hash"]:
                messagebox.showerror("Nova Store", "Wrong PIN.")
                return
            self.settings["kids"] = False
        self.save_data()
        if self.settings["kids"] and self.nav in KIDS_HIDDEN:
            self.nav = "All Apps"
        self.rebuild()

    # ---------------- storage ----------------
    def clear_installed(self):
        if messagebox.askyesno("Clear installed apps", "Remove all installed apps?"):
            self.installed.clear()
            self.save_data()
            self.refresh_installed_count()
            self.toast("Installed apps cleared")

    def reset_settings(self):
        if not messagebox.askyesno("Reset settings", "Reset all settings to defaults?"):
            return
        keep = {k: self.settings[k] for k in ("kids", "pin_salt", "pin_hash")}
        self.settings = {**DEFAULTS, **keep}
        self.save_data()
        self.rebuild()

    def open_icon_folder(self):
        os.makedirs(ICON_DIR, exist_ok=True)
        try:
            os.startfile(ICON_DIR)
        except Exception:
            webbrowser.open("file://" + ICON_DIR)

    def download_icons(self, label):
        if getattr(self, "dl_running", False):
            return
        os.makedirs(ICON_DIR, exist_ok=True)
        self.dl_running = True
        self.dl_state = {"done": 0, "ok": 0, "total": len(DOMAINS)}
        threading.Thread(target=self._dl_worker, daemon=True).start()
        self._poll_dl(label)

    def _dl_worker(self):
        for name, domain in DOMAINS.items():
            path = os.path.join(ICON_DIR, safe_name(name) + ".png")
            if not os.path.isfile(path):
                try:
                    url = "https://www.google.com/s2/favicons?domain=" + domain.split("/")[0] + "&sz=128"
                    req = urllib.request.Request(url, headers={"User-Agent": "NovaStore/4.0"})
                    with urllib.request.urlopen(req, timeout=8) as r:
                        data = r.read()
                    if len(data) > 200:
                        with open(path, "wb") as f:
                            f.write(data)
                        self.dl_state["ok"] += 1
                except Exception:
                    pass
            self.dl_state["done"] += 1
        self.dl_running = False

    def _poll_dl(self, label):
        s = self.dl_state
        try:
            if label.winfo_exists():
                label.configure(text=f"{s['done']}/{s['total']} ({s['ok']} saved)")
        except tk.TclError:
            pass
        if self.dl_running:
            self.after(300, lambda: self._poll_dl(label))
        else:
            self.img_cache.clear()
            self.toast(f"Icons downloaded: {s['ok']}" if s["ok"] else "No new icons downloaded")
            if self.page in ("list", "detail", "updates"):
                self.show_page()


def open_store():
    global STORE
    if STORE is not None and STORE.winfo_exists():
        STORE.deiconify()
        STORE.lift()
        STORE.focus_force()
    else:
        STORE = Store(root)


# ============================================================
# MYOS APPS (windows)
# ============================================================
_cascade = [0]


def make_window(title, width=600, height=450):
    win = tk.Toplevel(root)
    win.title(f"{OS_NAME} - {title}")
    off = (_cascade[0] % 6) * 28
    _cascade[0] += 1
    win.geometry(f"{width}x{height}+{140 + off}+{90 + off}")
    win.configure(bg=WINDOW)
    if ICON_IMG:
        try:
            win.iconphoto(False, ICON_IMG)
        except Exception:
            pass
    win.lift()
    win.focus_force()
    return win


def dark_btn(parent, text, cmd, bg=BUTTON, **kw):
    return tk.Button(parent, text=text, command=cmd, bg=bg, fg=TEXT, relief="flat",
                     activebackground=ACCENT, activeforeground="white", cursor="hand2", **kw)


def open_notepad():
    win = make_window("Notepad", 700, 500)
    top = tk.Frame(win, bg=WINDOW)
    top.pack(fill="x")
    editor = tk.Text(win, bg="#15161a", fg="white", insertbackground="white",
                     font=("Consolas", 12), undo=True)
    editor.pack(fill="both", expand=True, padx=10, pady=10)

    def save():
        p = filedialog.asksaveasfilename(defaultextension=".txt",
                                         filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if p:
            with open(p, "w", encoding="utf-8") as f:
                f.write(editor.get("1.0", "end-1c"))

    def load():
        p = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if p:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                editor.delete("1.0", "end")
                editor.insert("1.0", f.read())

    dark_btn(top, "Open", load).pack(side="left", padx=5, pady=5)
    dark_btn(top, "Save", save).pack(side="left", padx=5, pady=5)


def open_calculator():
    win = make_window("Calculator", 350, 520)
    display = tk.Entry(win, bg="#111216", fg="white", insertbackground="white",
                       font=("Arial", 22), justify="right")
    display.pack(fill="x", padx=15, pady=15, ipady=10)
    frame = tk.Frame(win, bg=WINDOW)
    frame.pack(expand=True, fill="both")
    keys = ["C", "(", ")", "⌫", "7", "8", "9", "/", "4", "5", "6", "*",
            "1", "2", "3", "-", "0", ".", "=", "+"]

    def press(v):
        if v == "=":
            expr = display.get()
            try:
                if not re.fullmatch(r"[0-9+\-*/(). ]+", expr):
                    raise ValueError
                res = eval(expr, {"__builtins__": {}}, {})
                display.delete(0, "end")
                display.insert(0, str(res))
            except Exception:
                display.delete(0, "end")
                display.insert(0, "Error")
        elif v == "C":
            display.delete(0, "end")
        elif v == "⌫":
            display.delete(len(display.get()) - 1, "end")
        else:
            display.insert("end", v)

    for i, k in enumerate(keys):
        dark_btn(frame, k, lambda x=k: press(x), bg=ACCENT if k == "=" else BUTTON,
                 font=("Arial", 14)).grid(row=i // 4, column=i % 4, sticky="nsew", padx=3, pady=3)
    for i in range(5):
        frame.rowconfigure(i, weight=1)
    for i in range(4):
        frame.columnconfigure(i, weight=1)
    display.bind("<Return>", lambda e: press("="))


def open_file_manager():
    win = make_window("File Manager", 760, 520)
    state = {"path": os.path.expanduser("~")}
    bar = tk.Frame(win, bg=WINDOW)
    bar.pack(fill="x", padx=10, pady=8)
    path_label = tk.Label(bar, bg=WINDOW, fg=TEXT, anchor="w")
    box = tk.Frame(win, bg=WINDOW)
    lb = tk.Listbox(box, bg="#15161a", fg="white", font=("Arial", 12),
                    selectbackground=ACCENT, activestyle="none")
    sb = ttk.Scrollbar(box, command=lb.yview)
    lb.configure(yscrollcommand=sb.set)

    def refresh():
        lb.delete(0, "end")
        path_label.config(text=state["path"])
        try:
            items = sorted(os.listdir(state["path"]),
                           key=lambda n: (not os.path.isdir(os.path.join(state["path"], n)), n.lower()))
            for it in items:
                lb.insert("end", ("📁  " if os.path.isdir(os.path.join(state["path"], it)) else "📄  ") + it)
        except Exception as e:
            messagebox.showerror(OS_NAME, str(e), parent=win)

    def up():
        state["path"] = os.path.dirname(state["path"]) or state["path"]
        refresh()

    def opened(_e=None):
        sel = lb.curselection()
        if not sel:
            return
        p = os.path.join(state["path"], lb.get(sel[0])[3:])
        if os.path.isdir(p):
            state["path"] = p
            refresh()
        else:
            try:
                if platform.system() == "Windows":
                    os.startfile(p)
                elif platform.system() == "Darwin":
                    subprocess.Popen(["open", p])
                else:
                    subprocess.Popen(["xdg-open", p])
            except Exception as e:
                messagebox.showerror(OS_NAME, str(e), parent=win)

    dark_btn(bar, "⬆ Up", up).pack(side="left", padx=(0, 8))
    path_label.pack(side="left", fill="x", expand=True)
    box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    sb.pack(side="right", fill="y")
    lb.pack(side="left", fill="both", expand=True)
    lb.bind("<Double-Button-1>", opened)
    lb.bind("<Return>", opened)
    refresh()


def open_browser():
    win = make_window("Bharat Browser", 900, 560)
    bar = tk.Frame(win, bg=WINDOW)
    bar.pack(fill="x", padx=10, pady=10)
    address = tk.Entry(bar, bg="#111216", fg="white", insertbackground="white", font=("Arial", 11))
    address.pack(side="left", fill="x", expand=True, ipady=7)

    def browse(_e=None):
        url = address.get().strip()
        if not url:
            return
        if not url.startswith(("http://", "https://")):
            url = ("https://" + url) if "." in url and " " not in url else \
                  "https://www.google.com/search?q=" + urllib.parse.quote(url)
        webbrowser.open(url)

    dark_btn(bar, "GO", browse, bg=ACCENT).pack(side="right", padx=5, ipadx=8)
    address.bind("<Return>", browse)
    page = tk.Frame(win, bg="#111216")
    page.pack(fill="both", expand=True)
    tk.Label(page, text="Bharat Browser", bg="#111216", fg="white", font=("Arial", 22, "bold")
             ).pack(pady=(40, 6))
    tk.Label(page, text=QUOTE_HI, bg="#111216", fg=SAFFRON, font=("Segoe UI", 12)).pack()
    tk.Label(page, text="Quick links", bg="#111216", fg="#9aa0a6").pack(pady=(30, 8))
    links = tk.Frame(page, bg="#111216")
    links.pack()
    for i, (n, d) in enumerate([("Instagram", "instagram.com"), ("Twitter / X", "x.com"),
                                ("YouTube", "youtube.com"), ("Google", "google.com"),
                                ("DigiLocker", "digilocker.gov.in"), ("UMANG", "umang.gov.in"),
                                ("Flipkart", "flipkart.com"), ("PhonePe", "phonepe.com")]):
        dark_btn(links, n, lambda d=d: open_web(d), width=14, pady=6
                 ).grid(row=i // 4, column=i % 4, padx=5, pady=5)


def open_terminal():
    win = make_window("Terminal", 700, 450)
    out = tk.Text(win, bg="black", fg="#00ff66", insertbackground="#00ff66", font=("Consolas", 11))
    out.pack(fill="both", expand=True)
    out.insert("end", f"{OS_NAME} Terminal\nType a command below.\n\n")
    cmd = tk.Entry(win, bg="black", fg="#00ff66", insertbackground="#00ff66", font=("Consolas", 11))
    cmd.pack(fill="x")
    cmd.focus_set()

    def run(_e=None):
        c = cmd.get()
        if not c:
            return
        out.insert("end", f"> {c}\n")
        try:
            r = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=20)
            out.insert("end", r.stdout + (r.stderr or ""))
        except Exception as e:
            out.insert("end", str(e) + "\n")
        out.see("end")
        cmd.delete(0, "end")

    cmd.bind("<Return>", run)


def open_settings():
    win = make_window("Settings", 640, 520)
    c = tk.Canvas(win, width=96, height=96, bg=WINDOW, highlightthickness=0)
    c.pack(pady=(25, 0))
    c.create_oval(3, 3, 93, 93, fill="white", outline=SAFFRON, width=6)
    draw_chakra(c, 48, 48, 32)
    tk.Label(win, text=OS_NAME, bg=WINDOW, fg=TEXT, font=("Arial", 24, "bold")).pack(pady=(8, 0))
    tk.Label(win, text=QUOTE_HI, bg=WINDOW, fg=SAFFRON, font=("Segoe UI", 11)).pack(pady=(4, 14))
    info = (f"Version: {APP_VERSION}\nPython: {platform.python_version()}\n"
            f"Computer: {platform.node()}\nSystem: {platform.system()}\n"
            f"Apps in Nova Store: {len(APPS)}")
    tk.Label(win, text=info, bg=WINDOW, fg=TEXT, font=("Arial", 13), justify="left").pack(pady=10)
    dark_btn(win, "🛍  Open Nova Store", open_store, bg=GREEN, font=("Arial", 11, "bold"),
             padx=16, pady=6).pack(pady=6)


def open_about():
    messagebox.showinfo(f"About {OS_NAME}",
                        f"{OS_NAME} {APP_VERSION}\n\n{QUOTE_HI}\n\n{QUOTE_EN}\n\nCreated by Parth Rai")


# ============================================================
# DESKTOP, START MENU, TASKBAR
# ============================================================
DESK_APPS = [
    ("🛍", "Nova Store", open_store), ("🌐", "Browser", open_browser),
    ("📁", "Files", open_file_manager), ("📝", "Notepad", open_notepad),
    ("🧮", "Calculator", open_calculator), ("⌨", "Terminal", open_terminal),
    ("⬇", "Browsers", lambda: downloader.open_downloader(root)),
    ("📡", "System", lambda: system_tools.open_system(root)),
    ("⚙", "Settings", open_settings), ("📸", "Instagram", lambda: open_web("instagram.com")),
    ("🐦", "Twitter / X", lambda: open_web("x.com")),
]
TASKBAR_H = 54
START_H = 540
start_menu = None
desk = None
_wall_src, _wall_cache, _wall_photo, _redraw_job = None, {}, None, None


def load_wallpaper():
    global _wall_src
    if not Image:
        return
    for p in WALLPAPERS:
        if os.path.isfile(p):
            try:
                _wall_src = Image.open(p).convert("RGB")
                return
            except Exception:
                pass


def shadow_text(c, x, y, text, font, fill="white", **kw):
    c.create_text(x + 2, y + 2, text=text, font=font, fill="black", **kw)
    c.create_text(x, y, text=text, font=font, fill=fill, **kw)


def draw_desktop(_e=None):
    """Draws wallpaper, title, quote and icons. Never leaves the screen black:
    if anything fails, a plain tricolour is drawn and the error is logged."""
    global _wall_photo, _redraw_job
    _redraw_job = None
    w, h = desk.winfo_width(), desk.winfo_height()
    if w < 80 or h < 80:
        schedule_redraw()
        return
    desk.delete("all")
    try:
        _draw_wallpaper(w, h)
    except Exception:
        log_error("wallpaper")
        _draw_fallback(w, h)
    try:
        _draw_overlay(w, h)
    except Exception:
        log_error("desktop overlay")


def _draw_fallback(w, h):
    desk.create_rectangle(0, 0, w, h / 3 + 1, fill=SAFFRON, outline="")
    desk.create_rectangle(0, h / 3, w, 2 * h / 3 + 1, fill="white", outline="")
    desk.create_rectangle(0, 2 * h / 3, w, h, fill=GREEN, outline="")
    draw_chakra(desk, w / 2, h / 2, min(w, h) * 0.14)


def _icon_rects(h):
    per_col = max(1, (h - 200) // 104)
    out = []
    for i in range(len(DESK_APPS)):
        x = 60 + (i // per_col) * 104
        y = 130 + (i % per_col) * 104
        out.append((x, y))
    return out


def _draw_wallpaper(w, h):
    global _wall_photo
    if _wall_src is None:
        _draw_fallback(w, h)
        return
    key = (w, h)
    if key not in _wall_cache:
        if len(_wall_cache) > 3:
            _wall_cache.clear()
        iw, ih = _wall_src.size
        s = max(w / iw, h / ih)
        im = _wall_src.resize((int(iw * s) + 1, int(ih * s) + 1), Image.LANCZOS)
        l, t = (im.width - w) // 2, (im.height - h) // 2
        im = im.crop((l, t, l + w, t + h))
        # darken the quote strip and icon tiles inside the image itself
        # (no stipple, so it looks the same on Windows, Linux and Mac)
        def darken(box, f):
            box = (max(0, box[0]), max(0, box[1]), min(w, box[2]), min(h, box[3]))
            if box[2] > box[0] and box[3] > box[1]:
                im.paste(ImageEnhance.Brightness(im.crop(box)).enhance(f), box[:2])
        darken((0, h - 84, w, h), 0.35)
        for x, y in _icon_rects(h):
            darken((x - 44, y - 44, x + 44, y + 48), 0.45)
        _wall_cache[key] = ImageTk.PhotoImage(im)
    _wall_photo = _wall_cache[key]
    desk.create_image(0, 0, image=_wall_photo, anchor="nw")


def _draw_overlay(w, h):
    if _wall_src is None:     # fallback has no darkened areas, draw solid ones
        desk.create_rectangle(0, h - 84, w, h, fill="#1a1a1a", outline="")
        for x, y in _icon_rects(h):
            desk.create_rectangle(x - 44, y - 44, x + 44, y + 48, fill="#1a1a1a", outline="")
    shadow_text(desk, w / 2, 46, "BHARAT OS", ("Segoe UI", 28, "bold"))
    shadow_text(desk, w / 2, 82, "Made in India", ("Segoe UI", 12))
    shadow_text(desk, w / 2, h - 56, "Atmanirbhar Bharat", ("Segoe UI", 16, "bold"), fill="#ffd9a0")
    shadow_text(desk, w / 2, h - 30, QUOTE_HI, ("Segoe UI", 11), fill="white")
    for i, (x, y) in enumerate(_icon_rects(h)):
        emoji, name, fn = DESK_APPS[i]
        tag = f"ico{i}"
        # invisible hit-box so the whole tile is clickable
        desk.create_rectangle(x - 44, y - 44, x + 44, y + 48, fill="", outline="", tags=tag)
        desk.create_text(x, y - 10, text=emoji, font=("Segoe UI Emoji", 28), fill="white", tags=tag)
        desk.create_text(x, y + 30, text=name, font=("Segoe UI", 9, "bold"), fill="white", tags=tag)
        desk.tag_bind(tag, "<Button-1>", lambda e, f=fn: (hide_start(), f()))
        desk.tag_bind(tag, "<Enter>", lambda e: desk.configure(cursor="hand2"))
        desk.tag_bind(tag, "<Leave>", lambda e: desk.configure(cursor=""))


def schedule_redraw(_e=None):
    global _redraw_job
    if _redraw_job:
        root.after_cancel(_redraw_job)
    _redraw_job = root.after(120, draw_desktop)      # debounced = smooth resizing


def hide_start(_e=None):
    global start_menu
    if start_menu is not None:
        try:
            start_menu.destroy()
        except Exception:
            pass
        start_menu = None


def toggle_start():
    global start_menu
    if start_menu is not None:
        hide_start()
        return
    start_menu = tk.Frame(root, bg=WINDOW, width=350, height=START_H,
                          highlightbackground=SAFFRON, highlightthickness=2)
    start_menu.pack_propagate(False)
    place_start()
    start_menu.lift()

    head = tk.Frame(start_menu, bg=WINDOW)
    head.pack(fill="x", pady=(14, 6))
    logo_canvas(head, 46, WINDOW).pack(side="left", padx=(18, 10))
    tk.Label(head, text="BHARAT OS", bg=WINDOW, fg="white", font=("Arial", 19, "bold")).pack(side="left")

    def run(fn):
        hide_start()
        fn()

    items = [("🛍  Nova Store", open_store), ("🌐  Browser", open_browser),
             ("📁  File Manager", open_file_manager), ("📝  Notepad", open_notepad),
             ("🧮  Calculator", open_calculator), ("⌨  Terminal", open_terminal),
             ("⬇  Download Browsers", lambda: downloader.open_downloader(root)),
             ("📡  Wi-Fi / Bluetooth / Search", lambda: system_tools.open_system(root)),
             ("⚙  Settings", open_settings), ("ℹ  About", open_about)]
    for text, fn in items:
        dark_btn(start_menu, text, lambda f=fn: run(f), anchor="w", font=("Arial", 12)
                 ).pack(fill="x", padx=18, pady=3, ipady=5)
    dark_btn(start_menu, "⏻  Exit Bharat OS", lambda: (hide_start(), exit_os()), bg="#8a2a2a",
             anchor="w", font=("Arial", 12)).pack(fill="x", padx=18, pady=(8, 3), ipady=5)
    tk.Label(start_menu, text="Atmanirbhar Bharat", bg=WINDOW, fg=SAFFRON,
             font=("Segoe UI", 10, "bold")).pack(side="bottom", pady=8)


def place_start():
    if start_menu is not None:
        start_menu.place(x=10, y=max(10, root.winfo_height() - TASKBAR_H - START_H - 8))


def exit_os():
    if messagebox.askyesno(OS_NAME, "Shut down Bharat OS?"):
        root.destroy()


def build_taskbar():
    bar = tk.Frame(root, bg=TASKBAR, height=TASKBAR_H)
    bar.pack(side="bottom", fill="x")
    bar.pack_propagate(False)
    tri = tk.Frame(bar, height=3)
    tri.pack(fill="x", side="top")
    for col in (SAFFRON, "white", GREEN):
        tk.Frame(tri, bg=col, height=3).pack(side="left", fill="x", expand=True)

    lg = logo_canvas(bar, 36, TASKBAR)
    lg.pack(side="left", padx=(12, 2), pady=7)
    lg.bind("<Button-1>", lambda e: toggle_start())
    lg.configure(cursor="hand2")
    tk.Button(bar, text="Bharat OS", command=toggle_start, bg=TASKBAR, fg="white",
              activebackground=BUTTON, activeforeground="white", relief="flat",
              font=("Arial", 12, "bold"), cursor="hand2").pack(side="left", padx=(0, 18))

    for emoji, tip, fn in (("🛍", "Nova Store", open_store), ("🌐", "Browser", open_browser),
                           ("📁", "Files", open_file_manager), ("📝", "Notepad", open_notepad),
                           ("📸", "Instagram", lambda: open_web("instagram.com")),
                           ("🐦", "Twitter / X", lambda: open_web("x.com"))):
        tk.Button(bar, text=emoji, command=lambda f=fn: (hide_start(), f()), bg=TASKBAR,
                  fg="white", activebackground=BUTTON, relief="flat", cursor="hand2",
                  font=("Segoe UI Emoji", 14)).pack(side="left", padx=2)

    clock = tk.Label(bar, bg=TASKBAR, fg="white", font=("Arial", 10), justify="right")
    clock.pack(side="right", padx=15)

    def tick():
        clock.config(text=datetime.datetime.now().strftime("%H:%M:%S\n%d/%m/%Y"))
        root.after(1000, tick)

    tick()


# ============================================================
# START
# ============================================================
def main():
    global root, desk, ICON_IMG
    root = tk.Tk()
    root.title(OS_NAME)
    root.geometry("1280x760")
    root.minsize(900, 560)
    root.configure(bg=BG)
    ICON_IMG = make_icon_image()
    if ICON_IMG:
        try:
            root.iconphoto(True, ICON_IMG)
        except Exception:
            pass
    def on_error(exc, val, tb):
        # any error inside a button/callback is logged and shown (not silent)
        import traceback
        text = "".join(traceback.format_exception(exc, val, tb))
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"--- {datetime.datetime.now()}\n{text}\n")
        except Exception:
            pass
        print(text)
        try:
            messagebox.showerror(OS_NAME, "Something went wrong:\n\n" + text[-700:] +
                                 "\n(Saved in Bharat_OS_error.log)")
        except Exception:
            pass

    root.report_callback_exception = on_error
    try:
        load_wallpaper()
    except Exception:
        log_error("load wallpaper")
    build_taskbar()                       # packed first so it always stays visible
    desk = tk.Canvas(root, bg=BG, highlightthickness=0)
    desk.pack(fill="both", expand=True)
    desk.bind("<Configure>", schedule_redraw)
    desk.bind("<Button-1>", hide_start, add="+")
    root.bind("<Configure>", lambda e: place_start() if e.widget is root else None, add="+")
    root.update_idletasks()
    root.update()
    if not security.require_login(root):
        root.destroy(); return
    root.after(150, draw_desktop)         # first paint, do not wait for a resize
    root.after(700, draw_desktop)         # second paint in case the window was still sizing
    root.mainloop()


if __name__ == "__main__":
    main()
