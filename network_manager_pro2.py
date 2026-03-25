import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import psutil
import threading
import socket
import select
import os
import json
import winreg
import sys
import ctypes
import win32com.client
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw, ImageFont

# ── Admin kontrolü ────────────────────────────────────────────────────────────
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(f'"{a}"' for a in sys.argv), None, 1
    )

if not is_admin():
    run_as_admin()
    sys.exit()

# ── Renk paleti ───────────────────────────────────────────────────────────────
C = {
    "bg":           "#F5F7FA",
    "card":         "#FFFFFF",
    "border":       "#E2E8F0",
    "header_bg":    "#1558D6",
    "header_grad":  "#1A73E8",
    "accent":       "#1A73E8",
    "accent_dark":  "#1558D6",
    "accent_light": "#E8F0FE",
    "success":      "#1E8E3E",
    "success_bg":   "#E6F4EA",
    "danger":       "#D93025",
    "danger_bg":    "#FCE8E6",
    "text":         "#202124",
    "text_sub":     "#5F6368",
    "text_muted":   "#9AA0A6",
    "white":        "#FFFFFF",
    "log_bg":       "#0D1117",
    "log_fg":       "#C9D1D9",
    "log_green":    "#3FB950",
    "log_yellow":   "#D29922",
    "log_blue":     "#58A6FF",
    "dot_on":       "#1E8E3E",
    "dot_off":      "#9AA0A6",
}

# ── WiFi Proxy ────────────────────────────────────────────────────────────────
class WiFiProxy:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.running = False
        self.server = None

    def start(self):
        self.running = True
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.server.listen(100)
        while self.running:
            try:
                client, _ = self.server.accept()
                threading.Thread(target=self.handle_client, args=(client,), daemon=True).start()
            except:
                break

    def handle_client(self, client):
        try:
            request = client.recv(8192)
            if not request:
                return
            first_line = request.split(b'\r\n')[0].decode('utf-8', errors='ignore')
            if 'CONNECT' in first_line:
                parts = first_line.split()
                hp = parts[1].split(':')
                host, port = hp[0], int(hp[1]) if len(hp) > 1 else 443
                remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote.settimeout(30)
                remote.bind((self.host, 0))
                remote.connect((host, port))
                client.send(b'HTTP/1.1 200 Connection established\r\n\r\n')
                sockets = [client, remote]
                while True:
                    r, _, _ = select.select(sockets, [], [], 60)
                    if not r:
                        break
                    for s in r:
                        data = s.recv(16384)
                        if not data:
                            return
                        (remote if s == client else client).send(data)
            else:
                parts = first_line.split()
                url = parts[1] if len(parts) > 1 else ''
                if url.startswith('http://'):
                    url = url[7:]
                    host = url.split('/')[0].split(':')[0]
                    remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    remote.settimeout(30)
                    remote.bind((self.host, 0))
                    remote.connect((host, 80))
                    remote.send(request)
                    while True:
                        data = remote.recv(16384)
                        if not data:
                            break
                        client.send(data)
                    remote.close()
        except:
            pass
        finally:
            client.close()

    def stop(self):
        self.running = False
        if self.server:
            try:
                self.server.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self.server.close()
            except:
                pass


# ── UI Yardımcıları ───────────────────────────────────────────────────────────
class Card(tk.Frame):
    """Gölgeli, kenarlıklı beyaz kart."""
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C["card"], relief=tk.FLAT,
                         highlightbackground=C["border"], highlightthickness=1, **kw)

class SectionLabel(tk.Label):
    def __init__(self, parent, text, **kw):
        super().__init__(parent, text=text, font=("Segoe UI", 8, "bold"),
                         bg=C["bg"], fg=C["text_muted"], **kw)

class ModernCheckbutton(tk.Frame):
    """Özel renkli checkbox + label."""
    def __init__(self, parent, text, variable, command=None, **kw):
        super().__init__(parent, bg=C["card"], **kw)
        self.var = variable
        self.cmd = command
        self.box = tk.Label(self, width=2, height=1, font=("Segoe UI", 10),
                            bg=C["card"], fg=C["accent"], cursor="hand2")
        self.box.pack(side=tk.LEFT)
        tk.Label(self, text=text, font=("Segoe UI", 9),
                 bg=C["card"], fg=C["text"]).pack(side=tk.LEFT)
        self.box.bind("<Button-1>", self._toggle)
        self._refresh()

    def _toggle(self, _=None):
        self.var.set(not self.var.get())
        self._refresh()
        if self.cmd:
            self.cmd()

    def _refresh(self):
        self.box.config(text="☑" if self.var.get() else "☐")


