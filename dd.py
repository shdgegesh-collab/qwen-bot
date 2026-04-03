import customtkinter as ctk
import asyncio
import os
import threading
import shutil
import hashlib
import requests
import json
import csv
import re
import time
import random
import logging
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox
from functools import wraps

# Импортируем Telethon
from telethon import TelegramClient, events
from telethon.tl.types import ChannelParticipantsAdmins, UserStatusRecently, UserStatusOnline
from telethon.tl.functions.messages import AddChatUserRequest, ImportChatInviteRequest
from telethon.errors import FloodWaitError, ChatAdminRequiredError, UserPrivacyRestrictedError, UsernameNotOccupiedError, InviteHashExpiredError, InviteHashInvalidError, UserAlreadyParticipantError

# --- НАСТРОЙКИ ---
API_ID = 36925315  # ЗАМЕНИ НА СВОЙ
API_HASH = "e4c7b45f2331be96a242cce6e3b3c1c1"  # ЗАМЕНИ НА СВОЙ
LICENSE_URL = "https://gist.githubusercontent.com/shdgegesh-collab/d1d6496033f3246f84c452cbf7d659d4/raw/keys"

# Настройки прокси для обхода блокировок (опционально)
# Заполните если нужен прокси для подключения:
# Формат: ("socks5", "ip", port, True, "user", "pass")

# ⚠️ ВАЖНО: Если используете VPN - установите PROXY_SETTINGS = None
# VPN сам обойдёт блокировки, прокси не нужен!

# ВАШ ПРОКСИ (от продавца) - ОТКЛЮЧЁН для теста с VPN
PROXY_SETTINGS = None  # ("socks5", "200.10.34.49", 50101, True, "vitalysilin", "Idq3vsxG8R")

# РЕКОМЕНДАЦИЯ: Включите VPN и оставьте PROXY_SETTINGS = None
# Если VPN не работает для Python - используйте MTProxy ниже

# MTProxy (лучше обходят блокировки чем SOCKS5)
# Актуальные секреты: https://t.me/mtproxy, https://t.me/proxylist
# Обновлённые рабочие MTProxy (декабрь 2024):
MT_PROXIES = [
    # Формат: (host, port, secret)
    ("138.204.223.132", 443, "ee000000000000000000000000000000ee"),
    ("146.190.212.200", 443, "ee000000000000000000000000000000ee"),
    ("154.204.183.212", 443, "ee000000000000000000000000000000ee"),
    ("tweb.ru", 443, "dd000000000000000000000000000000dd"),
    ("mtp10.hosting", 443, "dd000000000000000000000000000000dd"),
]

# Список бесплатных прокси для авто-выбора (скорее всего не работают)
FREE_PROXIES = [
    # Пробуем эти (обновляются раз в неделю)
    ("socks5", "192.111.139.165", 1080, True, "free", "free"),
    ("socks5", "185.169.234.122", 41486, True, "uG4514", "B55lqk"),
    ("socks5", "51.158.180.133", 9999, True, "xZ2711", "Z92926"),
    ("socks5", "195.154.255.118", 8080, True, "free", "free"),
    ("socks5", "103.149.194.26", 3265, True, "free", "free"),
]

# MTProxy (лучше работают с Telegram, обходят блокировки)
# Секреты можно найти в каналах типа @mtproxy, @proxylist
MT_PROXIES = [
    # Формат: (host, port, secret)
    # Примеры рабочих (обновляются):
    # ("proxy.nntime.com", 443, "dd000000000000000000000000000000dd"),
]

def get_working_proxy():
    """Пытается найти рабочий прокси из списка"""
    import socket
    for proxy in FREE_PROXIES:
        try:
            # Быстрая проверка доступности
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((proxy[1], proxy[2]))
            sock.close()
            if result == 0:
                logger.info(f"✅ Прокси доступен: {proxy[1]}:{proxy[2]}")
                return proxy
        except:
            continue
    logger.warning("⚠️ Ни один бесплатный прокси не доступен")
    return None

# Альтернативные серверы Telegram для подключения
TELETHON_CONNECTIONS = [
    # Основные серверы
    {"ip": "149.154.167.50", "port": 443},
    {"ip": "149.154.167.51", "port": 443},
    {"ip": "149.154.167.52", "port": 443},
    {"ip": "149.154.167.53", "port": 443},
    {"ip": "149.154.167.54", "port": 443},
    # Альтернативные
    {"ip": "149.154.167.50", "port": 80},
    {"ip": "149.154.167.51", "port": 80},
]

# === НАСТРОЙКИ ДИЗАЙНА ===
class DesignConfig:
    """Конфигурация современного дизайна"""
    # Цветовая палитра
    PRIMARY_COLOR = "#2563eb"        # Современный синий
    SECONDARY_COLOR = "#1e40af"      # Темно-синий
    ACCENT_COLOR = "#3b82f6"         # Яркий синий
    SUCCESS_COLOR = "#10b981"        # Изумрудный
    WARNING_COLOR = "#f59e0b"        # Янтарный
    DANGER_COLOR = "#ef4444"         # Красный
    BG_DARK = "#0f172a"              # Темный фон
    BG_CARD = "#1e293b"              # Фон карточек
    BG_SIDEBAR = "#1e293b"           # Фон сайдбара
    TEXT_PRIMARY = "#f1f5f9"         # Основной текст
    TEXT_SECONDARY = "#94a3b8"       # Вторичный текст
    
    # Шрифты
    FONT_FAMILY = "Segoe UI"
    FONT_TITLE = (FONT_FAMILY, 24, "bold")
    FONT_HEADER = (FONT_FAMILY, 16, "bold")
    FONT_SUBHEADER = (FONT_FAMILY, 14, "bold")
    FONT_NORMAL = (FONT_FAMILY, 12)
    FONT_SMALL = (FONT_FAMILY, 10)
    
    # Размеры
    SIDEBAR_WIDTH = 260
    BUTTON_HEIGHT = 40
    BUTTON_CORNER = 8
    CARD_CORNER = 12
    PADDING_LARGE = 20
    PADDING_MEDIUM = 15
    PADDING_SMALL = 10

# Настройки логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/arbitrage_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Rate limiting настройки
RATE_LIMIT_DELAY = 1.0  # Задержка между запросами к API
PARSER_BATCH_SIZE = 100  # Размер пакета для парсинга
INVITE_DELAY_MIN = 30  # Минимальная задержка между приглашениями (сек)
INVITE_DELAY_MAX = 60  # Максимальная задержка между приглашениями (сек)
SPAM_DELAY_MIN = 60    # Минимальная задержка между сообщениями
SPAM_DELAY_MAX = 120   # Максимальная задержка между сообщениями


def get_hwid():
    try:
        import subprocess
        cmd = 'wmic csproduct get uuid'
        uuid = subprocess.check_output(cmd, shell=True).decode().split('\n')[1].strip()
        return hashlib.sha256(uuid.encode()).hexdigest()
    except:
        return "default_hwid"


def create_telethon_client(session_path, api_id=API_ID, api_hash=API_HASH, proxy=None):
    """Создает клиента Telethon с поддержкой прокси и альтернативных серверов"""
    from telethon import TelegramClient
    from telethon.network import ConnectionTcpFull
    
    # Используем прокси если указан
    use_proxy = proxy or PROXY_SETTINGS
    
    # Если прокси не указан, пробуем MTProxy (лучше для Telegram)
    if not use_proxy and MT_PROXIES:
        logger.info("🔄 Пробуем MTProxy...")
        for mt_proxy in MT_PROXIES:
            try:
                # Проверяем доступность
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((mt_proxy[0], mt_proxy[1]))
                sock.close()
                if result == 0:
                    logger.info(f"✅ MTProxy доступен: {mt_proxy[0]}:{mt_proxy[1]}")
                    # Конвертируем MTProxy в формат для Telethon
                    use_proxy = {
                        'proxy_type': 'mtproto',
                        'addr': mt_proxy[0],
                        'port': mt_proxy[1],
                        'secret': mt_proxy[2]
                    }
                    break
            except:
                continue
    
    # Если MTProxy не доступен, пробуем бесплатные SOCKS5
    if not use_proxy:
        use_proxy = get_working_proxy()
    
    # Создаем клиента с альтернативными серверами
    client = TelegramClient(
        session_path,
        api_id,
        api_hash,
        proxy=use_proxy,
        connection=ConnectionTcpFull,
        flood_sleep_threshold=60,
        raise_last_call_error=False,
        auto_reconnect=True,
        retry_delay=5
    )
    
    return client


def add_bindings(widget):
    """Добавляет горячие клавиши для копирования/вставки"""
    def copy_text(event=None):
        try:
            if isinstance(widget, ctk.CTkTextbox):
                widget.event_generate("<<Copy>>")
            else:
                widget.clipboard_clear()
                widget.clipboard_append(widget.get())
        except:
            pass
        return "break"
    
    def paste_text(event=None):
        try:
            if isinstance(widget, ctk.CTkTextbox):
                widget.event_generate("<<Paste>>")
            else:
                text = widget.clipboard_get()
                widget.insert(len(widget.get()), text)
        except:
            pass
        return "break"
    
    def cut_text(event=None):
        try:
            if isinstance(widget, ctk.CTkTextbox):
                widget.event_generate("<<Cut>>")
            else:
                widget.clipboard_clear()
                widget.clipboard_append(widget.get())
                widget.delete(0, len(widget.get()))
        except:
            pass
        return "break"
    
    def select_all(event=None):
        try:
            if isinstance(widget, ctk.CTkTextbox):
                widget.tag_add("sel", "1.0", "end")
            else:
                widget.select_range(0, 'end')
        except:
            pass
        return "break"
    
    widget.bind("<Control-v>", paste_text)
    widget.bind("<Control-c>", copy_text)
    widget.bind("<Control-x>", cut_text)
    widget.bind("<Control-a>", select_all)


