"""
GEMINI ULTIMATE v40.0 - Cryptocurrency Arbitrage Scanner
Версия с ОТЛАДКОЙ и обработкой ошибок
"""

import asyncio
import threading
import webbrowser
import winsound
import hashlib
import sys
import logging
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import time
from collections import defaultdict

# GUI
import customtkinter as ctk
from tkinter import messagebox, Menu

# Network & API
import requests
import pyperclip
import ccxt.pro as ccxt

# ============================================================================
# КОНФИГУРАЦИЯ И ЛОГИРОВАНИЕ
# ============================================================================

LOGS_DIR = Path(__file__).parent / "logs"
DATA_DIR = Path(__file__).parent / "data"
LOGS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

def setup_logging():
    log_file = LOGS_DIR / f"arb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8', mode='w'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("Gemini")

logger = setup_logging()

# ============================================================================
# ЛИЦЕНЗИЯ
# ============================================================================

LICENSE_SERVER_URL = 'https://gist.githubusercontent.com/shdgegesh-collab/17f3b02936ced28ef3877eae177cd650/raw/arb'

def get_hwid() -> str:
    try:
        import wmi
        c = wmi.WMI()
        proc = c.Win32_Processor()[0].ProcessorId.strip()
        board = c.Win32_BaseBoard()[0].SerialNumber.strip()
        return hashlib.sha256(f"{proc}-{board}".encode()).hexdigest()[:16].upper()
    except:
        import platform
        return hashlib.md5(f"{platform.node()}{platform.processor()}".encode()).hexdigest()[:16].upper()

def check_access():
    user_hwid = get_hwid()
    try:
        response = requests.get(LICENSE_SERVER_URL + f"?t={time.time()}", timeout=10)
        if user_hwid not in [line.strip() for line in response.text.splitlines() if line.strip()]:
            pyperclip.copy(user_hwid)
            time.sleep(0.5)
            root = ctk.CTk()
            root.withdraw()
            messagebox.showerror("LICENSE ERROR", f"HWID:\n{user_hwid}\n\nСКОПИРОВАН!")
            sys.exit(1)
        logger.info(f"✅ Лицензия OK: {user_hwid}")
    except Exception as e:
        logger.error(f"Лицензия: {e}")
        root = ctk.CTk()
        root.withdraw()
        if not messagebox.askyesno("Error", "Продолжить в демо-режиме?"):
            sys.exit(1)

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

URLS = {
    'binance': 'https://www.binance.com/en/trade/{}_USDT',
    'bybit': 'https://www.bybit.com/trade/spot/{}/USDT',
    'okx': 'https://www.okx.com/markets/spot/{}-usdt',
    'bitget': 'https://www.bitget.com/spot/{}_USDT',
    'kucoin': 'https://www.kucoin.com/trade/{}-USDT',
    'mexc': 'https://www.mexc.com/exchange/{}_USDT',
    'gateio': 'https://www.gate.io/trade/{}_USDT',
    'lbank': 'https://www.lbank.com/trade/{}_usdt'
}

SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT', 'DOT/USDT', 'LTC/USDT']

# ============================================================================
# СКАНЕР
# ============================================================================