class StatusDot(tk.Canvas):
    """Küçük animasyonlu durum noktası."""
    def __init__(self, parent, **kw):
        super().__init__(parent, width=12, height=12, bg=C["card"],
                         highlightthickness=0, **kw)
        self._dot = self.create_oval(2, 2, 10, 10, fill=C["dot_off"], outline="")

    def set_state(self, active: bool):
        self.itemconfig(self._dot, fill=C["dot_on"] if active else C["dot_off"])


class ModernButton(tk.Frame):
    """Hover efektli düz buton."""
    def __init__(self, parent, text, command, color, hover_color,
                 fg=C["white"], width=160, height=38, state="normal", **kw):
        super().__init__(parent, bg=parent["bg"] if hasattr(parent, "__getitem__") else C["bg"], **kw)
        self._color = color
        self._hover = hover_color
        self._state = state
        self._cmd = command
        self.btn = tk.Label(self, text=text, font=("Segoe UI", 10, "bold"),
                            bg=color if state == "normal" else C["border"],
                            fg=fg if state == "normal" else C["text_muted"],
                            width=0, cursor="hand2" if state == "normal" else "arrow",
                            relief=tk.FLAT, padx=18, pady=8)
        self.btn.pack()
        if state == "normal":
            self.btn.bind("<Enter>", lambda _: self.btn.config(bg=hover_color))
            self.btn.bind("<Leave>", lambda _: self.btn.config(bg=color))
            self.btn.bind("<Button-1>", lambda _: command())

    def enable(self):
        self._state = "normal"
        self.btn.config(bg=self._color, fg=C["white"], cursor="hand2")
        self.btn.bind("<Enter>", lambda _: self.btn.config(bg=self._hover))
        self.btn.bind("<Leave>", lambda _: self.btn.config(bg=self._color))
        self.btn.bind("<Button-1>", lambda _: self._cmd())

    def disable(self):
        self._state = "disabled"
        self.btn.config(bg=C["border"], fg=C["text_muted"], cursor="arrow")
        self.btn.unbind("<Enter>")
        self.btn.unbind("<Leave>")
        self.btn.unbind("<Button-1>")