def rate_limit(delay=RATE_LIMIT_DELAY):
    """Декоратор для ограничения частоты запросов"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            await asyncio.sleep(delay)
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# --- ОКНО АВТОРИЗАЦИИ ---
class LoginWindow(ctk.CTk):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.title("Arbitrage Pro - Авторизация")
        self.geometry("400x480")
        self.resizable(False, False)
        
        # Настройка темы - светлая
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # Белый фон всего окна
        main_frame = ctk.CTkFrame(self, fg_color="white")
        main_frame.pack(fill="both", expand=True)
        
        # Заголовок
        header = ctk.CTkFrame(main_frame, fg_color="white")
        header.pack(fill="x", padx=30, pady=(30, 20))
        
        ctk.CTkLabel(header, text="🔐", font=("Segoe UI Emoji", 36)).pack()
        ctk.CTkLabel(header, text="ARBITRAGE PRO", 
                     font=("Arial", 22, "bold"), 
                     text_color="#2563eb").pack()
        
        # Поле ввода
        entry_frame = ctk.CTkFrame(main_frame, fg_color="white")
        entry_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(entry_frame, text="Лицензионный ключ:", 
                     font=("Arial", 11, "bold"),
                     text_color="#374151").pack(anchor="w")
        
        self.entry_key = ctk.CTkEntry(entry_frame, 
                                      placeholder_text="оставьте пустым для теста",
                                      font=("Arial", 11),
                                      height=38,
                                      corner_radius=6,
                                      border_width=2,
                                      border_color="#2563eb",
                                      fg_color="#f9fafb")
        self.entry_key.pack(fill="x", pady=5)
        add_bindings(self.entry_key)
        
        # HWID
        self.hwid = get_hwid()
        
        hwid_frame = ctk.CTkFrame(main_frame, fg_color="#f3f4f6", corner_radius=6)
        hwid_frame.pack(fill="x", padx=30, pady=15)
        
        ctk.CTkLabel(hwid_frame, text="ID устройства:", 
                     font=("Arial", 9, "bold"),
                     text_color="#6b7280").pack(anchor="w", padx=12, pady=(8, 4))
        
        ctk.CTkLabel(hwid_frame, 
                     text=self.hwid,
                     font=("Consolas", 8),
                     text_color="#2563eb",
                     anchor="w",
                     wraplength=320).pack(fill="x", padx=12, pady=(0, 8))
        
        ctk.CTkButton(hwid_frame,
                      text="📋 Копировать",
                      command=self.copy_hwid,
                      font=("Arial", 10, "bold"),
                      height=26,
                      width=120,
                      corner_radius=5,
                      fg_color="#2563eb",
                      hover_color="#1d4ed8").pack(pady=(0, 8))
        
        # Кнопка входа
        self.btn_check = ctk.CTkButton(main_frame, 
                                       text="ВОЙТИ",
                                       command=self.check,
                                       font=("Arial", 13, "bold"),
                                       height=42,
                                       corner_radius=8,
                                       fg_color="#16a34a",
                                       hover_color="#15803d")
        self.btn_check.pack(fill="x", padx=30, pady=15)
        
        # Статус
        self.status = ctk.CTkLabel(main_frame, text="", 
                                   font=("Arial", 10, "bold"),
                                   text_color="#dc2626")
        self.status.pack(pady=5)
        
        # Подсказка
        ctk.CTkLabel(main_frame, 
                     text="💡 Оставьте поле пустым для входа",
                     font=("Arial", 9),
                     text_color="#9ca3af").pack(side="bottom", pady=15)

    def copy_hwid(self):
        self.clipboard_clear()
        self.clipboard_append(self.hwid)
        self.status.configure(text="✅ Скопировано!", text_color="#16a34a")
        self.after(2000, lambda: self.status.configure(text="", text_color="#dc2626"))

    def check(self):
        key = self.entry_key.get().strip().upper()
        
        if key == "TEST" or key == "":
            logger.info("🔧 ТЕСТОВЫЙ РЕЖИМ")
            self.destroy()
            self.on_success()
            return
        
        try:
            res = requests.get(LICENSE_URL, timeout=10)
            if res.status_code == 200:
                for line in res.text.splitlines():
                    if ":" in line:
                        k, h = line.split(":", 1)
                        if key == k.strip().upper() and (h.strip() == "NEW" or h.strip() == self.hwid):
                            self.destroy()
                            self.on_success()
                            return
                self.status.configure(text="❌ Ключ неверен")
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            self.status.configure(text="⚠️ Нет сети")


# --- ОСНОВНОЕ ПРИЛОЖЕНИЕ ---
class ArbitrageApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Arbitrage Pro v2.0")
        self.geometry("1400x950")
        self.minsize(1200, 800)
        
        # Конфигурация сетки
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Top bar - фиксированная высота
        self.grid_rowconfigure(1, weight=1)  # Контент - расширяется
        self.grid_rowconfigure(2, weight=0)  # Log panel - фиксированная высота

        # Пути к папкам
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.sessions_dir = os.path.join(self.base_dir, "sessions")
        self.parsed_dir = os.path.join(self.base_dir, "parsed_data")
        self.proxy_dir = os.path.join(self.base_dir, "proxy_settings")
        self.logs_dir = os.path.join(self.base_dir, "logs")

        for d in [self.sessions_dir, self.parsed_dir, self.proxy_dir, self.logs_dir]:
            if not os.path.exists(d):
                os.makedirs(d)

        self.current_session = "ВСЕ"
        self.selected_db_path = ""
        self.is_spam_active = False
        self.is_ar_active = False
        self.is_invite_active = False
        self.clients_cache = {}

        # Переменные для UI элементов
        self.menu_buttons = {}
        self.active_button = None

        # Устанавливаем тему ДО создания виджетов
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # Устанавливаем цвет фона главного окна
        self.configure(fg_color=DesignConfig.BG_DARK)

        self.setup_ui()
        self.refresh_sessions()

    def log(self, text, level="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        color_map = {
            "info": "#3b82f6",
            "success": "#10b981",
            "warning": "#f59e0b",
            "error": "#ef4444"
        }
        color = color_map.get(level, "#94a3b8")
        
        formatted_text = f"[{timestamp}] {text}"
        self.log_view.insert("end", f"> {formatted_text}\n", "color")
        self.log_view.tag_config("color", foreground=color)
        self.log_view.see("end")

        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.log(log_level, text)

    def setup_ui(self):
        # === SIDEBAR ===
        self.sidebar = ctk.CTkFrame(self, width=DesignConfig.SIDEBAR_WIDTH, 
                                    corner_radius=0,
                                    fg_color=DesignConfig.BG_SIDEBAR)
        self.sidebar.grid(row=0, rowspan=2, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Логотип в sidebar
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=80)
        logo_frame.pack(fill="x", padx=20, pady=20)
        logo_frame.pack_propagate(False)
        
        ctk.CTkLabel(logo_frame, text="⚡", font=("Segoe UI Emoji", 36)).pack()
        ctk.CTkLabel(logo_frame, text="ARBITRAGE", 
                     font=("Segoe UI", 18, "bold"),
                     text_color=DesignConfig.TEXT_PRIMARY).pack()
        ctk.CTkLabel(logo_frame, text="PRO v2.0", 
                     font=("Segoe UI", 10),
                     text_color=DesignConfig.PRIMARY_COLOR).pack()

        # Разделитель
        ctk.CTkFrame(self.sidebar, height=2, fg_color=DesignConfig.BG_DARK).pack(fill="x", padx=20, pady=10)

        # Секция аккаунтов
        ctk.CTkLabel(self.sidebar, text="💼 АККАУНТЫ", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_SECONDARY,
                     anchor="w").pack(fill="x", padx=20, pady=(15, 10))

        self.session_menu = ctk.CTkOptionMenu(self.sidebar, 
                                              values=["ВСЕ"],
                                              command=lambda v: setattr(self, 'current_session', v),
                                              font=DesignConfig.FONT_NORMAL,
                                              height=40,
                                              corner_radius=8,
                                              fg_color=DesignConfig.BG_CARD,
                                              button_color=DesignConfig.PRIMARY_COLOR,
                                              button_hover_color=DesignConfig.SECONDARY_COLOR)
        self.session_menu.pack(fill="x", padx=20, pady=5)

        # Кнопки управления аккаунтами
        btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkButton(btn_frame, text="🔄", command=self.refresh_sessions,
                      width=50, height=36, corner_radius=6,
                      fg_color=DesignConfig.BG_CARD,
                      hover_color=DesignConfig.PRIMARY_COLOR).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="➕", command=self.add_session,
                      width=50, height=36, corner_radius=6,
                      fg_color=DesignConfig.BG_CARD,
                      hover_color=DesignConfig.PRIMARY_COLOR).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="✓", command=lambda: self.run_async(self.check_all_sessions),
                      width=50, height=36, corner_radius=6,
                      fg_color=DesignConfig.BG_CARD,
                      hover_color=DesignConfig.SUCCESS_COLOR).pack(side="left", padx=2)

        # Разделитель
        ctk.CTkFrame(self.sidebar, height=2, fg_color=DesignConfig.BG_DARK).pack(fill="x", padx=20, pady=20)

        # Меню
        ctk.CTkLabel(self.sidebar, text="📱 МЕНЮ",
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_SECONDARY,
                     anchor="w").pack(fill="x", padx=20, pady=(0, 10))

        menu_items = [
            ("Парсинг", "🔍"),
            ("Поиск чатов", "📢"),
            ("Инвайтер", "👥"),
            ("Вход по ссылке", "🔗"),
            ("Рассылка", "📨"),
            ("Прогрев", "🔥"),
            ("Автоответчик", "🤖"),
            ("Контакты", "📞"),
            ("Статистика", "📊"),
            ("Прокси", "🌐")
        ]
        
        for i, (name, icon) in enumerate(menu_items):
            btn = ctk.CTkButton(self.sidebar,
                                text=f"  {icon}  {name}",
                                command=lambda n=name: self.show_frame(n),
                                anchor="w",
                                height=40,
                                corner_radius=0,
                                font=DesignConfig.FONT_NORMAL,
                                fg_color="transparent",
                                hover_color=DesignConfig.BG_CARD)
            btn.pack(fill="x", padx=0, pady=0)
            
            # Разделительная линия после каждой кнопки
            separator = ctk.CTkFrame(self.sidebar, height=1, fg_color=DesignConfig.BG_DARK)
            separator.pack(fill="x", padx=15, pady=0)
            self.menu_buttons[name] = btn

        # Статус бар внизу sidebar
        status_bar = ctk.CTkFrame(self.sidebar, fg_color=DesignConfig.BG_DARK, 
                                  corner_radius=8)
        status_bar.pack(side="bottom", fill="x", padx=15, pady=15)
        
        self.status_indicator = ctk.CTkLabel(status_bar, text="🟢", font=("Segoe UI Emoji", 16))
        self.status_indicator.pack(side="left", padx=10, pady=10)
        ctk.CTkLabel(status_bar, text="Готов к работе", 
                     font=DesignConfig.FONT_SMALL,
                     text_color=DesignConfig.TEXT_SECONDARY).pack(side="left", pady=10)

        # === MAIN CONTENT AREA ===
        # Верхняя панель
        self.top_bar = ctk.CTkFrame(self, height=70, corner_radius=0,
                                    fg_color=DesignConfig.BG_CARD)
        self.top_bar.grid(row=0, column=1, sticky="ew")
        self.top_bar.grid_propagate(False)

        self.page_title = ctk.CTkLabel(self.top_bar, text="Парсинг",
                                        font=DesignConfig.FONT_TITLE,
                                        text_color=DesignConfig.TEXT_PRIMARY)
        self.page_title.pack(side="left", padx=30, pady=20)

        self.session_info = ctk.CTkLabel(self.top_bar, text="",
                                          font=DesignConfig.FONT_NORMAL,
                                          text_color=DesignConfig.TEXT_SECONDARY)
        self.session_info.pack(side="right", padx=30, pady=25)

        # Контейнер для контента - в row 1
        self.content_scroll = ctk.CTkScrollableFrame(self, fg_color=DesignConfig.BG_CARD,
                                                     corner_radius=0)
        self.content_scroll.grid(row=1, column=1, sticky="nsew")

        self.frames = {}
        for name, _ in menu_items:
            f = ctk.CTkFrame(self.content_scroll, fg_color=DesignConfig.BG_CARD)
            self.frames[name] = f
            self.build_frame(name, f)

        # === LOG PANEL === в row 2
        self.log_frame = ctk.CTkFrame(self, height=200,
                                      fg_color=DesignConfig.BG_CARD)
        self.log_frame.grid(row=2, column=0, columnspan=2, sticky="ew")

        log_header = ctk.CTkFrame(self.log_frame, fg_color="transparent", height=40)
        log_header.pack(fill="x")
        log_header.pack_propagate(False)

        ctk.CTkLabel(log_header, text="📋 Журнал событий",
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(side="left", padx=20, pady=10)

        ctk.CTkButton(log_header, text="🗑 Очистить", command=self.clear_log,
                      height=30, width=100, corner_radius=6,
                      fg_color=DesignConfig.DANGER_COLOR,
                      hover_color="#dc2626").pack(side="right", padx=5, pady=5)
        
        ctk.CTkButton(log_header, text="📋 Копировать лог", command=self.copy_log,
                      height=30, width=120, corner_radius=6,
                      fg_color=DesignConfig.PRIMARY_COLOR,
                      hover_color=DesignConfig.SECONDARY_COLOR).pack(side="right", padx=5, pady=5)

        self.log_view = ctk.CTkTextbox(self.log_frame, font=("Consolas", 11))
        self.log_view.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        add_bindings(self.log_view)

        self.show_frame("Парсинг")

    def build_frame(self, name, f):
        if name == "Парсинг":
            self.build_parser_frame(f)
        elif name == "Поиск чатов":
            self.build_chat_search_frame(f)
        elif name == "Инвайтер":
            self.build_inviter_frame(f)
        elif name == "Вход по ссылке":
            self.build_join_by_link_frame(f)
        elif name == "Рассылка":
            self.build_spam_frame(f)
        elif name == "Прогрев":
            self.build_warm_frame(f)
        elif name == "Автоответчик":
            self.build_autoresponder_frame(f)
        elif name == "Контакты":
            self.build_contacts_frame(f)
        elif name == "Статистика":
            self.build_stats_frame(f)
        elif name == "Прокси":
            self.build_proxy_frame(f)

    # ==================== ПАРСИНГ ====================
    def build_parser_frame(self, f):
        # Заголовок раздела
        header_frame = ctk.CTkFrame(f, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text="🔍 Парсинг участников", 
                     font=DesignConfig.FONT_TITLE,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(header_frame, text="Сбор участников из чатов Telegram", 
                     font=DesignConfig.FONT_NORMAL,
                     text_color=DesignConfig.TEXT_SECONDARY).pack(side="left", padx=20, pady=25)

        # Карточка настроек
        settings_card = ctk.CTkFrame(f, fg_color=DesignConfig.BG_CARD, 
                                     corner_radius=DesignConfig.CARD_CORNER)
        settings_card.pack(fill="x", pady=10)
        
        # Внутренний фрейм для отступов
        inner = ctk.CTkFrame(settings_card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25, pady=20)

        # Row 1: Целевой чат
        input_row = ctk.CTkFrame(inner, fg_color="transparent")
        input_row.pack(fill="x", pady=10)
        
        ctk.CTkLabel(input_row, text="📢", font=("Segoe UI Emoji", 20)).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(input_row, text="Целевой чат:", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(side="left")
        
        self.p_entry = ctk.CTkEntry(inner, 
                                    placeholder_text="@durov или https://t.me/durov",
                                    font=DesignConfig.FONT_NORMAL,
                                    height=45,
                                    corner_radius=8,
                                    border_width=1,
                                    border_color=DesignConfig.BG_DARK)
        self.p_entry.pack(fill="x", pady=10)
        add_bindings(self.p_entry)

        # Row 2: Лимит и экспорт
        options_row = ctk.CTkFrame(inner, fg_color="transparent")
        options_row.pack(fill="x", pady=15)
        
        left_col = ctk.CTkFrame(options_row, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True)
        
        ctk.CTkLabel(left_col, text="👥 Лимит участников:", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(anchor="w")
        self.parse_limit = ctk.CTkEntry(left_col, 
                                        placeholder_text="1000",
                                        font=DesignConfig.FONT_NORMAL,
                                        width=150,
                                        height=40,
                                        corner_radius=8)
        self.parse_limit.pack(pady=5)
        self.parse_limit.insert(0, "1000")
        
        right_col = ctk.CTkFrame(options_row, fg_color="transparent")
        right_col.pack(side="right")
        
        ctk.CTkLabel(right_col, text="💾 Формат экспорта:", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(anchor="w")
        self.export_format = ctk.CTkOptionMenu(right_col, 
                                               values=["TXT", "CSV", "JSON"],
                                               font=DesignConfig.FONT_NORMAL,
                                               height=40,
                                               corner_radius=8,
                                               fg_color=DesignConfig.BG_DARK,
                                               button_color=DesignConfig.PRIMARY_COLOR)
        self.export_format.pack(pady=5)
        self.export_format.set("TXT")

        # Карточка фильтров
        filters_card = ctk.CTkFrame(f, fg_color=DesignConfig.BG_CARD, 
                                    corner_radius=DesignConfig.CARD_CORNER)
        filters_card.pack(fill="x", pady=10)
        
        filters_inner = ctk.CTkFrame(filters_card, fg_color="transparent")
        filters_inner.pack(fill="both", expand=True, padx=25, pady=20)
        
        ctk.CTkLabel(filters_inner, text="🎛 Фильтры участников", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(anchor="w", pady=(0, 15))
        
        filters_grid = ctk.CTkFrame(filters_inner, fg_color="transparent")
        filters_grid.pack(fill="x")
        
        self.filter_bots = ctk.CTkCheckBox(filters_grid, 
                                           text="Исключить ботов",
                                           font=DesignConfig.FONT_NORMAL,
                                           checkbox_width=20,
                                           checkbox_height=20)
        self.filter_bots.grid(row=0, column=0, padx=10, pady=8, sticky="w")
        self.filter_bots.select()

        self.filter_deleted = ctk.CTkCheckBox(filters_grid, 
                                              text="Исключить удаленные аккаунты",
                                              font=DesignConfig.FONT_NORMAL,
                                              checkbox_width=20,
                                              checkbox_height=20)
        self.filter_deleted.grid(row=0, column=1, padx=10, pady=8, sticky="w")
        self.filter_deleted.select()

        self.filter_admins = ctk.CTkCheckBox(filters_grid, 
                                             text="Исключить админов",
                                             font=DesignConfig.FONT_NORMAL,
                                             checkbox_width=20,
                                             checkbox_height=20)
        self.filter_admins.grid(row=1, column=0, padx=10, pady=8, sticky="w")
        self.filter_admins.select()

        self.filter_recent = ctk.CTkCheckBox(filters_grid, 
                                             text="Только активные недавно",
                                             font=DesignConfig.FONT_NORMAL,
                                             checkbox_width=20,
                                             checkbox_height=20)
        self.filter_recent.grid(row=1, column=1, padx=10, pady=8, sticky="w")

        # Кнопки действий
        actions_card = ctk.CTkFrame(f, fg_color="transparent")
        actions_card.pack(fill="x", pady=25)

        btn1 = ctk.CTkButton(actions_card,
                             text="🚀 НАЧАТЬ ПАРСИНГ",
                             font=DesignConfig.FONT_SUBHEADER,
                             height=50,
                             corner_radius=10,
                             fg_color=DesignConfig.PRIMARY_COLOR,
                             hover_color=DesignConfig.SECONDARY_COLOR,
                             command=lambda: self.run_async(self.do_parse))
        btn1.pack(side="left", padx=10)

        btn2 = ctk.CTkButton(actions_card,
                             text="🗑 Очистить базы",
                             font=DesignConfig.FONT_NORMAL,
                             height=50,
                             width=140,
                             corner_radius=10,
                             fg_color=DesignConfig.DANGER_COLOR,
                             hover_color="#dc2626",
                             command=self.clear_parsed)
        btn2.pack(side="left", padx=10)

        btn3 = ctk.CTkButton(actions_card,
                             text="📂 Открыть папку",
                             font=DesignConfig.FONT_NORMAL,
                             height=50,
                             width=140,
                             corner_radius=10,
                             fg_color=DesignConfig.BG_CARD,
                             hover_color=DesignConfig.PRIMARY_COLOR,
                             command=lambda: os.startfile(self.parsed_dir))
        btn3.pack(side="left", padx=10)

        btn4 = ctk.CTkButton(actions_card,
                             text="🌐 Прокси",
                             font=DesignConfig.FONT_NORMAL,
                             height=50,
                             width=100,
                             corner_radius=10,
                             fg_color="#b87333",
                             hover_color="#9a602b",
                             command=lambda: self.show_frame("Прокси"))
        btn4.pack(side="left", padx=10)

        # Статус
        self.parse_status = ctk.CTkLabel(f, text="",
                                         font=DesignConfig.FONT_NORMAL,
                                         text_color=DesignConfig.WARNING_COLOR)
        self.parse_status.pack(pady=15)
        
        # Подсказка про прокси
        ctk.CTkLabel(f,
                     text="⚠️ Если ошибка подключения - настройте прокси в разделе 🌐 Прокси",
                     font=("Arial", 9),
                     text_color="#888888").pack(pady=(0, 10))

    async def do_parse(self):
        target = self.p_entry.get().strip()
        if not target:
            self.log("⚠️ Введите юзернейм чата!", "warning")
            return

        # Очистка ввода от ссылки
        target = re.sub(r'https?://t\.me/', '', target)
        target = target.replace('@', '')

        accs = [f.replace(".session", "") for f in os.listdir(self.sessions_dir) if f.endswith(".session")]
        if not accs:
            self.log("⚠️ Нет файлов сессий в папке sessions!", "warning")
            return

        acc = accs[0] if self.current_session == "ВСЕ" else self.current_session
        session_path = os.path.join(self.sessions_dir, acc)
        proxy = self.get_proxy(acc)

        try:
            limit = int(self.parse_limit.get() or 1000)
        except ValueError:
            limit = 1000

        self.log(f"🚀 Запуск парсинга @{target} (лимит: {limit})")
        self.parse_status.configure(text="Парсинг...", text_color="orange")

        client = create_telethon_client(session_path, proxy=proxy)

        try:
            await client.connect()
            if not await client.is_user_authorized():
                self.log(f"❌ Аккаунт {acc} не авторизован", "error")
                await client.disconnect()
                return

            self.log(f"✅ Успешный вход как {acc}")

            # Получаем информацию о чате
            try:
                entity = await client.get_entity(target)
                self.log(f"📊 Чат найден: {entity.title} ({entity.id})")
            except Exception as e:
                self.log(f"❌ Чат не найден: {e}", "error")
                self.parse_status.configure(text="Ошибка", text_color="red")
                await client.disconnect()
                return

            collected_users = []
            stats = {
                'total': 0,
                'with_username': 0,
                'bots': 0,
                'deleted': 0,
                'admins': 0,
                'active_recently': 0
            }

            # Получаем админов для исключения
            admin_ids = set()
            if self.filter_admins.get():
                try:
                    admin_users = await client.get_participants(entity, filter=ChannelParticipantsAdmins)
                    admin_ids = {u.id for u in admin_users}
                    stats['admins'] = len(admin_ids)
                    self.log(f"👑 Найдено админов: {len(admin_ids)}")
                except Exception as e:
                    self.log(f"⚠️ Не удалось получить админов: {e}", "warning")

            self.log("🔄 Сбор участников...")
            
            # Парсинг участников
            offset = 0
            batch_size = PARSER_BATCH_SIZE
            
            while len(collected_users) < limit:
                try:
                    participants = await client.get_participants(
                        entity,
                        offset=offset,
                        limit=batch_size
                    )
                    
                    if not participants:
                        break

                    for user in participants:
                        stats['total'] += 1
                        
                        # Фильтры
                        if self.filter_bots.get() and user.bot:
                            stats['bots'] += 1
                            continue
                        if self.filter_deleted.get() and user.deleted:
                            stats['deleted'] += 1
                            continue
                        if user.id in admin_ids:
                            continue

                        # Проверка активности
                        is_active = False
                        if self.filter_recent.get():
                            if hasattr(user, 'status'):
                                if isinstance(user.status, (UserStatusOnline, UserStatusRecently)):
                                    is_active = True
                                    stats['active_recently'] += 1
                                else:
                                    continue
                            else:
                                continue
                        else:
                            is_active = True

                        if is_active and user.username:
                            collected_users.append({
                                'username': user.username,
                                'id': user.id,
                                'first_name': getattr(user, 'first_name', ''),
                                'last_name': getattr(user, 'last_name', ''),
                                'is_bot': user.bot,
                                'is_premium': getattr(user, 'premium', False)
                            })
                            stats['with_username'] += 1

                    offset += batch_size
                    self.log(f"📈 Обработано: {offset} участников (собрано: {len(collected_users)})")
                    
                    # Rate limiting
                    await asyncio.sleep(RATE_LIMIT_DELAY)
                    
                except FloodWaitError as e:
                    self.log(f"⏳ FloodWait: ждем {e.seconds} сек", "warning")
                    await asyncio.sleep(e.seconds + 5)
                except Exception as e:
                    self.log(f"⚠️ Ошибка при парсинге: {e}", "warning")
                    break

            # Парсинг сообщений для сбора активных
            if len(collected_users) < limit:
                self.log("🔄 Дополнительный сбор из сообщений...")
                try:
                    async for message in client.iter_messages(entity, limit=2000):
                        if len(collected_users) >= limit:
                            break
                        sender = await message.get_sender()
                        if sender and not sender.bot and not sender.deleted and sender.username:
                            if sender.username not in [u['username'] for u in collected_users]:
                                collected_users.append({
                                    'username': sender.username,
                                    'id': sender.id,
                                    'first_name': getattr(sender, 'first_name', ''),
                                    'last_name': getattr(sender, 'last_name', ''),
                                    'is_bot': sender.bot,
                                    'is_premium': getattr(sender, 'premium', False)
                                })
                except Exception as e:
                    self.log(f"⚠️ Ошибка парсинга сообщений: {e}", "warning")

            # Сохранение
            if collected_users:
                self.save_parsed_data(target, collected_users, stats)
                self.log(f"✅ Успех! Собрано {len(collected_users)} уникальных пользователей", "success")
                self.parse_status.configure(text=f"Готово: {len(collected_users)}", text_color="green")
            else:
                self.log("⚠️ Не удалось найти пользователей", "warning")
                self.parse_status.configure(text="Нет результатов", text_color="orange")

        except Exception as e:
            self.log(f"❌ Критическая ошибка: {e}", "error")
            self.parse_status.configure(text="Ошибка", text_color="red")
        finally:
            await client.disconnect()

    def save_parsed_data(self, target, users, stats):
        os.makedirs(self.parsed_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_format = self.export_format.get()

        # Сохраняем статистику
        stats_file = os.path.join(self.parsed_dir, f"{target}_stats_{timestamp}.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump({
                'target': target,
                'timestamp': timestamp,
                'stats': stats,
                'collected_count': len(users)
            }, f, indent=2, ensure_ascii=False)

        if export_format == "TXT":
            filename = os.path.join(self.parsed_dir, f"{target}_{timestamp}.txt")
            with open(filename, 'w', encoding='utf-8') as f:
                for user in users:
                    f.write(f"@{user['username']}\n")
                    
        elif export_format == "CSV":
            filename = os.path.join(self.parsed_dir, f"{target}_{timestamp}.csv")
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['username', 'id', 'first_name', 'last_name', 'is_bot', 'is_premium'])
                writer.writeheader()
                writer.writerows(users)
                
        elif export_format == "JSON":
            filename = os.path.join(self.parsed_dir, f"{target}_{timestamp}.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2, ensure_ascii=False)

        self.log(f"💾 Сохранено в {filename}")

    def clear_parsed(self):
        if messagebox.askyesno("Подтверждение", "Удалить все файлы парсинга?"):
            for f in os.listdir(self.parsed_dir):
                filepath = os.path.join(self.parsed_dir, f)
                try:
                    if os.path.isfile(filepath):
                        os.remove(filepath)
                except Exception as e:
                    self.log(f"⚠️ Ошибка удаления {f}: {e}", "warning")
            self.log("✅ Папка parsed_data очищена")

    # ==================== ПОИСК ЧАТОВ ====================
    def build_chat_search_frame(self, f):
        # Заголовок
        header_frame = ctk.CTkFrame(f, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text="📢 Поиск чатов", 
                     font=DesignConfig.FONT_TITLE,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(header_frame, text="Поиск каналов и групп по ключевым словам", 
                     font=DesignConfig.FONT_NORMAL,
                     text_color=DesignConfig.TEXT_SECONDARY).pack(side="left", padx=20, pady=25)

        # Карточка поиска
        search_card = ctk.CTkFrame(f, fg_color=DesignConfig.BG_CARD, 
                                   corner_radius=DesignConfig.CARD_CORNER)
        search_card.pack(fill="x", pady=10)
        
        search_inner = ctk.CTkFrame(search_card, fg_color="transparent")
        search_inner.pack(fill="both", expand=True, padx=25, pady=20)
        
        ctk.CTkLabel(search_inner, text="🔑 Ключевые слова:", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(anchor="w", pady=(0, 10))
        
        self.search_query = ctk.CTkEntry(search_inner, 
                                         placeholder_text="крипта, трейдинг, инвестиции",
                                         font=DesignConfig.FONT_NORMAL,
                                         height=45,
                                         corner_radius=8)
        self.search_query.pack(fill="x", pady=10)
        add_bindings(self.search_query)
        
        options_row = ctk.CTkFrame(search_inner, fg_color="transparent")
        options_row.pack(fill="x", pady=15)
        
        ctk.CTkLabel(options_row, text="📊 Лимит результатов:", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(side="left", padx=(0, 10))
        self.search_limit = ctk.CTkEntry(options_row, 
                                         placeholder_text="50",
                                         font=DesignConfig.FONT_NORMAL,
                                         width=100,
                                         height=40,
                                         corner_radius=8)
        self.search_limit.pack(side="left")
        self.search_limit.insert(0, "50")
        
        ctk.CTkButton(options_row, 
                      text="🔍 НАЧАТЬ ПОИСК",
                      font=DesignConfig.FONT_SUBHEADER,
                      height=45,
                      corner_radius=10,
                      fg_color=DesignConfig.PRIMARY_COLOR,
                      hover_color=DesignConfig.SECONDARY_COLOR,
                      command=lambda: self.run_async(self.do_chat_search)).pack(side="right")

        # Результаты
        results_card = ctk.CTkFrame(f, fg_color=DesignConfig.BG_CARD, 
                                    corner_radius=DesignConfig.CARD_CORNER)
        results_card.pack(fill="both", expand=True, pady=15)
        
        results_inner = ctk.CTkFrame(results_card, fg_color="transparent")
        results_inner.pack(fill="both", expand=True, padx=25, pady=20)
        
        ctk.CTkLabel(results_inner, text="📋 Результаты поиска:", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(anchor="w", pady=(0, 15))
        
        self.search_results = ctk.CTkTextbox(results_inner, 
                                             font=("Consolas", 11),
                                             corner_radius=8,
                                             border_width=1,
                                             border_color=DesignConfig.BG_DARK)
        self.search_results.pack(fill="both", expand=True, pady=10)
        add_bindings(self.search_results)
        
        btn_frame = ctk.CTkFrame(results_inner, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(btn_frame, 
                      text="💾 Сохранить",
                      font=DesignConfig.FONT_NORMAL,
                      height=40,
                      corner_radius=8,
                      fg_color=DesignConfig.SUCCESS_COLOR,
                      hover_color="#059669",
                      command=self.save_search_results).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, 
                      text="📋 Копировать",
                      font=DesignConfig.FONT_NORMAL,
                      height=40,
                      corner_radius=8,
                      fg_color=DesignConfig.BG_DARK,
                      hover_color=DesignConfig.PRIMARY_COLOR,
                      command=lambda: self.clipboard_append(self.search_results.get("1.0", "end"))).pack(side="left", padx=5)

    async def do_chat_search(self):
        query = self.search_query.get().strip()
        if not query:
            self.log("⚠️ Введите поисковый запрос", "warning")
            return

        try:
            limit = int(self.search_limit.get() or 50)
        except ValueError:
            limit = 50

        self.log(f"🔍 Поиск чатов по запросу: {query}")
        self.search_results.insert("1.0", f"Поиск по запросу: {query}\n{'='*50}\n\n")

        accs = [f.replace(".session", "") for f in os.listdir(self.sessions_dir) if f.endswith(".session")]
        if not accs:
            self.log("⚠️ Нет сессий!", "warning")
            return

        acc = accs[0] if self.current_session == "ВСЕ" else self.current_session
        session_path = os.path.join(self.sessions_dir, acc)
        proxy = self.get_proxy(acc)

        client = create_telethon_client(session_path, proxy=proxy)

        try:
            await client.connect()
            if not await client.is_user_authorized():
                self.log("❌ Аккаунт не авторизован", "error")
                return

            results = []
            
            # Поиск через глобальный поиск
            self.log("🔄 Поиск чатов...")
            
            # Используем метод search_global
            from telethon.tl.functions.contacts import SearchRequest
            
            try:
                search_result = await client(SearchRequest(
                    q=query,
                    limit=limit
                ))
                
                for peer in search_result.peers.chats:
                    results.append({
                        'type': 'channel/superchannel',
                        'id': peer.id,
                        'title': getattr(peer, 'title', 'Unknown'),
                        'username': getattr(peer, 'username', 'N/A'),
                        'participants': getattr(peer, 'participants_count', 'N/A')
                    })
                    
                for peer in search_result.peers.channels:
                    results.append({
                        'type': 'channel',
                        'id': peer.id,
                        'title': getattr(peer, 'title', 'Unknown'),
                        'username': getattr(peer, 'username', 'N/A'),
                        'participants': getattr(peer, 'participants_count', 'N/A')
                    })
                    
            except Exception as e:
                self.log(f"⚠️ Ошибка поиска: {e}", "warning")

            # Альтернативный поиск по известным паттернам
            self.log("🔄 Дополнительный поиск...")
            patterns = [
                f"{query} chat",
                f"{query} group",
                f"{query} crypto",
                f"crypto {query}",
                f"{query} trading"
            ]
            
            for pattern in patterns:
                if len(results) >= limit:
                    break
                try:
                    entity = await client.get_entity(pattern.replace(' ', ''))
                    if hasattr(entity, 'participants_count'):
                        results.append({
                            'type': 'channel',
                            'id': entity.id,
                            'title': getattr(entity, 'title', 'Unknown'),
                            'username': getattr(entity, 'username', 'N/A'),
                            'participants': getattr(entity, 'participants_count', 'N/A')
                        })
                except:
                    pass
                await asyncio.sleep(RATE_LIMIT_DELAY)

            # Вывод результатов
            self.search_results.delete("1.0", "end")
            self.search_results.insert("1.0", f"Найдено чатов: {len(results)}\n{'='*60}\n\n")
            
            for i, r in enumerate(results[:limit], 1):
                text = f"{i}. [{r['type']}] {r['title']}\n"
                text += f"   Username: @{r['username']}\n"
                text += f"   ID: {r['id']}\n"
                text += f"   Участников: {r['participants']}\n"
                text += f"   Ссылка: https://t.me/{r['username']}\n\n"
                self.search_results.insert("end", text)

            self.log(f"✅ Найдено {len(results)} чатов", "success")

        except Exception as e:
            self.log(f"❌ Ошибка поиска: {e}", "error")
        finally:
            await client.disconnect()

    def save_search_results(self):
        results = self.search_results.get("1.0", "end")
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(results)
            self.log(f"💾 Результаты сохранены в {filepath}")

    # ==================== ИНВАЙТЕР ====================
    def build_inviter_frame(self, f):
        # Заголовок
        header_frame = ctk.CTkFrame(f, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text="👥 Инвайтер", 
                     font=DesignConfig.FONT_TITLE,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(header_frame, text="Автоматическое добавление участников в чат", 
                     font=DesignConfig.FONT_NORMAL,
                     text_color=DesignConfig.TEXT_SECONDARY).pack(side="left", padx=20, pady=25)

        # Карточка настроек
        settings_card = ctk.CTkFrame(f, fg_color=DesignConfig.BG_CARD, 
                                     corner_radius=DesignConfig.CARD_CORNER)
        settings_card.pack(fill="x", pady=10)
        
        settings_inner = ctk.CTkFrame(settings_card, fg_color="transparent")
        settings_inner.pack(fill="both", expand=True, padx=25, pady=20)
        
        # База участников
        row1 = ctk.CTkFrame(settings_inner, fg_color="transparent")
        row1.pack(fill="x", pady=10)
        
        ctk.CTkLabel(row1, text="📂", font=("Segoe UI Emoji", 20)).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(row1, text="База участников:", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(side="left", padx=(0, 15))
        
        self.invite_db_info = ctk.CTkLabel(row1, text="Файл не выбран", 
                                           font=DesignConfig.FONT_NORMAL,
                                           text_color=DesignConfig.TEXT_SECONDARY)
        self.invite_db_info.pack(side="left", padx=10)
        
        ctk.CTkButton(row1, text="Выбрать", 
                      command=self.load_invite_db,
                      height=35,
                      corner_radius=6,
                      fg_color=DesignConfig.PRIMARY_COLOR,
                      hover_color=DesignConfig.SECONDARY_COLOR).pack(side="right")

        # Целевой чат
        row2 = ctk.CTkFrame(settings_inner, fg_color="transparent")
        row2.pack(fill="x", pady=10)
        
        ctk.CTkLabel(row2, text="📢 Целевой чат:", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(side="left", padx=(0, 15))
        self.invite_target = ctk.CTkEntry(row2, 
                                          placeholder_text="@your_channel",
                                          font=DesignConfig.FONT_NORMAL,
                                          height=40,
                                          corner_radius=8,
                                          width=300)
        self.invite_target.pack(side="left", padx=10)
        add_bindings(self.invite_target)

        # Лимит и задержки
        row3 = ctk.CTkFrame(settings_inner, fg_color="transparent")
        row3.pack(fill="x", pady=15)
        
        col1 = ctk.CTkFrame(row3, fg_color="transparent")
        col1.pack(side="left", fill="both", expand=True)
        
        ctk.CTkLabel(col1, text="👥 Лимит приглашений:", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(anchor="w")
        self.invite_limit = ctk.CTkEntry(col1, 
                                         placeholder_text="50",
                                         font=DesignConfig.FONT_NORMAL,
                                         width=120,
                                         height=40,
                                         corner_radius=8)
        self.invite_limit.pack(pady=5)
        self.invite_limit.insert(0, "50")
        
        col2 = ctk.CTkFrame(row3, fg_color="transparent")
        col2.pack(side="right")
        
        ctk.CTkLabel(col2, text="⏱ Задержка между приглашениями (сек):", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(anchor="w")
        
        delay_frame = ctk.CTkFrame(col2, fg_color="transparent")
        delay_frame.pack(pady=5)
        
        self.invite_delay_min = ctk.CTkEntry(delay_frame, 
                                             placeholder_text="30",
                                             font=DesignConfig.FONT_NORMAL,
                                             width=80,
                                             height=40,
                                             corner_radius=8)
        self.invite_delay_min.pack(side="left", padx=(0, 5))
        self.invite_delay_min.insert(0, "30")
        
        ctk.CTkLabel(delay_frame, text="-", 
                     font=DesignConfig.FONT_NORMAL,
                     text_color=DesignConfig.TEXT_SECONDARY).pack(side="left", padx=5)
        
        self.invite_delay_max = ctk.CTkEntry(delay_frame, 
                                             placeholder_text="60",
                                             font=DesignConfig.FONT_NORMAL,
                                             width=80,
                                             height=40,
                                             corner_radius=8)
        self.invite_delay_max.pack(side="left")
        self.invite_delay_max.insert(0, "60")

        # Кнопки управления
        controls_card = ctk.CTkFrame(f, fg_color="transparent")
        controls_card.pack(fill="x", pady=25)
        
        ctk.CTkButton(controls_card, 
                      text="🚀 ЗАПУСТИТЬ ИНВАЙТ",
                      font=DesignConfig.FONT_SUBHEADER,
                      height=50,
                      corner_radius=10,
                      fg_color=DesignConfig.SUCCESS_COLOR,
                      hover_color="#059669",
                      command=lambda: self.run_async(self.do_invite)).pack(side="left", padx=10)
        
        ctk.CTkButton(controls_card, 
                      text="⏹ СТОП",
                      font=DesignConfig.FONT_SUBHEADER,
                      height=50,
                      width=120,
                      corner_radius=10,
                      fg_color=DesignConfig.DANGER_COLOR,
                      hover_color="#dc2626",
                      command=lambda: setattr(self, 'is_invite_active', False)).pack(side="left", padx=10)

        # Статус
        self.invite_status = ctk.CTkLabel(f, text="", 
                                          font=DesignConfig.FONT_NORMAL,
                                          text_color=DesignConfig.WARNING_COLOR)
        self.invite_status.pack(pady=15)

    def load_invite_db(self):
        p = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if p:
            self.selected_invite_db = p
            self.invite_db_info.configure(text=os.path.basename(p), text_color="green")

    async def do_invite(self):
        if not hasattr(self, 'selected_invite_db') or not self.selected_invite_db:
            self.log("⚠️ Выберите базу участников", "warning")
            return

        target = self.invite_target.get().strip().replace('@', '')
        if not target:
            self.log("⚠️ Введите целевой чат", "warning")
            return

        try:
            limit = int(self.invite_limit.get() or 50)
            delay_min = int(self.invite_delay_min.get() or 30)
            delay_max = int(self.invite_delay_max.get() or 60)
        except ValueError:
            self.log("⚠️ Неверные числовые значения", "warning")
            return

        accs = [f.replace(".session", "") for f in os.listdir(self.sessions_dir) if f.endswith(".session")]
        if not accs:
            self.log("⚠️ Нет сессий!", "warning")
            return

        acc = accs[0] if self.current_session == "ВСЕ" else self.current_session
        session_path = os.path.join(self.sessions_dir, acc)
        proxy = self.get_proxy(acc)

        # Загрузка базы
        with open(self.selected_invite_db, 'r', encoding='utf-8') as f:
            usernames = [line.strip().replace('@', '') for line in f if line.strip()]

        if not usernames:
            self.log("⚠️ База пуста", "warning")
            return

        self.log(f"🚀 Запуск инвайта в @{target} (лимит: {limit})")
        self.is_invite_active = True
        self.invite_status.configure(text="Инвайт...", text_color="orange")

        client = create_telethon_client(session_path, proxy=proxy)
        stats = {'success': 0, 'failed': 0, 'limited': 0}

        try:
            await client.connect()
            if not await client.is_user_authorized():
                self.log("❌ Аккаунт не авторизован", "error")
                return

            # Получаем чат
            try:
                entity = await client.get_entity(target)
                self.log(f"✅ Чат найден: {entity.title}")
            except Exception as e:
                self.log(f"❌ Чат не найден: {e}", "error")
                return

            for i, username in enumerate(usernames[:limit]):
                if not self.is_invite_active:
                    self.log("⏹ Остановлено пользователем", "warning")
                    break

                try:
                    user = await client.get_entity(username)
                    
                    # Пробуем добавить через AddChatUserRequest (для групп)
                    try:
                        await client(AddChatUserRequest(
                            chat_id=entity.id,
                            user_id=user.id,
                            fwd_limit=0
                        ))
                        stats['success'] += 1
                        self.log(f"✅ Добавлен: @{username} ({stats['success']}/{i+1})")
                    except ChatAdminRequiredError:
                        self.log(f"⚠️ Нет прав админа для @{username}", "warning")
                        stats['failed'] += 1
                    except UserPrivacyRestrictedError:
                        self.log(f"🔒 Приватность: @{username}", "warning")
                        stats['failed'] += 1
                    except Exception as e:
                        stats['failed'] += 1
                        self.log(f"❌ Ошибка @{username}: {e}", "warning")

                except FloodWaitError as e:
                    wait_time = e.seconds
                    self.log(f"⏳ FloodWait: ждем {wait_time} сек", "warning")
                    stats['limited'] += 1
                    await asyncio.sleep(wait_time + 5)
                except Exception as e:
                    stats['failed'] += 1
                    self.log(f"❌ Ошибка: {e}", "error")

                # Задержка
                delay = random.uniform(delay_min, delay_max)
                await asyncio.sleep(delay)

            self.log(f"✅ Инвайт завершен! Успешно: {stats['success']}, Ошибок: {stats['failed']}, Лимитов: {stats['limited']}", "success")
            self.invite_status.configure(text=f"Готово: {stats['success']} успешных", text_color="green")

        except Exception as e:
            self.log(f"❌ Критическая ошибка: {e}", "error")
            self.invite_status.configure(text="Ошибка", text_color="red")
        finally:
            await client.disconnect()
            self.is_invite_active = False

    # ==================== ВХОД ПО ССЫЛКЕ-ПРИГЛАШЕНИЮ ====================
    def build_join_by_link_frame(self, f):
        header_frame = ctk.CTkFrame(f, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text="🔗 Вход по ссылке", 
                     font=DesignConfig.FONT_TITLE,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(header_frame, text="Вступление в чат по приватной ссылке", 
                     font=DesignConfig.FONT_NORMAL,
                     text_color=DesignConfig.TEXT_SECONDARY).pack(side="left", padx=20, pady=25)

        card = ctk.CTkFrame(f, fg_color=DesignConfig.BG_CARD, corner_radius=DesignConfig.CARD_CORNER)
        card.pack(fill="x", pady=15)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=30, pady=25)
        
        ctk.CTkLabel(inner, text="📎 Ссылка-приглашение:", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(anchor="w", pady=(0, 10))
        
        self.join_link_entry = ctk.CTkEntry(inner, 
                                            placeholder_text="https://t.me/+AbCdEfGhIjK",
                                            font=DesignConfig.FONT_NORMAL,
                                            height=50,
                                            corner_radius=8)
        self.join_link_entry.pack(fill="x", pady=10)
        add_bindings(self.join_link_entry)
        
        ctk.CTkButton(inner, 
                      text="🚀 ВОЙТИ В ЧАТ",
                      font=DesignConfig.FONT_SUBHEADER,
                      height=50,
                      corner_radius=10,
                      fg_color=DesignConfig.SUCCESS_COLOR,
                      hover_color="#059669",
                      command=lambda: self.run_async(self.do_join_by_link)).pack(pady=20)
        
        self.join_status = ctk.CTkLabel(inner, text="", 
                                        font=DesignConfig.FONT_NORMAL,
                                        text_color=DesignConfig.WARNING_COLOR)
        self.join_status.pack(pady=10)

    async def do_join_by_link(self):
        link = self.join_link_entry.get().strip()
        if not link:
            self.log("⚠️ Введите ссылку-приглашение", "warning")
            return

        accs = [f.replace(".session", "") for f in os.listdir(self.sessions_dir) if f.endswith(".session")]
        if not accs:
            self.log("⚠️ Нет сессий!", "warning")
            return

        acc = accs[0] if self.current_session == "ВСЕ" else self.current_session
        session_path = os.path.join(self.sessions_dir, acc)
        proxy = self.get_proxy(acc)

        self.log(f"🔗 Вход по ссылке: {link}")
        self.join_status.configure(text="Вход...", text_color="orange")

        client = create_telethon_client(session_path, proxy=proxy)

        try:
            await client.connect()
            if not await client.is_user_authorized():
                self.log("❌ Аккаунт не авторизован", "error")
                self.join_status.configure(text="Ошибка авторизации", text_color="red")
                return

            # Извлекаем хэш приглашения из ссылки
            # Форматы: https://t.me/+HASH, https://t.me/joinchat/HASH, t.me/+HASH, telegram.me/+HASH
            link = link.strip()
            hash_match = re.search(r'(?:t\.me/|telegram\.me/|\+|joinchat/)(\+?[A-Za-z0-9_-]+)', link)
            if not hash_match:
                self.log("⚠️ Неверный формат ссылки", "warning")
                self.join_status.configure(text="Неверный формат", text_color="red")
                return

            invite_hash = hash_match.group(1)
            if invite_hash.startswith('+'):
                invite_hash = invite_hash[1:]

            self.log(f"🔍 Хэш приглашения: {invite_hash}")

            # Получаем информацию о приглашении
            from telethon.tl.functions.messages import CheckChatInviteRequest
            try:
                invite_info = await client(CheckChatInviteRequest(invite_hash))
                chat_title = invite_info.chat.title if hasattr(invite_info, 'chat') else "Неизвестно"
                self.log(f"📊 Чат: {chat_title}")
            except InviteHashExpiredError:
                self.log("⚠️ Ссылка устарела или истекла", "warning")
                self.join_status.configure(text="❌ Ссылка устарела", text_color="red")
                await client.disconnect()
                return
            except InviteHashInvalidError:
                self.log("⚠️ Неверная ссылка-приглашение", "warning")
                self.join_status.configure(text="❌ Неверная ссылка", text_color="red")
                await client.disconnect()
                return
            except Exception as e:
                self.log(f"⚠️ Ошибка получения информации: {e}", "warning")

            # Входим в чат
            from telethon.tl.functions.messages import ImportChatInviteRequest
            try:
                result = await client(ImportChatInviteRequest(invite_hash))
                
                # Получаем информацию о чате после входа
                if hasattr(result, 'chats') and result.chats:
                    chat = result.chats[0]
                    self.log(f"✅ Успешный вход в чат: {getattr(chat, 'title', 'Неизвестно')}", "success")
                    self.join_status.configure(text=f"✅ Вход выполнен: {getattr(chat, 'title', 'Чат')}", text_color="green")
                else:
                    self.log("✅ Успешный вход в чат", "success")
                    self.join_status.configure(text="✅ Вход выполнен", text_color="green")
                    
            except InviteHashExpiredError:
                self.log("⚠️ Ссылка устарела или истекла", "warning")
                self.join_status.configure(text="❌ Ссылка устарела", text_color="red")
            except InviteHashInvalidError:
                self.log("⚠️ Неверная ссылка-приглашение", "warning")
                self.join_status.configure(text="❌ Неверная ссылка", text_color="red")
            except UserAlreadyParticipantError:
                self.log("ℹ️ Вы уже в этом чате", "info")
                self.join_status.configure(text="ℹ️ Уже в чате", text_color="orange")
            except FloodWaitError as e:
                self.log(f"⏳ FloodWait: ждем {e.seconds} сек", "warning")
                self.join_status.configure(text=f"FloodWait: {e.seconds} сек", text_color="orange")
            except Exception as e:
                self.log(f"❌ Ошибка входа: {e}", "error")
                self.join_status.configure(text=f"Ошибка: {str(e)[:50]}", text_color="red")

        except FloodWaitError as e:
            self.log(f"⏳ FloodWait: ждем {e.seconds} сек", "warning")
            self.join_status.configure(text=f"FloodWait: {e.seconds} сек", text_color="orange")
        except Exception as e:
            self.log(f"❌ Ошибка: {e}", "error")
            self.join_status.configure(text=f"Ошибка: {str(e)[:50]}", text_color="red")
        finally:
            await client.disconnect()

    # ==================== РАССЫЛКА ====================
    def build_spam_frame(self, f):
        header_frame = ctk.CTkFrame(f, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text="📨 Рассылка", 
                     font=DesignConfig.FONT_TITLE,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(header_frame, text="Массовая отправка сообщений участникам", 
                     font=DesignConfig.FONT_NORMAL,
                     text_color=DesignConfig.TEXT_SECONDARY).pack(side="left", padx=20, pady=25)

        card = ctk.CTkFrame(f, fg_color=DesignConfig.BG_CARD, corner_radius=DesignConfig.CARD_CORNER)
        card.pack(fill="x", pady=10)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25, pady=20)
        
        # База
        row1 = ctk.CTkFrame(inner, fg_color="transparent")
        row1.pack(fill="x", pady=10)
        
        ctk.CTkLabel(row1, text="📂", font=("Segoe UI Emoji", 20)).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(row1, text="База получателей:", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(side="left", padx=(0, 15))
        
        self.db_info = ctk.CTkLabel(row1, text="Файл не выбран", 
                                    font=DesignConfig.FONT_NORMAL,
                                    text_color=DesignConfig.TEXT_SECONDARY)
        self.db_info.pack(side="left", padx=10)
        
        ctk.CTkButton(row1, text="Выбрать", 
                      command=self.load_txt,
                      height=35,
                      corner_radius=6,
                      fg_color=DesignConfig.PRIMARY_COLOR,
                      hover_color=DesignConfig.SECONDARY_COLOR).pack(side="right")

        # Сообщение
        ctk.CTkLabel(inner, text="✉️ Текст сообщения:", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(anchor="w", pady=(15, 10))
        
        self.s_msg = ctk.CTkTextbox(inner, 
                                    font=DesignConfig.FONT_NORMAL,
                                    height=150,
                                    corner_radius=8,
                                    border_width=1,
                                    border_color=DesignConfig.BG_DARK)
        self.s_msg.pack(fill="x", pady=10)
        add_bindings(self.s_msg)

        # Задержки
        row2 = ctk.CTkFrame(inner, fg_color="transparent")
        row2.pack(fill="x", pady=15)
        
        ctk.CTkLabel(row2, text="⏱ Задержка между сообщениями (сек):", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(side="left", padx=(0, 15))
        
        delay_frame = ctk.CTkFrame(row2, fg_color="transparent")
        delay_frame.pack(side="left")
        
        self.spam_delay_min = ctk.CTkEntry(delay_frame, 
                                           placeholder_text="60",
                                           font=DesignConfig.FONT_NORMAL,
                                           width=80,
                                           height=40,
                                           corner_radius=8)
        self.spam_delay_min.pack(side="left", padx=(0, 5))
        self.spam_delay_min.insert(0, "60")
        
        ctk.CTkLabel(delay_frame, text="-", 
                     font=DesignConfig.FONT_NORMAL,
                     text_color=DesignConfig.TEXT_SECONDARY).pack(side="left", padx=5)
        
        self.spam_delay_max = ctk.CTkEntry(delay_frame, 
                                           placeholder_text="120",
                                           font=DesignConfig.FONT_NORMAL,
                                           width=80,
                                           height=40,
                                           corner_radius=8)
        self.spam_delay_max.pack(side="left")
        self.spam_delay_max.insert(0, "120")

        # Кнопки
        controls = ctk.CTkFrame(inner, fg_color="transparent")
        controls.pack(fill="x", pady=20)
        
        ctk.CTkButton(controls, 
                      text="▶ ПУСК",
                      font=DesignConfig.FONT_SUBHEADER,
                      height=45,
                      corner_radius=10,
                      fg_color=DesignConfig.SUCCESS_COLOR,
                      hover_color="#059669",
                      command=lambda: self.run_async(self.do_spam)).pack(side="left", padx=5)
        
        ctk.CTkButton(controls, 
                      text="⏹ СТОП",
                      font=DesignConfig.FONT_SUBHEADER,
                      height=45,
                      width=100,
                      corner_radius=10,
                      fg_color=DesignConfig.DANGER_COLOR,
                      hover_color="#dc2626",
                      command=lambda: setattr(self, 'is_spam_active', False)).pack(side="left", padx=5)

    async def do_spam(self):
        if not self.selected_db_path:
            self.log("⚠️ Выберите базу для рассылки!", "warning")
            return

        message = self.s_msg.get("1.0", "end").strip()
        if not message:
            self.log("⚠️ Введите текст сообщения", "warning")
            return

        try:
            delay_min = int(self.spam_delay_min.get() or 60)
            delay_max = int(self.spam_delay_max.get() or 120)
        except ValueError:
            self.log("⚠️ Неверные значения задержки", "warning")
            return

        self.is_spam_active = True
        self.log(f"🚀 Рассылка запущена (задержка: {delay_min}-{delay_max} сек)")

        with open(self.selected_db_path, 'r', encoding='utf-8') as f:
            usernames = [line.strip().replace('@', '') for line in f if line.strip()]

        if not usernames:
            self.log("⚠️ База пуста", "warning")
            return

        accs = [f.replace(".session", "") for f in os.listdir(self.sessions_dir) if f.endswith(".session")]
        if not accs:
            self.log("⚠️ Нет сессий!", "warning")
            return

        acc = accs[0] if self.current_session == "ВСЕ" else self.current_session
        session_path = os.path.join(self.sessions_dir, acc)
        proxy = self.get_proxy(acc)

        client = create_telethon_client(session_path, proxy=proxy)
        stats = {'success': 0, 'failed': 0}

        try:
            await client.connect()
            if not await client.is_user_authorized():
                self.log("❌ Аккаунт не авторизован", "error")
                return

            for i, username in enumerate(usernames):
                if not self.is_spam_active:
                    self.log("⏹ Остановлено пользователем", "warning")
                    break

                try:
                    user = await client.get_entity(username)
                    await client.send_message(user, message)
                    stats['success'] += 1
                    self.log(f"✅ Отправлено @{username} ({stats['success']}/{i+1})")
                except FloodWaitError as e:
                    wait_time = e.seconds
                    self.log(f"⏳ FloodWait: ждем {wait_time} сек", "warning")
                    stats['failed'] += 1
                    await asyncio.sleep(wait_time + 5)
                except Exception as e:
                    stats['failed'] += 1
                    self.log(f"❌ Ошибка @{username}: {e}", "warning")

                delay = random.uniform(delay_min, delay_max)
                await asyncio.sleep(delay)

            self.log(f"✅ Рассылка завершена! Успешно: {stats['success']}, Ошибок: {stats['failed']}", "success")

        except Exception as e:
            self.log(f"❌ Критическая ошибка: {e}", "error")
        finally:
            await client.disconnect()
            self.is_spam_active = False

    # ==================== ПРОГРЕВ ====================
    def build_warm_frame(self, f):
        header_frame = ctk.CTkFrame(f, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text="🔥 Прогрев", 
                     font=DesignConfig.FONT_TITLE,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(header_frame, text="Автоматическая активность для имитации живого пользователя", 
                     font=DesignConfig.FONT_NORMAL,
                     text_color=DesignConfig.TEXT_SECONDARY).pack(side="left", padx=20, pady=25)

        card = ctk.CTkFrame(f, fg_color=DesignConfig.BG_CARD, corner_radius=DesignConfig.CARD_CORNER)
        card.pack(fill="both", expand=True, pady=10)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25, pady=20)
        
        ctk.CTkLabel(inner, text="📢 Каналы для активности (username или ссылка, каждый с новой строки):", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(anchor="w", pady=(0, 10))
        
        self.w_text = ctk.CTkTextbox(inner, 
                                     font=DesignConfig.FONT_NORMAL,
                                     height=200,
                                     corner_radius=8,
                                     border_width=1,
                                     border_color=DesignConfig.BG_DARK)
        self.w_text.pack(fill="both", expand=True, pady=10)
        add_bindings(self.w_text)

        # Действия
        actions_row = ctk.CTkFrame(inner, fg_color="transparent")
        actions_row.pack(fill="x", pady=15)
        
        ctk.CTkLabel(actions_row, text="✅ Действия:", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(side="left", padx=(0, 20))
        
        self.warm_subscribe = ctk.CTkCheckBox(actions_row, 
                                              text="Подписка на каналы",
                                              font=DesignConfig.FONT_NORMAL,
                                              checkbox_width=20,
                                              checkbox_height=20)
        self.warm_subscribe.pack(side="left", padx=10)
        self.warm_subscribe.select()
        
        self.warm_like = ctk.CTkCheckBox(actions_row, 
                                         text="Лайки постов",
                                         font=DesignConfig.FONT_NORMAL,
                                         checkbox_width=20,
                                         checkbox_height=20)
        self.warm_like.pack(side="left", padx=10)
        self.warm_like.select()
        
        self.warm_comment = ctk.CTkCheckBox(actions_row, 
                                            text="Комментарии",
                                            font=DesignConfig.FONT_NORMAL,
                                            checkbox_width=20,
                                            checkbox_height=20)
        self.warm_comment.pack(side="left", padx=10)

        ctk.CTkButton(inner, 
                      text="🔥 Запустить прогрев",
                      font=DesignConfig.FONT_SUBHEADER,
                      height=50,
                      corner_radius=10,
                      fg_color="#b87333",
                      hover_color="#9a602b",
                      command=lambda: self.run_async(self.do_warm)).pack(pady=20)

    async def do_warm(self):
        channels_text = self.w_text.get("0.0", "end").strip()
        channels = [ch.strip().replace('@', '').replace('https://t.me/', '') for ch in channels_text.splitlines() if ch.strip()]
        
        if not channels:
            self.log("⚠️ Введите каналы для прогрева", "warning")
            return

        accs = [f.replace(".session", "") for f in os.listdir(self.sessions_dir) if f.endswith(".session")]
        if not accs:
            self.log("⚠️ Нет сессий!", "warning")
            return

        acc = accs[0] if self.current_session == "ВСЕ" else self.current_session
        session_path = os.path.join(self.sessions_dir, acc)
        proxy = self.get_proxy(acc)

        self.log(f"🔥 Запуск прогрева для {len(channels)} каналов")

        client = create_telethon_client(session_path, proxy=proxy)

        try:
            await client.connect()
            if not await client.is_user_authorized():
                self.log("❌ Аккаунт не авторизован", "error")
                return

            stats = {'subscribed': 0, 'liked': 0, 'commented': 0}

            for channel in channels:
                try:
                    entity = await client.get_entity(channel)
                    self.log(f"📊 Канал: {entity.title}")

                    # Подписка
                    if self.warm_subscribe.get():
                        try:
                            await client.join_chat(channel)
                            stats['subscribed'] += 1
                            self.log(f"✅ Подписан на @{channel}")
                        except Exception as e:
                            self.log(f"⚠️ Ошибка подписки: {e}", "warning")

                    # Лайки последних постов
                    if self.warm_like.get():
                        try:
                            async for msg in client.iter_messages(entity, limit=3):
                                await msg.react('👍')
                                stats['liked'] += 1
                                self.log(f"❤️ Лайк посту #{msg.id}")
                                await asyncio.sleep(2)
                        except Exception as e:
                            self.log(f"⚠️ Ошибка лайков: {e}", "warning")

                    await asyncio.sleep(random.uniform(5, 15))

                except Exception as e:
                    self.log(f"❌ Ошибка с каналом {channel}: {e}", "error")

            self.log(f"✅ Прогрев завершен! Подписок: {stats['subscribed']}, Лайков: {stats['liked']}", "success")

        except Exception as e:
            self.log(f"❌ Критическая ошибка: {e}", "error")
        finally:
            await client.disconnect()

    # ==================== АВТООТВЕТЧИК ====================
    def build_autoresponder_frame(self, f):
        header_frame = ctk.CTkFrame(f, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text="🤖 Автоответчик", 
                     font=DesignConfig.FONT_TITLE,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(header_frame, text="Автоматические ответы на сообщения", 
                     font=DesignConfig.FONT_NORMAL,
                     text_color=DesignConfig.TEXT_SECONDARY).pack(side="left", padx=20, pady=25)

        card = ctk.CTkFrame(f, fg_color=DesignConfig.BG_CARD, corner_radius=DesignConfig.CARD_CORNER)
        card.pack(fill="both", expand=True, pady=10)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25, pady=20)
        
        ctk.CTkLabel(inner, text="💬 Текст автоматического ответа:", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(anchor="w", pady=(0, 10))
        
        self.ar_msg = ctk.CTkTextbox(inner, 
                                     font=DesignConfig.FONT_NORMAL,
                                     height=150,
                                     corner_radius=8,
                                     border_width=1,
                                     border_color=DesignConfig.BG_DARK)
        self.ar_msg.pack(fill="both", expand=True, pady=10)
        add_bindings(self.ar_msg)

        ctk.CTkLabel(inner, text="🔑 Ключевые слова (через запятую) или оставьте пустым для ответа всем:", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(anchor="w", pady=(15, 10))
        
        self.ar_keywords = ctk.CTkEntry(inner, 
                                        placeholder_text="привет, здравствуйте, вопрос",
                                        font=DesignConfig.FONT_NORMAL,
                                        height=45,
                                        corner_radius=8)
        self.ar_keywords.pack(fill="x", pady=10)
        add_bindings(self.ar_keywords)

        ctk.CTkLabel(inner, text="📋 Чаты для мониторинга (username, каждый с новой строки):", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(anchor="w", pady=(15, 10))
        
        self.ar_chats = ctk.CTkTextbox(inner, 
                                       font=DesignConfig.FONT_NORMAL,
                                       height=100,
                                       corner_radius=8,
                                       border_width=1,
                                       border_color=DesignConfig.BG_DARK)
        self.ar_chats.pack(fill="both", expand=True, pady=10)
        add_bindings(self.ar_chats)

        self.ar_btn = ctk.CTkButton(inner, 
                                    text="ВКЛЮЧИТЬ",
                                    font=DesignConfig.FONT_SUBHEADER,
                                    height=50,
                                    corner_radius=10,
                                    fg_color=DesignConfig.SUCCESS_COLOR,
                                    hover_color="#059669",
                                    command=self.toggle_ar)
        self.ar_btn.pack(pady=25)

    def toggle_ar(self):
        self.is_ar_active = not self.is_ar_active
        if self.is_ar_active:
            self.ar_btn.configure(text="ВЫКЛЮЧИТЬ", fg_color="red")
            self.log("🤖 Автоответчик включен")
            self.run_async(self.run_autoresponder)
        else:
            self.ar_btn.configure(text="ВКЛЮЧИТЬ", fg_color="green")
            self.log("🛑 Автоответчик выключлен")

    async def run_autoresponder(self):
        message_text = self.ar_msg.get("1.0", "end").strip()
        keywords_text = self.ar_keywords.get().strip()
        keywords = [k.strip().lower() for k in keywords_text.split(',')] if keywords_text else []
        chats_text = self.ar_chats.get("0.0", "end").strip()
        chat_list = [ch.strip().replace('@', '') for ch in chats_text.splitlines() if ch.strip()]

        accs = [f.replace(".session", "") for f in os.listdir(self.sessions_dir) if f.endswith(".session")]
        if not accs:
            self.log("⚠️ Нет сессий для автоответчика", "warning")
            return

        acc = accs[0] if self.current_session == "ВСЕ" else self.current_session
        session_path = os.path.join(self.sessions_dir, acc)
        proxy = self.get_proxy(acc)

        client = create_telethon_client(session_path, proxy=proxy)

        try:
            await client.connect()
            
            if not await client.is_user_authorized():
                self.log("❌ Аккаунт не авторизован", "error")
                await client.disconnect()
                return

            self.log("✅ Автоответчик подключен", "success")

            @client.on(events.NewMessage(chats=chat_list if chat_list else None))
            async def handler(event):
                try:
                    if not self.is_ar_active:
                        return

                    if event.sender_id == (await client.get_me()).id:
                        return

                    text = event.message.text.lower()

                    # Проверка ключевых слов
                    if keywords and not any(kw in text for kw in keywords):
                        return

                    await event.respond(message_text)
                    self.log(f"💬 Автоответ пользователю {event.sender_id}")
                except Exception as e:
                    self.log(f"⚠️ Ошибка в автоответчике: {e}", "warning")

            self.log("🤖 Автоответчик активен. Ожидание сообщений...")
            while self.is_ar_active:
                await asyncio.sleep(1)

        except Exception as e:
            self.log(f"❌ Ошибка автоответчика: {e}", "error")
        finally:
            try:
                await client.disconnect()
            except:
                pass

    # ==================== КОНТАКТЫ ====================
    def build_contacts_frame(self, f):
        header_frame = ctk.CTkFrame(f, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text="📞 Сбор контактов", 
                     font=DesignConfig.FONT_TITLE,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(header_frame, text="Извлечение телефонных номеров из профилей", 
                     font=DesignConfig.FONT_NORMAL,
                     text_color=DesignConfig.TEXT_SECONDARY).pack(side="left", padx=20, pady=25)

        card = ctk.CTkFrame(f, fg_color=DesignConfig.BG_CARD, corner_radius=DesignConfig.CARD_CORNER)
        card.pack(fill="x", pady=10)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25, pady=20)
        
        ctk.CTkLabel(inner, text="📋 Чат для сбора контактов (username):", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(anchor="w", pady=(0, 10))
        
        self.contacts_chat = ctk.CTkEntry(inner, 
                                          placeholder_text="@durov",
                                          font=DesignConfig.FONT_NORMAL,
                                          height=45,
                                          corner_radius=8)
        self.contacts_chat.pack(fill="x", pady=15)
        add_bindings(self.contacts_chat)

        ctk.CTkButton(inner, 
                      text="🔍 Собрать контакты",
                      font=DesignConfig.FONT_SUBHEADER,
                      height=50,
                      corner_radius=10,
                      fg_color=DesignConfig.PRIMARY_COLOR,
                      hover_color=DesignConfig.SECONDARY_COLOR,
                      command=lambda: self.run_async(self.do_collect_contacts)).pack(pady=20)

        ctk.CTkLabel(inner, text="📋 Результаты:", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(anchor="w", pady=(15, 10))
        
        self.contacts_results = ctk.CTkTextbox(inner, 
                                               font=("Consolas", 11),
                                               height=300,
                                               corner_radius=8,
                                               border_width=1,
                                               border_color=DesignConfig.BG_DARK)
        self.contacts_results.pack(fill="both", expand=True, pady=10)
        add_bindings(self.contacts_results)

        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(btn_frame, 
                      text="💾 Сохранить",
                      font=DesignConfig.FONT_NORMAL,
                      height=40,
                      corner_radius=8,
                      fg_color=DesignConfig.SUCCESS_COLOR,
                      hover_color="#059669",
                      command=self.save_contacts).pack(side="left", padx=5)

    async def do_collect_contacts(self):
        chat = self.contacts_chat.get().strip().replace('@', '')
        if not chat:
            self.log("⚠️ Введите чат", "warning")
            return

        accs = [f.replace(".session", "") for f in os.listdir(self.sessions_dir) if f.endswith(".session")]
        if not accs:
            self.log("⚠️ Нет сессий!", "warning")
            return

        acc = accs[0] if self.current_session == "ВСЕ" else self.current_session
        session_path = os.path.join(self.sessions_dir, acc)
        proxy = self.get_proxy(acc)

        self.log(f"📞 Сбор контактов из @{chat}")
        self.contacts_results.delete("1.0", "end")

        client = create_telethon_client(session_path, proxy=proxy)
        contacts = []

        try:
            await client.connect()
            if not await client.is_user_authorized():
                self.log("❌ Аккаунт не авторизован", "error")
                return

            entity = await client.get_entity(chat)
            
            async for user in client.iter_participants(entity):
                phone = getattr(user, 'phone', None)
                if phone:
                    contacts.append({
                        'username': user.username,
                        'phone': phone,
                        'name': f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
                    })
                    self.contacts_results.insert("end", f"{phone} - @{user.username} ({user.first_name})\n")

            self.log(f"✅ Найдено контактов: {len(contacts)}", "success")

        except Exception as e:
            self.log(f"❌ Ошибка: {e}", "error")
        finally:
            await client.disconnect()

        self.collected_contacts = contacts

    def save_contacts(self):
        if not hasattr(self, 'collected_contacts') or not self.collected_contacts:
            self.log("⚠️ Нет контактов для сохранения", "warning")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt")]
        )
        if filepath:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['phone', 'username', 'name'])
                writer.writeheader()
                writer.writerows(self.collected_contacts)
            self.log(f"💾 Контакты сохранены в {filepath}")

    # ==================== СТАТИСТИКА ====================
    def build_stats_frame(self, f):
        header_frame = ctk.CTkFrame(f, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text="📊 Статистика", 
                     font=DesignConfig.FONT_TITLE,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(header_frame, text="Информация обо всех аккаунтах", 
                     font=DesignConfig.FONT_NORMAL,
                     text_color=DesignConfig.TEXT_SECONDARY).pack(side="left", padx=20, pady=25)

        card = ctk.CTkFrame(f, fg_color=DesignConfig.BG_CARD, corner_radius=DesignConfig.CARD_CORNER)
        card.pack(fill="both", expand=True, pady=10)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25, pady=20)
        
        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 20))
        
        ctk.CTkButton(btn_row, 
                      text="🔄 Обновить статистику",
                      font=DesignConfig.FONT_SUBHEADER,
                      height=45,
                      corner_radius=10,
                      fg_color=DesignConfig.PRIMARY_COLOR,
                      hover_color=DesignConfig.SECONDARY_COLOR,
                      command=lambda: self.run_async(self.show_stats)).pack(side="left", padx=5)
        
        ctk.CTkButton(btn_row, 
                      text="💾 Экспорт отчета",
                      font=DesignConfig.FONT_SUBHEADER,
                      height=45,
                      corner_radius=10,
                      fg_color=DesignConfig.SUCCESS_COLOR,
                      hover_color="#059669",
                      command=self.export_stats).pack(side="left", padx=5)

        self.stats_text = ctk.CTkTextbox(inner, 
                                         font=("Consolas", 11),
                                         corner_radius=8,
                                         border_width=1,
                                         border_color=DesignConfig.BG_DARK)
        self.stats_text.pack(fill="both", expand=True)
        add_bindings(self.stats_text)

    async def show_stats(self):
        accs = [f.replace(".session", "") for f in os.listdir(self.sessions_dir) if f.endswith(".session")]
        if not accs:
            self.log("⚠️ Нет сессий!", "warning")
            return

        self.stats_text.delete("1.0", "end")
        self.stats_text.insert("1.0", "📊 СТАТИСТИКА АККАУНТОВ\n" + "="*60 + "\n\n")

        total_stats = {
            'total': len(accs),
            'active': 0,
            'premium': 0,
            'chats': 0
        }

        for acc in accs:
            session_path = os.path.join(self.sessions_dir, acc)
            proxy = self.get_proxy(acc)

            client = create_telethon_client(session_path, proxy=proxy)
            
            try:
                await client.connect()
                
                if await client.is_user_authorized():
                    me = await client.get_me()
                    total_stats['active'] += 1
                    if getattr(me, 'premium', False):
                        total_stats['premium'] += 1
                    
                    # Количество диалогов
                    dialogs_count = 0
                    async for _ in client.iter_dialogs():
                        dialogs_count += 1
                    total_stats['chats'] += dialogs_count
                    
                    self.stats_text.insert("end", f"✅ {acc}\n")
                    self.stats_text.insert("end", f"   Имя: {me.first_name} @{me.username}\n")
                    self.stats_text.insert("end", f"   ID: {me.id}, Premium: {getattr(me, 'premium', False)}\n")
                    self.stats_text.insert("end", f"   Диалогов: {dialogs_count}\n\n")
                else:
                    self.stats_text.insert("end", f"❌ {acc} - Не авторизован\n\n")
                    
            except Exception as e:
                self.stats_text.insert("end", f"⚠️ {acc} - Ошибка: {e}\n\n")
            finally:
                await client.disconnect()

        self.stats_text.insert("end", "\n" + "="*60 + "\n")
        self.stats_text.insert("end", f"ВСЕГО: {total_stats['total']}\n")
        self.stats_text.insert("end", f"АКТИВНЫХ: {total_stats['active']}\n")
        self.stats_text.insert("end", f"PREMIUM: {total_stats['premium']}\n")
        self.stats_text.insert("end", f"ВСЕГО ДИАЛОГОВ: {total_stats['chats']}\n")

        self.account_stats = total_stats

    def export_stats(self):
        if not hasattr(self, 'account_stats'):
            self.log("⚠️ Сначала получите статистику", "warning")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt")]
        )
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.account_stats, f, indent=2, ensure_ascii=False)
            self.log(f"💾 Статистика сохранена в {filepath}")

    # ==================== ПРОКСИ ====================
    def build_proxy_frame(self, f):
        header_frame = ctk.CTkFrame(f, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text="🌐 Прокси", 
                     font=DesignConfig.FONT_TITLE,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(header_frame, text="Настройки для обхода блокировок", 
                     font=DesignConfig.FONT_NORMAL,
                     text_color=DesignConfig.TEXT_SECONDARY).pack(side="left", padx=20, pady=25)

        # Инструкция
        info_card = ctk.CTkFrame(f, fg_color=DesignConfig.BG_CARD, corner_radius=DesignConfig.CARD_CORNER)
        info_card.pack(fill="x", pady=10)
        
        info_inner = ctk.CTkFrame(info_card, fg_color="transparent")
        info_inner.pack(fill="both", expand=True, padx=25, pady=20)
        
        ctk.CTkLabel(info_inner, text="📖 Форматы прокси:", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(anchor="w", pady=(0, 10))
        
        info_text = ctk.CTkTextbox(info_inner, 
                                   font=("Consolas", 10),
                                   height=100,
                                   corner_radius=8,
                                   border_width=1,
                                   border_color=DesignConfig.BG_DARK)
        info_text.pack(fill="x")
        info_text.insert("1.0", """Формат 1: ip:port:user:pass
   Пример: 192.168.1.1:1080:myuser:mypass