class ArbitrageScanner:
    def __init__(self, exchange_ids: List[str], config: dict, log_callback):
        self.exchange_ids = exchange_ids
        self.config = config
        self.log_callback = log_callback
        self.running = False
        self.exchanges: Dict = {}
        self.stats = {'opportunities': 0, 'best_roi': 0, 'scans': 0}
        
    def log(self, msg: str, level: str = "info"):
        logger.info(msg)
        if self.log_callback:
            self.log_callback(msg, level)
    
    async def connect_exchanges(self):
        """Подключение к биржам"""
        self.log("🔌 Подключение к биржам...", "info")
        logger.info(f"Попытка подключения к: {self.exchange_ids}")
        
        connected = 0
        for eid in self.exchange_ids:
            try:
                self.log(f"⏳ {eid.upper()}...", "info")
                
                exchange_class = getattr(ccxt, eid, None)
                if not exchange_class:
                    self.log(f"❌ {eid.upper()} - не найден в ccxt", "error")
                    continue
                
                exchange = exchange_class({
                    'enableRateLimit': True,
                    'timeout': 30000,
                    'options': {'defaultType': 'spot'}
                })
                
                await asyncio.wait_for(exchange.load_markets(), timeout=25)
                
                self.exchanges[eid] = exchange
                self.log(f"✅ {eid.upper()} - {len(exchange.symbols)} пар", "success")
                connected += 1
                
            except asyncio.TimeoutError:
                self.log(f"⏱️ {eid.upper()} - таймаут 30 сек", "error")
            except Exception as e:
                error_msg = str(e)[:80]
                self.log(f"❌ {eid.upper()} - {type(e).__name__}: {error_msg}", "error")
                logger.debug(f"Ошибка {eid}: {traceback.format_exc()}")
        
        self.log(f"📊 Подключено: {connected}/{len(self.exchange_ids)}", "success" if connected > 0 else "error")
        return connected > 0
    
    async def scan_symbol(self, symbol: str):
        """Сканирование символа"""
        while self.running:
            try:
                prices = {}
                
                for eid, exchange in list(self.exchanges.items()):
                    try:
                        ob = await asyncio.wait_for(
                            exchange.watch_order_book(symbol),
                            timeout=10
                        )
                        if ob and ob.get('asks') and ob.get('bids'):
                            prices[eid] = {
                                'ask': ob['asks'][0][0],
                                'bid': ob['bids'][0][0]
                            }
                    except asyncio.TimeoutError:
                        pass
                    except Exception as e:
                        logger.debug(f"{eid} {symbol}: {e}")
                
                if len(prices) >= 2:
                    await self._find_arbitrage(symbol, prices)
                
                await asyncio.sleep(0.5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"scan {symbol}: {e}")
                await asyncio.sleep(2)
    
    async def _find_arbitrage(self, symbol: str, prices: Dict):
        """Поиск арбитража"""
        min_roi = self.config.get('min_roi', 0.0)
        deposit = self.config.get('deposit', 1000)
        fee = 0.002
        
        for buy_ex, buy_data in prices.items():
            for sell_ex, sell_data in prices.items():
                if buy_ex == sell_ex:
                    continue
                
                buy_price = buy_data['ask']
                sell_price = sell_data['bid']
                
                net_roi = ((sell_price / buy_price - 1) * 100) - (fee * 100)
                
                if net_roi >= min_roi:
                    profit = deposit * (net_roi / 100)
                    self.stats['opportunities'] += 1
                    if net_roi > self.stats['best_roi']:
                        self.stats['best_roi'] = net_roi
                    
                    self._report(symbol, buy_ex, sell_ex, buy_price, sell_price, net_roi, profit)
    
    def _report(self, symbol, buy_ex, sell_ex, buy_price, sell_price, roi, profit):
        coin = symbol.split('/')[0]
        buy_link = URLS.get(buy_ex, '#').format(coin)
        sell_link = URLS.get(sell_ex, '#').format(coin)
        
        msg = (f"💎 {symbol}\n"
               f"💰 ROI: {roi:.2f}% | ПРОФИТ: ${profit:.2f}\n"
               f"🛒 {buy_ex.upper()}: ${buy_price:,.2f}\n"
               f"📈 {sell_ex.upper()}: ${sell_price:,.2f}")
        
        self.log(msg, "opportunity")
        
        if self.config.get('sound', False):
            try:
                winsound.Beep(1000, 200)
            except:
                pass
    
    async def run_loop(self):
        """Основной цикл"""
        try:
            self.running = True
            self.log("🚀 GEMINI v40.0 ЗАПУЩЕН", "success")
            self.log(f"📊 Бирж: {len(self.exchange_ids)} | Символов: {len(SYMBOLS)}", "info")
            
            # Подключение
            if not await self.connect_exchanges():
                self.log("⚠️ НИ ОДНА БИРЖА НЕ ПОДКЛЮЧЕНА!", "error")
            
            await asyncio.sleep(2)
            
            # Тестовый сигнал
            await self._test_signal()
            
            # Запуск сканирования
            tasks = []
            for symbol in SYMBOLS:
                tasks.append(asyncio.create_task(self.scan_symbol(symbol)))
            
            scan_count = 0
            while self.running:
                scan_count += 1
                self.stats['scans'] += 1
                
                if scan_count % 5 == 0:
                    self.log(f"🔄 Цикл #{scan_count} | Найдено: {self.stats['opportunities']}", "info")
                
                await asyncio.sleep(1)
            
            # Остановка
            for task in tasks:
                task.cancel()
            
            for ex in self.exchanges.values():
                try:
                    await ex.close()
                except:
                    pass
            
            self.log(f"✅ Стоп. Найдено: {self.stats['opportunities']}", "success")
            
        except Exception as e:
            logger.error(f"CRITICAL: {e}")
            logger.error(traceback.format_exc())
            self.log(f"❌ CRITICAL ERROR: {str(e)[:100]}", "error")
            self.log(traceback.format_exc()[:500], "error")
    
    async def _test_signal(self):
        """Тестовый сигнал"""
        self.log("🧪 ТЕСТ СИГНАЛ...", "test")
        msg = ("💎 BTC/USDT\n"
               "💰 ROI: 1.00% | ПРОФИТ: $10.00\n"
               "🛒 MEXC: $95000\n"
               "📈 GATEIO: $96000\n"
               "✅ СИСТЕМА РАБОТАЕТ!")
        self.log(msg, "opportunity")
        try:
            winsound.Beep(1000, 200)
        except:
            pass