# ── NetworkManager ────────────────────────────────────────────────────────────
class NetworkManager:
    def __init__(self, root):
        self.root = root
        root.title("Network Manager Pro  v2")
        root.configure(bg=C["bg"])
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        W, H = 720, 780
        root.update_idletasks()
        x = (root.winfo_screenwidth()  - W) // 2
        y = (root.winfo_screenheight() - H) // 2
        root.geometry(f"{W}x{H}+{x}+{y}")

        self.config_file = os.path.join(os.path.expanduser("~"), ".nmgr_v2.json")
        self.proxy        = None
        self.proxy_thread = None
        self.tray_icon    = None
        self.is_running   = False
        self._eth_name    = None

        self._build_ui()
        self.load_wifi()
        self.load_config()
        self.setup_tray()

        if "--autostart" in sys.argv:
            self.root.withdraw()
            self.root.after(600, self._autostart_run)
        else:
            self.log("info", "Hazır — BAŞLAT butonuna tıklayın.")

    # ─────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── HEADER ──────────────────────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=C["header_bg"], height=70)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        left = tk.Frame(hdr, bg=C["header_bg"])
        left.pack(side=tk.LEFT, padx=24, pady=12)
        tk.Label(left, text="⚡", font=("Segoe UI", 22),
                 bg=C["header_bg"], fg=C["white"]).pack(side=tk.LEFT)
        title_f = tk.Frame(left, bg=C["header_bg"])
        title_f.pack(side=tk.LEFT, padx=8)
        tk.Label(title_f, text="Network Manager Pro",
                 font=("Segoe UI", 14, "bold"),
                 bg=C["header_bg"], fg=C["white"]).pack(anchor=tk.W)
        tk.Label(title_f, text="v2.0  •  WiFi / Ethernet yöneticisi",
                 font=("Segoe UI", 8),
                 bg=C["header_bg"], fg="#A8C7FA").pack(anchor=tk.W)

        # hakkında butonu (sağ üst)
        about_btn = tk.Label(hdr, text="ℹ  Hakkında", font=("Segoe UI", 9),
                             bg=C["header_bg"], fg="#A8C7FA", cursor="hand2")
        about_btn.pack(side=tk.RIGHT, padx=(0, 16))
        about_btn.bind("<Enter>", lambda _: about_btn.config(fg=C["white"]))
        about_btn.bind("<Leave>", lambda _: about_btn.config(fg="#A8C7FA"))
        about_btn.bind("<Button-1>", lambda _: self._show_about())

        # durum badge (sağ üst)
        self._badge_frame = tk.Frame(hdr, bg=C["header_bg"])
        self._badge_frame.pack(side=tk.RIGHT, padx=24)
        self._status_dot = tk.Canvas(self._badge_frame, width=10, height=10,
                                     bg=C["header_bg"], highlightthickness=0)
        self._status_dot.pack(side=tk.LEFT, pady=2)
        self._dot_oval = self._status_dot.create_oval(1,1,9,9, fill="#9AA0A6", outline="")
        self._badge_lbl = tk.Label(self._badge_frame, text="Pasif",
                                   font=("Segoe UI", 9, "bold"),
                                   bg=C["header_bg"], fg="#9AA0A6")
        self._badge_lbl.pack(side=tk.LEFT, padx=(4,0))

        # ── SCROLL CANVAS (içerik) ───────────────────────────────────────────
        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=24, pady=16)

        # ── KART 1: Ağ Seçimi ───────────────────────────────────────────────
        SectionLabel(body, "AĞ ARAYÜZÜ").pack(anchor=tk.W, pady=(0,4))
        net_card = Card(body)
        net_card.pack(fill=tk.X, pady=(0,12))

        # WiFi satırı
        wifi_row = tk.Frame(net_card, bg=C["card"])
        wifi_row.pack(fill=tk.X, padx=16, pady=(14,6))
        tk.Label(wifi_row, text="📶  WiFi", font=("Segoe UI", 9, "bold"),
                 bg=C["card"], fg=C["text"], width=14, anchor=tk.W).pack(side=tk.LEFT)
        self.wifi_combo = ttk.Combobox(wifi_row, width=44, state="readonly",
                                       font=("Segoe UI", 9))
        self.wifi_combo.pack(side=tk.LEFT, padx=(0,8))
        self.wifi_combo.bind("<<ComboboxSelected>>", lambda e: self.save_config())
        refresh_lbl = tk.Label(wifi_row, text="🔄", font=("Segoe UI", 11),
                 bg=C["card"], fg=C["accent"], cursor="hand2")
        refresh_lbl.pack(side=tk.LEFT)
        refresh_lbl.bind("<Button-1>", lambda _: self.load_wifi())

        # Ethernet satırı
        eth_row = tk.Frame(net_card, bg=C["card"])
        eth_row.pack(fill=tk.X, padx=16, pady=(0,14))
        tk.Label(eth_row, text="🖥  Ethernet", font=("Segoe UI", 9, "bold"),
                 bg=C["card"], fg=C["text"], width=14, anchor=tk.W).pack(side=tk.LEFT)
        self.eth_combo = ttk.Combobox(eth_row, width=44, state="readonly",
                                      font=("Segoe UI", 9))
        self.eth_combo.pack(side=tk.LEFT)
        self.eth_combo.bind("<<ComboboxSelected>>", lambda e: self.save_config())

        # ── KART 2: Tarayıcı Seçimi ─────────────────────────────────────────
        SectionLabel(body, "TARAYICI SEÇİMİ  (WiFi üzerinden çalışır)").pack(anchor=tk.W, pady=(0,4))
        br_card = Card(body)
        br_card.pack(fill=tk.X, pady=(0,12))

        br_inner = tk.Frame(br_card, bg=C["card"])
        br_inner.pack(fill=tk.X, padx=16, pady=14)

        self.use_chrome  = tk.BooleanVar(value=False)
        self.use_firefox = tk.BooleanVar(value=False)
        self.use_all     = tk.BooleanVar(value=False)

        ModernCheckbutton(br_inner, "  🌐  Chrome",
                          self.use_chrome, self._on_browser_check).pack(side=tk.LEFT, padx=(0,24))
        ModernCheckbutton(br_inner, "  🦊  Firefox",
                          self.use_firefox, self._on_browser_check).pack(side=tk.LEFT, padx=(0,24))

        sep = tk.Frame(br_inner, bg=C["border"], width=1, height=22)
        sep.pack(side=tk.LEFT, padx=8)

        ModernCheckbutton(br_inner, "  🌍  Tüm Tarayıcılar",
                          self.use_all, self._on_all_check).pack(side=tk.LEFT, padx=(8,0))

        # ── KART 3: Ayarlar ─────────────────────────────────────────────────
        SectionLabel(body, "AYARLAR").pack(anchor=tk.W, pady=(0,4))
        opt_card = Card(body)
        opt_card.pack(fill=tk.X, pady=(0,12))

        opt_inner = tk.Frame(opt_card, bg=C["card"])
        opt_inner.pack(fill=tk.X, padx=16, pady=14)

        self.patch_shortcuts = tk.BooleanVar(value=True)
        self.auto_start      = tk.BooleanVar(value=False)
        self.minimize_tray   = tk.BooleanVar(value=True)

        ModernCheckbutton(opt_inner,
                          "Tarayıcı kısayollarını WiFi için otomatik ayarla",
                          self.patch_shortcuts, self.save_config).pack(anchor=tk.W, pady=2)
        ModernCheckbutton(opt_inner,
                          "Windows başlangıcında otomatik başlat  (systray'de gizli)",
                          self.auto_start, self.toggle_autostart).pack(anchor=tk.W, pady=2)
        ModernCheckbutton(opt_inner,
                          "Kapatınca sistem tepsisinde çalışmaya devam et",
                          self.minimize_tray, self.save_config).pack(anchor=tk.W, pady=2)

        # ── KONTROL BUTONLARI ────────────────────────────────────────────────
        btn_row = tk.Frame(body, bg=C["bg"])
        btn_row.pack(fill=tk.X, pady=(4,12))

        self._start_btn = ModernButton(btn_row, "▶   BAŞLAT",
                                       self.start_system,
                                       C["accent"], C["accent_dark"])
        self._start_btn.pack(side=tk.LEFT, padx=(0,10))

        self._stop_btn = ModernButton(btn_row, "⏹   DURDUR",
                                      self.stop_system,
                                      C["danger"], "#B71C1C",
                                      state="disabled")
        self._stop_btn.pack(side=tk.LEFT)

        # ── LOG ALANI ────────────────────────────────────────────────────────
        SectionLabel(body, "DURUM").pack(anchor=tk.W, pady=(0,4))
        log_card = Card(body)
        log_card.pack(fill=tk.BOTH, expand=True)

        self.status = scrolledtext.ScrolledText(
            log_card, height=9, font=("Cascadia Code", 9),
            bg=C["log_bg"], fg=C["log_fg"],
            insertbackground=C["log_fg"], relief=tk.FLAT,
            padx=12, pady=10, wrap=tk.WORD
        )
        self.status.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self.status.tag_config("info",    foreground=C["log_blue"])
        self.status.tag_config("success", foreground=C["log_green"])
        self.status.tag_config("warn",    foreground=C["log_yellow"])
        self.status.tag_config("dim",     foreground="#6E7681")

    # ── Hakkında penceresi ──────────────────────────────────────────────────
    def _show_about(self):
        win = tk.Toplevel(self.root)
        win.title("Hakkında")
        win.configure(bg=C["bg"])
        win.resizable(False, False)
        win.grab_set()
        W, H = 420, 320
        x = self.root.winfo_x() + (720 - W) // 2
        y = self.root.winfo_y() + (780 - H) // 2
        win.geometry(f"{W}x{H}+{x}+{y}")

        # header
        hdr = tk.Frame(win, bg=C["header_bg"], height=60)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⚡ Network Manager Pro", font=("Segoe UI", 13, "bold"),
                 bg=C["header_bg"], fg=C["white"]).pack(expand=True)

        body = tk.Frame(win, bg=C["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

        tk.Label(body, text="v2.0", font=("Segoe UI", 11, "bold"),
                 bg=C["bg"], fg=C["text"]).pack(anchor=tk.W)
        tk.Label(body, text="WiFi ve Ethernet'i aynı anda yönet.\nTarayıcıları WiFi'den, diğer programları\nEthernet'ten internete çıkar.",
                 font=("Segoe UI", 9), bg=C["bg"], fg=C["text_sub"],
                 justify=tk.LEFT).pack(anchor=tk.W, pady=(6, 16))

        sep = tk.Frame(body, bg=C["border"], height=1)
        sep.pack(fill=tk.X, pady=(0, 14))

        tk.Label(body, text="Geliştirici", font=("Segoe UI", 8, "bold"),
                 bg=C["bg"], fg=C["text_muted"]).pack(anchor=tk.W)
        tk.Label(body, text="Yusuf Ziya Kaplan", font=("Segoe UI", 10, "bold"),
                 bg=C["bg"], fg=C["text"]).pack(anchor=tk.W, pady=(2, 10))

        tk.Label(body, text="GitHub", font=("Segoe UI", 8, "bold"),
                 bg=C["bg"], fg=C["text_muted"]).pack(anchor=tk.W)

        link = tk.Label(body, text="github.com/yusufziyakaplan",
                        font=("Segoe UI", 9, "underline"),
                        bg=C["bg"], fg=C["accent"], cursor="hand2")
        link.pack(anchor=tk.W, pady=(2, 0))
        link.bind("<Button-1>", lambda _: __import__("webbrowser").open(
            "https://github.com/yusufziyakaplan?tab=repositories"))
        link.bind("<Enter>", lambda _: link.config(fg=C["accent_dark"]))
        link.bind("<Leave>", lambda _: link.config(fg=C["accent"]))

        tk.Button(win, text="Kapat", font=("Segoe UI", 9),
                  bg=C["accent"], fg=C["white"], relief=tk.FLAT,
                  padx=20, pady=6, cursor="hand2",
                  command=win.destroy).pack(pady=(0, 20))

    # ── Log ──────────────────────────────────────────────────────────────────
    def log(self, level, msg):
        prefix = {"info": "ℹ ", "success": "✓ ", "warn": "⚠ ", "dim": "  "}.get(level, "  ")
        self.status.insert(tk.END, prefix + msg + "\n", level)
        self.status.see(tk.END)

    # ── Header badge ─────────────────────────────────────────────────────────
    def _set_badge(self, active: bool):
        if active:
            self._status_dot.itemconfig(self._dot_oval, fill=C["dot_on"])
            self._badge_lbl.config(text="Aktif", fg=C["log_green"])
        else:
            self._status_dot.itemconfig(self._dot_oval, fill=C["dot_off"])
            self._badge_lbl.config(text="Pasif", fg="#9AA0A6")

    # ── Tarayıcı checkbox mantığı ─────────────────────────────────────────────
    def _on_browser_check(self):
        self.use_all.set(self.use_chrome.get() and self.use_firefox.get())
        # use_all checkbox görselini güncelle
        for w in self.root.winfo_children():
            self._refresh_all_widgets(w)
        self.save_config()

    def _refresh_all_widgets(self, widget):
        if isinstance(widget, ModernCheckbutton):
            widget._refresh()
        for child in widget.winfo_children():
            self._refresh_all_widgets(child)

    def _on_all_check(self):
        v = self.use_all.get()
        self.use_chrome.set(v)
        self.use_firefox.set(v)
        self._refresh_all_widgets(self.root)
        self.save_config()

    def _get_selected_browser(self):
        if self.use_all.get() or (self.use_chrome.get() and self.use_firefox.get()):
            return "all"
        if self.use_chrome.get():
            return "chrome"
        if self.use_firefox.get():
            return "firefox"
        return None

    def _autostart_run(self):
        self.start_system()
        b = self._get_selected_browser()
        if b:
            self.launch_browser(b)

    # ── Tray ─────────────────────────────────────────────────────────────────
    def _make_tray_icon(self, active: bool):
        color = (26, 115, 232) if active else (154, 160, 166)
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([4, 4, 60, 60], fill=color)
        d.text((20, 18), "N", fill=(255, 255, 255))
        return img

    def setup_tray(self):
        menu = Menu(
            MenuItem("Aç",     self.show_window, default=True),
            MenuItem("Başlat", self.start_system_from_tray,
                     enabled=lambda i: not self.is_running),
            MenuItem("Durdur", self.stop_system_from_tray,
                     enabled=lambda i: self.is_running),
            Menu.SEPARATOR,
            MenuItem("Çıkış",  self.quit_app)
        )
        self.tray_icon = Icon("NMPro", self._make_tray_icon(False),
                              "Network Manager Pro v2", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def minimize_to_tray(self):
        if self.minimize_tray.get():
            self.root.withdraw()
        else:
            self.quit_app()

    def start_system_from_tray(self):
        self.root.after(0, self.start_system)

    def stop_system_from_tray(self):
        self.root.after(0, self.stop_system)

    def quit_app(self):
        self.stop_system()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()

    # ── Ağ arayüzleri ────────────────────────────────────────────────────────
    def load_wifi(self):
        interfaces = []
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        for name, addr_list in addrs.items():
            if name not in stats or not stats[name].isup:
                continue
            for addr in addr_list:
                if addr.family == 2:
                    ip = addr.address
                    # loopback ve link-local adresleri filtrele
                    if ip.startswith("127.") or ip.startswith("169.254."):
                        continue
                    interfaces.append(f"{name} - {ip}")
        self.wifi_combo["values"] = interfaces
        self.eth_combo["values"]  = interfaces
        if len(interfaces) >= 2:
            if not self.wifi_combo.get(): self.wifi_combo.current(1)
            if not self.eth_combo.get():  self.eth_combo.current(0)
        elif interfaces:
            if not self.wifi_combo.get(): self.wifi_combo.current(0)
            if not self.eth_combo.get():  self.eth_combo.current(0)
        if not interfaces:
            self.log("warn", "Aktif ağ arayüzü bulunamadı — kabloyu/WiFi'yi kontrol edin")

    # ── Firefox profil proxy ────────────────────────────────────────────────
    def _firefox_profile_dirs(self):
        profiles_path = os.path.join(os.environ["APPDATA"], "Mozilla", "Firefox", "Profiles")
        if not os.path.isdir(profiles_path):
            return []
        return [
            os.path.join(profiles_path, d)
            for d in os.listdir(profiles_path)
            if os.path.isdir(os.path.join(profiles_path, d))
        ]

    def patch_firefox_proxy(self, wifi_ip, port=8888):
        user_js_content = (
            f'user_pref("network.proxy.type", 1);\n'
            f'user_pref("network.proxy.http", "{wifi_ip}");\n'
            f'user_pref("network.proxy.http_port", {port});\n'
            f'user_pref("network.proxy.ssl", "{wifi_ip}");\n'
            f'user_pref("network.proxy.ssl_port", {port});\n'
            f'user_pref("network.proxy.no_proxies_on", "");\n'
        )
        patched = 0
        for profile_dir in self._firefox_profile_dirs():
            try:
                with open(os.path.join(profile_dir, "user.js"), "w") as f:
                    f.write(user_js_content)
                patched += 1
            except:
                pass
        return patched

    def restore_firefox_proxy(self):
        restored = 0
        for profile_dir in self._firefox_profile_dirs():
            user_js = os.path.join(profile_dir, "user.js")
            if os.path.exists(user_js):
                try:
                    os.remove(user_js)
                    restored += 1
                except:
                    pass
        return restored

    # ── Kısayol yönetimi ─────────────────────────────────────────────────────
    def _shortcut_paths(self, browser):
        chrome = [
            os.path.join(os.environ["APPDATA"],
                r"Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar\Google Chrome.lnk"),
            os.path.join(os.environ["USERPROFILE"], r"Desktop\Google Chrome.lnk"),
            os.path.join(os.environ["APPDATA"],
                r"Microsoft\Windows\Start Menu\Programs\Google Chrome.lnk"),
            os.path.join(os.environ["PUBLIC"], r"Desktop\Google Chrome.lnk"),
        ]
        firefox = [
            os.path.join(os.environ["APPDATA"],
                r"Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar\Firefox.lnk"),
            os.path.join(os.environ["USERPROFILE"], r"Desktop\Firefox.lnk"),
            os.path.join(os.environ["APPDATA"],
                r"Microsoft\Windows\Start Menu\Programs\Firefox.lnk"),
            os.path.join(os.environ["PUBLIC"], r"Desktop\Firefox.lnk"),
        ]
        if browser == "chrome":  return chrome
        if browser == "firefox": return firefox
        return chrome + firefox

    def patch_browser_shortcuts(self, wifi_ip, browser):
        shell = win32com.client.Dispatch("WScript.Shell")
        patched = 0
        for path in self._shortcut_paths(browser):
            if os.path.exists(path):
                try:
                    sc = shell.CreateShortCut(path)
                    if "--proxy-server=" not in sc.Arguments:
                        sc.Arguments = f"--proxy-server={wifi_ip}:8888"
                        sc.save()
                        patched += 1
                except:
                    pass
        return patched

    def restore_browser_shortcuts(self):
        shell = win32com.client.Dispatch("WScript.Shell")
        restored = 0
        for path in self._shortcut_paths("all"):
            if os.path.exists(path):
                try:
                    sc = shell.CreateShortCut(path)
                    if "--proxy-server=" in sc.Arguments:
                        sc.Arguments = ""
                        sc.save()
                        restored += 1
                except:
                    pass
        return restored

    # ── Tarayıcı başlatma ────────────────────────────────────────────────────
    def launch_browser(self, browser):
        wifi_sel = self.wifi_combo.get()
        if not wifi_sel:
            return
        wifi_ip = wifi_sel.split(" - ")[1]

        def find(paths):
            for p in paths:
                if os.path.exists(p): return p
            return None

        chrome_exe  = find([r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                             r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"])
        firefox_exe = find([r"C:\Program Files\Mozilla Firefox\firefox.exe",
                             r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"])
        launched = []

        if browser in ("chrome", "all"):
            if chrome_exe:
                subprocess.Popen([chrome_exe, f"--proxy-server={wifi_ip}:8888"])
                launched.append("Chrome")
            else:
                self.log("warn", "Chrome bulunamadı")

        if browser in ("firefox", "all"):
            if firefox_exe:
                subprocess.Popen([firefox_exe])
                launched.append("Firefox")
            else:
                self.log("warn", "Firefox bulunamadı")

        if launched:
            self.log("success", f"{', '.join(launched)} WiFi üzerinden başlatıldı")

    # ── Sistem başlat ────────────────────────────────────────────────────────
    def start_system(self):
        wifi_sel = self.wifi_combo.get()
        eth_sel  = self.eth_combo.get()
        if not wifi_sel or not eth_sel:
            messagebox.showerror("Hata", "WiFi ve Ethernet seçmelisiniz!")
            return

        wifi_ip  = wifi_sel.split(" - ")[1]
        eth_ip   = eth_sel.split(" - ")[1]
        eth_name = eth_sel.split(" - ")[0]

        if wifi_ip == eth_ip:
            messagebox.showerror("Hata",
                "WiFi ve Ethernet için farklı arayüzler seçmelisiniz!\n"
                "Aynı IP adresini iki kez seçemezsiniz.")
            return

        self.status.delete(1.0, tk.END)
        self.log("dim",     "─" * 48)
        self.log("info",    "Network Manager Pro v2 başlatılıyor...")
        self.log("dim",     "─" * 48)

        self._eth_name = eth_name
        subprocess.run(
            ["netsh", "interface", "ip", "set", "interface", eth_name, "metric=10"],
            capture_output=True
        )
        self.log("success", f"Ethernet varsayılan yapıldı  →  {eth_name}")

        self.proxy = WiFiProxy(wifi_ip, 8888)
        self.proxy_thread = threading.Thread(target=self.proxy.start, daemon=True)
        self.proxy_thread.start()
        self.log("success", f"WiFi proxy aktif  \u2192  {wifi_ip}:8888")

        # Seçili tarayıcı kısayollarını hemen yamala
        browser = self._get_selected_browser()
        if browser and self.patch_shortcuts.get():
            n = self.patch_browser_shortcuts(wifi_ip, browser)
            if n:
                self.log("success", f"{n} tarayıcı kısayolu güncellendi  (her açılışta WiFi kullanır)")
            else:
                self.log("dim", "Kısayol bulunamadı veya zaten ayarlı")

        # Firefox profil proxy ayarı
        if browser in ("firefox", "all"):
            n = self.patch_firefox_proxy(wifi_ip)
            if n:
                self.log("success", f"Firefox proxy ayarlandı  ({n} profil)")
            else:
                self.log("warn", "Firefox profili bulunamadı — Firefox hiç açılmamış olabilir")
        self.log("dim",     "─" * 48)
        self.log("info",    f"Tarayıcılar  →  WiFi  ({wifi_ip})")
        self.log("info",    f"Diğer trafik →  Ethernet  ({eth_name})")
        self.log("dim",     "─" * 48)

        self._start_btn.disable()
        self._stop_btn.enable()
        self.is_running = True
        self._set_badge(True)
        if self.tray_icon:
            self.tray_icon.icon = self._make_tray_icon(True)
        self.save_config()

    # ── Sistem durdur ────────────────────────────────────────────────────────
    def stop_system(self):
        if not self.is_running:
            return
        self.status.delete(1.0, tk.END)
        self.log("info", "Sistem durduruluyor...")

        if self.proxy:
            self.proxy.stop()
            self.log("success", "Proxy durduruldu")

        if self.patch_shortcuts.get():
            n = self.restore_browser_shortcuts()
            if n:
                self.log("success", f"{n} tarayıcı kısayolu eski haline getirildi")

        n = self.restore_firefox_proxy()
        if n:
            self.log("success", f"Firefox proxy temizlendi  ({n} profil)")

        if self._eth_name:
            subprocess.run(
                ["netsh", "interface", "ip", "set", "interface", self._eth_name, "metric=automatic"],
                capture_output=True
            )
            subprocess.run(["ipconfig", "/release", self._eth_name], capture_output=True)
            subprocess.run(["ipconfig", "/renew",   self._eth_name], capture_output=True)
            self.log("success", f"Ethernet metric sıfırlandı, IP yenilendi  →  {self._eth_name}")
            self._eth_name = None

        self.log("dim", "─" * 48)
        self.log("warn", "Sistem durduruldu")

        self._start_btn.enable()
        self._stop_btn.disable()
        self.is_running = False
        self._set_badge(False)
        if self.tray_icon:
            self.tray_icon.icon = self._make_tray_icon(False)

    # ── Config ───────────────────────────────────────────────────────────────
    def save_config(self):
        cfg = {
            "wifi":             self.wifi_combo.get(),
            "ethernet":         self.eth_combo.get(),
            "patch_shortcuts":  self.patch_shortcuts.get(),
            "auto_start":       self.auto_start.get(),
            "minimize_tray":    self.minimize_tray.get(),
            "use_chrome":       self.use_chrome.get(),
            "use_firefox":      self.use_firefox.get(),
            "use_all":          self.use_all.get(),
        }
        with open(self.config_file, "w") as f:
            json.dump(cfg, f)

    def load_config(self):
        if not os.path.exists(self.config_file):
            return
        try:
            with open(self.config_file) as f:
                cfg = json.load(f)

            def set_combo(combo, saved):
                if not saved:
                    return
                values = combo["values"]
                # Önce tam eşleşme dene
                if saved in values:
                    combo.set(saved)
                    return
                # Tam eşleşme yoksa arayüz adına göre eşleştir (IP değişmiş olabilir)
                saved_name = saved.split(" - ")[0]
                for v in values:
                    if v.split(" - ")[0] == saved_name:
                        combo.set(v)
                        return

            set_combo(self.wifi_combo, cfg.get("wifi"))
            set_combo(self.eth_combo,  cfg.get("ethernet"))

            self.patch_shortcuts.set(cfg.get("patch_shortcuts", True))
            self.auto_start.set(cfg.get("auto_start", False))
            self.minimize_tray.set(cfg.get("minimize_tray", True))
            self.use_chrome.set(cfg.get("use_chrome", False))
            self.use_firefox.set(cfg.get("use_firefox", False))
            self.use_all.set(cfg.get("use_all", False))
            self._refresh_all_widgets(self.root)
        except:
            pass

    # ── Otomatik başlatma ────────────────────────────────────────────────────
    def toggle_autostart(self):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "NetworkManagerPro"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if self.auto_start.get():
                script_path = os.path.abspath(__file__)
                python_exe  = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
                if not os.path.exists(python_exe):
                    python_exe = sys.executable
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ,
                                  f'"{python_exe}" "{script_path}" --autostart')
                self.log("success", "Otomatik başlatma aktif  (systray'de gizli çalışacak)")
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                    self.log("warn", "Otomatik başlatma devre dışı")
                except:
                    pass
            winreg.CloseKey(key)
            self.save_config()
        except Exception as e:
            messagebox.showerror("Hata", f"Otomatik başlatma ayarlanamadı:\n{e}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = NetworkManager(root)
    root.mainloop()