Формат 2: user:pass@ip:port (как у вас!)
   Пример: myuser:mypass@192.168.1.1:1080

💡 Введите прокси в любом формате в поле ниже и нажмите "Авто-парсинг"
""")
        info_text.configure(state="disabled")

        # Быстрый ввод прокси
        quick_card = ctk.CTkFrame(f, fg_color=DesignConfig.BG_CARD, corner_radius=DesignConfig.CARD_CORNER)
        quick_card.pack(fill="x", pady=15)
        
        quick_inner = ctk.CTkFrame(quick_card, fg_color="transparent")
        quick_inner.pack(fill="both", expand=True, padx=25, pady=20)
        
        ctk.CTkLabel(quick_inner, text="⚡ Быстрый ввод (любой формат):", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(anchor="w", pady=(0, 10))
        
        self.pr_quick_entry = ctk.CTkEntry(quick_inner, 
                                           placeholder_text="user:pass@ip:port или ip:port:user:pass",
                                           font=("Consolas", 11),
                                           height=45,
                                           corner_radius=8)
        self.pr_quick_entry.pack(fill="x", pady=10)
        
        ctk.CTkButton(quick_inner, 
                      text="🔄 Авто-парсинг и привязка",
                      font=DesignConfig.FONT_SUBHEADER,
                      height=40,
                      corner_radius=8,
                      fg_color=DesignConfig.PRIMARY_COLOR,
                      hover_color=DesignConfig.SECONDARY_COLOR,
                      command=self.quick_parse_and_save).pack(pady=10)
        
        self.quick_status = ctk.CTkLabel(quick_inner, text="", 
                                         font=DesignConfig.FONT_NORMAL,
                                         text_color=DesignConfig.TEXT_SECONDARY)
        self.quick_status.pack(pady=5)

        # Ручной ввод
        settings_card = ctk.CTkFrame(f, fg_color=DesignConfig.BG_CARD, corner_radius=DesignConfig.CARD_CORNER)
        settings_card.pack(fill="x", pady=15)
        
        settings_inner = ctk.CTkFrame(settings_card, fg_color="transparent")
        settings_inner.pack(fill="both", expand=True, padx=25, pady=20)
        
        ctk.CTkLabel(settings_inner, text="⚙️ Ручной ввод (ip:port:user:pass):", 
                     font=DesignConfig.FONT_SUBHEADER,
                     text_color=DesignConfig.TEXT_PRIMARY).pack(anchor="w", pady=(0, 15))
        
        # Поля ввода в одну строку
        proxy_row = ctk.CTkFrame(settings_inner, fg_color="transparent")
        proxy_row.pack(fill="x", pady=10)
        
        ctk.CTkLabel(proxy_row, text="IP:", 
                     font=DesignConfig.FONT_NORMAL,
                     text_color=DesignConfig.TEXT_SECONDARY).pack(side="left", padx=(0, 5))
        self.pr_ip = ctk.CTkEntry(proxy_row, 
                                  placeholder_text="192.168.0.1",
                                  font=DesignConfig.FONT_NORMAL,
                                  width=140,
                                  height=40,
                                  corner_radius=6)
        self.pr_ip.pack(side="left", padx=5)
        
        ctk.CTkLabel(proxy_row, text="Port:", 
                     font=DesignConfig.FONT_NORMAL,
                     text_color=DesignConfig.TEXT_SECONDARY).pack(side="left", padx=(10, 5))
        self.pr_port = ctk.CTkEntry(proxy_row, 
                                    placeholder_text="1080",
                                    font=DesignConfig.FONT_NORMAL,
                                    width=100,
                                    height=40,
                                    corner_radius=6)
        self.pr_port.pack(side="left", padx=5)
        
        ctk.CTkLabel(proxy_row, text="User:", 
                     font=DesignConfig.FONT_NORMAL,
                     text_color=DesignConfig.TEXT_SECONDARY).pack(side="left", padx=(10, 5))
        self.pr_user = ctk.CTkEntry(proxy_row, 
                                    placeholder_text="username",
                                    font=DesignConfig.FONT_NORMAL,
                                    width=120,
                                    height=40,
                                    corner_radius=6)
        self.pr_user.pack(side="left", padx=5)
        
        ctk.CTkLabel(proxy_row, text="Pass:", 
                     font=DesignConfig.FONT_NORMAL,
                     text_color=DesignConfig.TEXT_SECONDARY).pack(side="left", padx=(10, 5))
        self.pr_pass = ctk.CTkEntry(proxy_row, 
                                    placeholder_text="password",
                                    font=DesignConfig.FONT_NORMAL,
                                    width=120,
                                    height=40,
                                    corner_radius=6)
        self.pr_pass.pack(side="left", padx=5)

        # Кнопки
        btn_row = ctk.CTkFrame(settings_inner, fg_color="transparent")
        btn_row.pack(fill="x", pady=20)
        
        ctk.CTkButton(btn_row, 
                      text="💾 Привязать",
                      font=DesignConfig.FONT_SUBHEADER,
                      height=45,
                      corner_radius=10,
                      fg_color=DesignConfig.PRIMARY_COLOR,
                      hover_color=DesignConfig.SECONDARY_COLOR,
                      command=self.save_proxy).pack(side="left", padx=5)
        
        ctk.CTkButton(btn_row, 
                      text="🗑 Удалить",
                      font=DesignConfig.FONT_SUBHEADER,
                      height=45,
                      corner_radius=10,
                      fg_color=DesignConfig.DANGER_COLOR,
                      hover_color="#dc2626",
                      command=self.remove_proxy).pack(side="left", padx=5)
        
        ctk.CTkButton(btn_row, 
                      text="🧪 Тест подключения",
                      font=DesignConfig.FONT_SUBHEADER,
                      height=45,
                      corner_radius=10,
                      fg_color=DesignConfig.SUCCESS_COLOR,
                      hover_color="#059669",
                      command=lambda: self.run_async(self.test_proxy_connection)).pack(side="left", padx=5)

        self.proxy_status = ctk.CTkLabel(settings_inner, text="", 
                                         font=DesignConfig.FONT_NORMAL,
                                         wraplength=600)
        self.proxy_status.pack(pady=15)

    def quick_parse_and_save(self):
        """Быстрый парсинг и привязка прокси"""
        proxy_str = self.pr_quick_entry.get().strip()
        if not proxy_str:
            self.quick_status.configure(text="⚠️ Введите прокси", text_color="#f59e0b")
            return
        
        proxy = self.parse_proxy_string(proxy_str)
        if not proxy:
            self.quick_status.configure(text="❌ Неверный формат", text_color="#ef4444")
            return
        
        # Заполняем поля
        self.pr_ip.delete(0, 'end')
        self.pr_ip.insert(0, proxy[1])
        self.pr_port.delete(0, 'end')
        self.pr_port.insert(0, str(proxy[2]))
        self.pr_user.delete(0, 'end')
        self.pr_user.insert(0, proxy[4])
        self.pr_pass.delete(0, 'end')
        self.pr_pass.insert(0, proxy[5])
        
        # Сохраняем
        self.save_proxy()
        self.quick_status.configure(text=f"✅ Распознано: {proxy[1]}:{proxy[2]}", text_color="#10b981")

    async def test_proxy_connection(self):
        """Тестирование подключения к Telegram через прокси"""
        proxy = self.get_proxy_for_test()
        if not proxy:
            self.proxy_status.configure(text="⚠️ Введите данные прокси или выберите аккаунт", text_color="orange")
            return

        self.proxy_status.configure(text="⏳ Тестирование...", text_color="orange")
        self.log("🧪 Тестирование прокси...")

        # Временная сессия для теста
        test_session = os.path.join(self.sessions_dir, "test_proxy_session")
        
        client = create_telethon_client(test_session, proxy=proxy)
        
        try:
            await client.connect()
            
            if await client.is_user_authorized():
                me = await client.get_me()
                self.proxy_status.configure(text=f"✅ Успешно! Аккаунт: {me.first_name}", text_color="green")
                self.log(f"✅ Прокси работает! Аккаунт: {me.first_name}", "success")
            else:
                self.proxy_status.configure(text="✅ Подключение успешно (требуется авторизация)", text_color="green")
                self.log("✅ Прокси работает - подключение успешно", "success")
                
            await client.disconnect()
            
        except Exception as e:
            self.proxy_status.configure(text=f"❌ Ошибка подключения: {e}", text_color="red")
            self.log(f"❌ Ошибка прокси: {e}", "error")
        finally:
            # Удаляем тестовую сессию
            try:
                for ext in ["", ".session", ".session-journal"]:
                    path = test_session + ext if ext else test_session
                    if os.path.exists(path):
                        if os.path.isfile(path):
                            os.remove(path)
                        elif os.path.isdir(path):
                            shutil.rmtree(path)
            except:
                pass

    def get_proxy_for_test(self):
        """Получение прокси для тестирования"""
        # Сначала пробуем из полей ввода (формат ip:port:user:pass)
        ip = self.pr_ip.get().strip()
        port = self.pr_port.get().strip()
        user = self.pr_user.get().strip()
        password = self.pr_pass.get().strip()
        
        if ip and port:
            try:
                return ("socks5", ip, int(port), True, user, password)
            except ValueError:
                return None
        
        # Если нет, пробуем прокси текущего аккаунта
        if self.current_session != "ВСЕ":
            return self.get_proxy(self.current_session)
        
        return None

    def parse_proxy_string(self, proxy_str):
        """Парсинг строки прокси в формате ip:port:user:pass или user:pass@ip:port"""
        proxy_str = proxy_str.strip()
        
        # Формат user:pass@ip:port
        if '@' in proxy_str:
            try:
                auth, server = proxy_str.split('@')
                user, password = auth.split(':', 1)
                ip, port = server.rsplit(':', 1)
                return ("socks5", ip.strip(), int(port.strip()), True, user.strip(), password.strip())
            except:
                return None
        
        # Формат ip:port:user:pass
        parts = proxy_str.split(':')
        if len(parts) == 4:
            try:
                return ("socks5", parts[0], int(parts[1]), True, parts[2], parts[3])
            except:
                return None
        
        return None

    def save_proxy(self):
        if self.current_session == "ВСЕ":
            self.log("⚠️ Выберите конкретный аккаунт слева!", "warning")
            self.proxy_status.configure(text="Выберите аккаунт", text_color="orange")
            return

        ip = self.pr_ip.get().strip()
        port = self.pr_port.get().strip()
        user = self.pr_user.get().strip()
        password = self.pr_pass.get().strip()
        
        if ip and port:
            try:
                os.makedirs(self.proxy_dir, exist_ok=True)
                with open(f"{self.proxy_dir}/{self.current_session}.json", "w", encoding='utf-8') as f:
                    json.dump({
                        "hostname": ip,
                        "port": int(port),
                        "username": user,
                        "password": password
                    }, f, indent=2)
                self.log(f"✅ Прокси привязан к {self.current_session}", "success")
                self.proxy_status.configure(text=f"Прокси сохранен для {self.current_session}", text_color="green")
            except ValueError:
                self.log("⚠️ Неверный формат порта!", "warning")
                self.proxy_status.configure(text="Неверный формат порта", text_color="red")
        else:
            self.log("⚠️ Введите IP и Port!", "warning")
            self.proxy_status.configure(text="Введите IP и Port", text_color="red")

    def remove_proxy(self):
        if self.current_session == "ВСЕ":
            self.log("⚠️ Выберите конкретный аккаунт", "warning")
            return
        
        proxy_file = f"{self.proxy_dir}/{self.current_session}.json"
        if os.path.exists(proxy_file):
            os.remove(proxy_file)
            self.log(f"✅ Прокси для {self.current_session} удален", "success")
            self.proxy_status.configure(text="Прокси удален", text_color="green")
        else:
            self.log(f"⚠️ Прокси для {self.current_session} не найден", "warning")

    # ==================== ОБЩИЕ МЕТОДЫ ====================
    def add_session(self):
        """Добавление новой сессии через авторизацию"""
        auth_window = ctk.CTkToplevel(self)
        auth_window.title("Добавление сессии")
        auth_window.geometry("450x400")
        auth_window.attributes('-topmost', True)

        ctk.CTkLabel(auth_window, text="НОВЫЙ АККАУНТ", font=("Arial", 18, "bold")).pack(pady=15)

        ctk.CTkLabel(auth_window, text="Номер телефона (с +):").pack()
        phone_entry = ctk.CTkEntry(auth_window, placeholder_text="+79991234567", width=300)
        phone_entry.pack(pady=10)
        add_bindings(phone_entry)

        status_label = ctk.CTkLabel(auth_window, text="", wraplength=350)
        status_label.pack(pady=10)

        code_entry = None
        code_frame = ctk.CTkFrame(auth_window, fg_color="transparent")

        async def start_auth():
            nonlocal code_entry, code_frame
            phone = phone_entry.get().strip()
            if not phone:
                status_label.configure(text="⚠️ Введите номер", text_color="red")
                return

            if not phone.startswith('+'):
                status_label.configure(text="⚠️ Номер должен начинаться с +", text_color="red")
                return

            session_name = hashlib.md5(phone.encode()).hexdigest()[:12]
            session_path = os.path.join(self.sessions_dir, session_name)
            proxy = self.get_proxy(session_name)

            status_label.configure(text="⏳ Подключение...", text_color="orange")

            client = create_telethon_client(session_path, proxy=proxy)
            
            try:
                await client.connect()
                
                if await client.is_user_authorized():
                    status_label.configure(text="✅ Уже авторизован!", text_color="green")
                    await client.disconnect()
                    auth_window.after(1500, auth_window.destroy)
                    self.refresh_sessions()
                    return

                # Отправляем код
                status_label.configure(text="📲 Отправка кода...", text_color="orange")
                await client.send_code_request(phone)
                
                status_label.configure(text="✅ Код отправлен! Проверьте Telegram", text_color="green")
                
                # Показываем поле для кода
                code_frame.pack(fill="x", padx=20, pady=10)
                ctk.CTkLabel(code_frame, text="Код из Telegram:").pack()
                code_entry = ctk.CTkEntry(code_frame, placeholder_text="12345", width=200)
                code_entry.pack(pady=5)
                add_bindings(code_entry)
                
                ctk.CTkButton(code_frame, text="Войти", fg_color="green",
                              command=lambda: self.run_async(lambda: complete_auth(client, phone, code_entry, status_label, auth_window))
                              ).pack(pady=10)

            except Exception as e:
                status_label.configure(text=f"❌ Ошибка: {e}", text_color="red")
                try:
                    await client.disconnect()
                except:
                    pass

        async def complete_auth(client, phone, code_entry, status_label, auth_window):
            code = code_entry.get().strip()
            if not code:
                status_label.configure(text="⚠️ Введите код", text_color="red")
                return

            try:
                await client.sign_in(phone, code)
                me = await client.get_me()
                status_label.configure(text=f"✅ Успешно: {me.first_name} (@{me.username or 'N/A'})", text_color="green")
                
                self.log(f"✅ Добавлен аккаунт: {me.first_name} (@{me.username})", "success")
                
                auth_window.after(1500, auth_window.destroy)
                self.refresh_sessions()
            except Exception as e:
                status_label.configure(text=f"❌ Ошибка входа: {e}", text_color="red")
            finally:
                await client.disconnect()

        ctk.CTkButton(auth_window, text="📲 Отправить код", fg_color="#1f538d", height=40,
                      command=lambda: self.run_async(start_auth)).pack(pady=20)
        
        ctk.CTkLabel(auth_window, text="Код придет в официальный Telegram", 
                     font=("Arial", 9), text_color="gray").pack()

    def refresh_sessions(self):
        files = [f.replace(".session", "") for f in os.listdir(self.sessions_dir) if f.endswith(".session")]
        self.session_menu.configure(values=["ВСЕ"] + sorted(files) if files else ["ВСЕ"])
        self.log(f"🔄 Найдено сессий: {len(files)}")

    async def check_all_sessions(self):
        """Проверка всех сессий на валидность"""
        accs = [f.replace(".session", "") for f in os.listdir(self.sessions_dir) if f.endswith(".session")]
        if not accs:
            self.log("⚠️ Нет сессий для проверки", "warning")
            return

        self.log(f"✓ Проверка {len(accs)} сессий...")
        valid = 0
        invalid = 0

        for acc in accs:
            session_path = os.path.join(self.sessions_dir, acc)
            proxy = self.get_proxy(acc)

            client = create_telethon_client(session_path, proxy=proxy)
            try:
                await client.connect()
                if await client.is_user_authorized():
                    me = await client.get_me()
                    self.log(f"✅ {acc} - @{me.username or 'N/A'}", "success")
                    valid += 1
                else:
                    self.log(f"❌ {acc} - Не авторизован", "error")
                    invalid += 1
            except Exception as e:
                self.log(f"⚠️ {acc} - Ошибка: {e}", "warning")
                invalid += 1
            finally:
                await client.disconnect()

        self.log(f"✅ Проверка завершена! Валидных: {valid}, Невалидных: {invalid}", "success")

    def load_txt(self):
        p = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if p:
            self.selected_db_path = p
            self.db_info.configure(text=os.path.basename(p), text_color="green")

    def get_proxy(self, session_name):
        path = os.path.join(self.proxy_dir, f"{session_name}.json")
        if os.path.exists(path):
            with open(path, "r", encoding='utf-8') as f:
                p = json.load(f)
                return ("socks5", p['hostname'], int(p['port']), True, p['username'], p['password'])
        return None

    def clear_log(self):
        """Очистить журнал событий"""
        self.log_view.delete("1.0", "end")
        self.log("🗑 Журнал очищен", "info")

    def copy_log(self):
        """Копировать весь текст лога в буфер обмена"""
        log_text = self.log_view.get("1.0", "end")
        self.clipboard_clear()
        self.clipboard_append(log_text)
        self.log("✅ Лог скопирован в буфер обмена", "success")

    def show_frame(self, name):
        """Переключить видимый фрейм с подсветкой кнопки"""
        # Снять подсветку со всех кнопок
        for btn_name, btn in self.menu_buttons.items():
            btn.configure(fg_color="transparent")

        # Подсветить активную кнопку
        if name in self.menu_buttons:
            self.menu_buttons[name].configure(fg_color=DesignConfig.BG_CARD)

        # Скрыть все фреймы
        for f in self.frames.values():
            f.pack_forget()

        # Показать нужный фрейм - fill BOTH чтобы занимал всю область
        if name in self.frames:
            self.frames[name].pack(fill="both", expand=True)

        # Обновить заголовок
        self.page_title.configure(text=name)

        # Обновить информацию о сессии
        self.session_info.configure(text=f"Аккаунт: {self.current_session}")
        
        # Принудительно обновляем layout
        self.update_idletasks()

    def run_async(self, coro):
        """Запускает асинхронную функцию в отдельном потоке"""
        def run_coro():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(coro())
            except Exception as e:
                self.log(f"❌ Ошибка в async функции: {e}", "error")
            finally:
                loop.close()

        threading.Thread(target=run_coro, daemon=True).start()


if __name__ == "__main__":
    # Проверка зависимостей
    try:
        import telethon
        import customtkinter
        import requests
        logger.info("✅ Все зависимости установлены")
    except ImportError as e:
        logger.error(f"❌ Отсутствуют зависимости: {e}")
        print(f"Установите зависимости: pip install telethon customtkinter requests")
        exit(1)

    def start_app():
        """Запуск основного приложения после авторизации"""
        app = ArbitrageApp()
        app.mainloop()

    auth = LoginWindow(on_success=start_app)
    auth.mainloop()