# ============================================================================
# GUI
# ============================================================================

class CopyPasteEntry(ctk.CTkEntry):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.menu = Menu(self, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#00d9ff")
        self.menu.add_command(label="📋 Копировать", command=self._copy)
        self.menu.add_command(label="📥 Вставить", command=self._paste)
        self.bind("<Button-3>", self._show_menu)
        self.bind("<Control-v>", lambda e: self._paste())
    
    def _show_menu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)
    
    def _copy(self):
        if t := self.get(): pyperclip.copy(t)
    
    def _paste(self):
        if t := pyperclip.paste():
            self.delete(0, 'end')
            self.insert(0, t)


class CopyPasteText(ctk.CTkTextbox):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.menu = Menu(self._textbox, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#00d9ff")
        self.menu.add_command(label="📋 Копировать", command=self._copy)
        self.menu.add_command(label="📥 Вставить", command=self._paste)
        self.menu.add_command(label="🗑️ Очистить", command=self._clear)
        self._textbox.bind("<Button-3>", self._show_menu)
        self._textbox.bind("<Control-v>", lambda e: self._paste())
    
    def _show_menu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)
    
    def _copy(self):
        try:
            pyperclip.copy(self._textbox.get("sel.first", "sel.last"))
        except:
            pyperclip.copy(self._textbox.get("1.0", "end-1c"))
    
    def _paste(self):
        if t := pyperclip.paste(): self._textbox.insert("insert", t)
    
    def _clear(self):
        self._textbox.delete("1.0", "end")


class UltimateGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        logger.info("=" * 50)
        logger.info("ЗАПУСК GEMINI v40.0")
        logger.info("=" * 50)
        
        check_access()
        
        self.title("GEMINI v40.0 DEBUG")
        self.geometry("1200x800")
        ctk.set_appearance_mode("dark")
        
        self.scanner = None
        self.loop = None
        self.is_running = False
        
        self._setup_ui()
        
        logger.info("GUI создан")
    
    def _setup_ui(self):
        logger.info("Создание UI...")
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=320, fg_color="#111")
        self.sidebar.pack(side="left", fill="y", padx=5, pady=5)
        
        # Header
        ctk.CTkLabel(self.sidebar, text="💎 GEMINI", font=ctk.CTkFont("Impact", 28), 
                    text_color="#00d9ff").pack(pady=15)
        ctk.CTkLabel(self.sidebar, text="v40.0 DEBUG", font=ctk.CTkFont(size=12), 
                    text_color="#666").pack()
        
        # Settings
        settings = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        settings.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Load Level
        ctk.CTkLabel(settings, text="⚙️ LOAD LEVEL", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.load_lvl = ctk.CTkSegmentedButton(settings, values=["Low", "Medium", "Overload"])
        self.load_lvl.set("Low")  # Меньше нагрузка для теста
        self.load_lvl.pack(fill="x", pady=5)
        
        # Параметры
        ctk.CTkLabel(settings, text="💰 ПАРАМЕТРЫ", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 3))
        self.roi_entry = CopyPasteEntry(settings, justify="center", height=30)
        self.roi_entry.insert(0, "-10.0")
        ctk.CTkLabel(settings, text="МИН ROI %").pack()
        self.roi_entry.pack(fill="x", pady=3)
        
        # Биржи
        ctk.CTkLabel(settings, text="🏛️ БИРЖИ", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 3))
        self.ex_vars = {}
        for ex in ['mexc', 'gateio', 'bitget', 'kucoin', 'lbank']:  # Только рабочие
            v = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(settings, text=ex.upper(), variable=v).pack(anchor="w", pady=2)
            self.ex_vars[ex] = v
        
        # Кнопка START
        self.btn = ctk.CTkButton(self.sidebar, text="▶️ START", command=self.toggle,
                                fg_color="#00d9ff", text_color="black",
                                font=ctk.CTkFont(size=16, weight="bold"), height=50)
        self.btn.pack(side="bottom", pady=20, padx=20, fill="x")
        
        # Статус
        self.status = ctk.CTkLabel(self.sidebar, text="⏸️ STOPPED", font=ctk.CTkFont(size=14))
        self.status.pack(pady=(0, 20))
        
        # Лог
        self.txt = CopyPasteText(self, font=ctk.CTkFont("Consolas", 12))
        self.txt.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Теги
        tb = self.txt._textbox
        tb.tag_config("time", foreground="#666")
        tb.tag_config("success", foreground="#00ff88")
        tb.tag_config("error", foreground="#ff4444")
        tb.tag_config("warning", foreground="#ffaa00")
        tb.tag_config("opportunity", foreground="#00d9ff")
        tb.tag_config("info", foreground="#cccccc")
        tb.tag_config("test", foreground="#ffff00")
        
        logger.info("UI создан")
    
    def add_log(self, msg: str, level: str = "info"):
        tb = self.txt._textbox
        tb.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] ", "time")
        tag = level if level in ["success", "error", "warning", "opportunity", "test"] else "info"
        tb.insert("end", msg + "\n" + "-" * 60 + "\n", tag)
        tb.see("end")
        logger.info(f"LOG [{level}]: {msg[:100]}")
    
    def toggle(self):
        """Кнопка START/STOP"""
        logger.info(f"toggle() нажата! is_running={self.is_running}")
        
        if not self.is_running:
            try:
                self.btn.configure(text="⏹️ STOP", fg_color="#ff4444")
                self.status.configure(text="🟢 RUNNING", text_color="#00ff88")
                self.is_running = True
                
                config = {
                    'min_roi': float(self.roi_entry.get() or 0),
                    'deposit': 1000,
                    'sound': True
                }
                
                exchange_ids = [k for k, v in self.ex_vars.items() if v.get()]
                
                logger.info(f"Конфиг: {config}")
                logger.info(f"Биржи: {exchange_ids}")
                
                self.add_log("🚀 ЗАПУСК...", "success")
                
                self.scanner = ArbitrageScanner(exchange_ids, config, self.add_log)
                
                def run_loop():
                    try:
                        logger.info("Создание event loop...")
                        self.loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(self.loop)
                        logger.info("Запуск run_loop...")
                        self.loop.run_until_complete(self.scanner.run_loop())
                    except Exception as e:
                        logger.error(f"Ошибка в потоке: {e}")
                        logger.error(traceback.format_exc())
                        self.add_log(f"❌ ОШИБКА: {str(e)[:100]}", "error")
                
                logger.info("Создание потока...")
                thread = threading.Thread(target=run_loop, daemon=True)
                thread.start()
                logger.info(f"Поток запущен: {thread.ident}")
                
            except Exception as e:
                logger.error(f"Ошибка в toggle: {e}")
                logger.error(traceback.format_exc())
                self.add_log(f"❌ ОШИБКА ЗАПУСКА: {str(e)[:100]}", "error")
                self.is_running = False
                self.btn.configure(text="▶️ START", fg_color="#00d9ff")
        else:
            self.btn.configure(text="▶️ START", fg_color="#00d9ff")
            self.status.configure(text="⏸️ STOPPED", text_color="#888")
            self.is_running = False
            if self.scanner:
                self.scanner.running = False
            self.add_log("🛑 ОСТАНОВЛЕНО", "warning")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("GEMINI v40.0 - ЗАПУСК ПРИЛОЖЕНИЯ")
    logger.info("=" * 60)
    
    try:
        logger.info("Создание UltimateGUI...")
        app = UltimateGUI()
        logger.info("Запуск mainloop...")
        app.mainloop()
        logger.info("mainloop завершен")
    except Exception as e:
        logger.critical(f"CRITICAL: {e}")
        logger.critical(traceback.format_exc())
        messagebox.showerror("CRITICAL ERROR", str(e))
