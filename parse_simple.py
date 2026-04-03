import asyncio
from telethon import TelegramClient, events
from telethon.tl.functions.messages import ImportChatInviteRequest, CheckChatInviteRequest
from telethon.tl.functions.messages import AddChatUserRequest
from telethon.tl.types import ChannelParticipantsAdmins
from telethon.errors import FloodWaitError, ChatAdminRequiredError, UserPrivacyRestrictedError
import os
import csv
import json
import random
import re

API_ID = 36925315
API_HASH = "e4c7b45f2331be96a242cce6e3b3c1c1"

class TelegramTools:
    def __init__(self):
        self.client = None
    
    async def connect(self):
        """Подключение к Telegram"""
        print("\n🔄 Подключение к Telegram...")
        self.client = TelegramClient("session", API_ID, API_HASH)
        await self.client.connect()
        
        if not await self.client.is_user_authorized():
            print("\n❌ Нужно войти в Telegram!")
            phone = input("Телефон (+7...): ").strip()
            print("📲 Отправляю код...")
            await self.client.send_code_request(phone)
            code = input("Введите код из Telegram: ").strip()
            await self.client.sign_in(phone, code)
            print("✅ Вход выполнен!")
        
        me = await self.client.get_me()
        print(f"✅ Подключено: {me.first_name} (@{me.username or 'N/A'})")
    
    async def disconnect(self):
        if self.client:
            await self.client.disconnect()
    
    async def parse_users(self):
        """1. ПАРСИНГ УЧАСТНИКОВ"""
        print("\n" + "="*60)
        print("🔍 ПАРСИНГ УЧАСТНИКОВ")
        print("="*60)
        
        target = input("\n📋 Целевой чат (username или ссылка): ").strip().replace("@", "").replace("https://t.me/", "")
        limit = int(input("👥 Лимит участников (например 1000): ") or "1000")
        
        print(f"\n🔄 Парсинг @{target}...")
        users = set()
        stats = {'total': 0, 'bots': 0, 'deleted': 0}
        
        # Метод 1: Прямой сбор
        print("\n📋 Метод 1: Сбор участников...")
        try:
            async for user in self.client.iter_participants(target, limit=limit):
                stats['total'] += 1
                if user.bot:
                    stats['bots'] += 1
                    continue
                if user.deleted:
                    stats['deleted'] += 1
                    continue
                if user.username:
                    users.add(f"@{user.username}")
                    if len(users) % 100 == 0:
                        print(f"  📈 Найдено: {len(users)}")
        except Exception as e:
            print(f"  ⚠️ Метод 1: {str(e)[:60]}")
        
        # Метод 2: Из сообщений
        if len(users) < limit:
            print("\n📋 Метод 2: Сбор из сообщений...")
            try:
                async for message in self.client.iter_messages(target, limit=5000):
                    if len(users) >= limit:
                        break
                    if message.sender and getattr(message.sender, 'username', None):
                        users.add(f"@{message.sender.username}")
            except Exception as e:
                print(f"  ⚠️ Метод 2: {str(e)[:60]}")
        
        # Сохранение
        if users:
            os.makedirs("parsed_data", exist_ok=True)
            fmt = input("\n💾 Формат (txt/csv/json) [txt]: ").strip() or "txt"
            filename = f"parsed_data/{target}.{fmt}"
            
            if fmt == "txt":
                with open(filename, "w", encoding="utf-8") as f:
                    f.write("\n".join(sorted(users)))
            elif fmt == "csv":
                with open(filename, "w", newline='', encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(['username'])
                    for u in sorted(users):
                        writer.writerow([u])
            elif fmt == "json":
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(sorted(list(users)), f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ ГОТОВО! Собрано {len(users)} пользователей")
            print(f"💾 Сохранено в: {filename}")
        else:
            print("❌ Не удалось собрать пользователей")
    
    async def search_chats(self):
        """2. ПОИСК ЧАТОВ"""
        print("\n" + "="*60)
        print("📢 ПОИСК ЧАТОВ")
        print("="*60)
        
        query = input("\n🔑 Ключевые слова: ").strip()
        limit = int(input("📊 Лимит результатов: ") or "50")
        
        print(f"\n🔄 Поиск по запросу: {query}")
        results = []
        
        # Поиск через глобальный поиск
        try:
            from telethon.tl.functions.contacts import SearchRequest
            search_result = await self.client(SearchRequest(q=query, limit=limit))
            
            for chat in search_result.chats:
                if hasattr(chat, 'title'):
                    results.append({
                        'title': chat.title,
                        'username': getattr(chat, 'username', 'N/A'),
                        'participants': getattr(chat, 'participants_count', 'N/A')
                    })
        except Exception as e:
            print(f"  ⚠️ Ошибка: {str(e)[:60]}")
        
        # Вывод результатов
        if results:
            print(f"\n✅ Найдено {len(results)} чатов:\n")
            for i, r in enumerate(results[:limit], 1):
                print(f"{i}. {r['title']}")
                print(f"   @{r['username']} | Участников: {r['participants']}")
                print(f"   https://t.me/{r['username']}")
                print()
            
            save = input("💾 Сохранить? (y/n): ").strip().lower()
            if save == 'y':
                os.makedirs("parsed_data", exist_ok=True)
                with open(f"parsed_data/search_{query}.txt", "w", encoding="utf-8") as f:
                    for r in results:
                        f.write(f"@{r['username']} - {r['title']}\n")
                print("✅ Сохранено!")
        else:
            print("❌ Ничего не найдено")
    
    async def invite_users(self):
        """3. ИНВАЙТЕР"""
        print("\n" + "="*60)
        print("👥 ИНВАЙТЕР")
        print("="*60)
        
        db_path = input("\n📂 Путь к базе (.txt): ").strip()
        if not os.path.exists(db_path):
            print(f"❌ Файл {db_path} не найден!")
            return
        
        target = input("📋 Целевой чат: ").strip().replace("@", "")
        invite_limit = int(input("👥 Лимит приглашений: ") or "50")
        delay_min = int(input("⏱ Мин. задержка (сек): ") or "30")
        delay_max = int(input("⏱ Макс. задержка (сек): ") or "60")
        
        with open(db_path, 'r', encoding="utf-8") as f:
            usernames = [line.strip().replace("@", "") for line in f if line.strip()]
        
        print(f"\n🚀 Запуск инвайта в @{target}...")
        stats = {'success': 0, 'failed': 0, 'limited': 0}
        
        try:
            entity = await self.client.get_entity(target)
            print(f"✅ Чат найден: {entity.title}")
            
            for i, username in enumerate(usernames[:invite_limit]):
                try:
                    user = await self.client.get_entity(username)
                    await self.client(AddChatUserRequest(
                        chat_id=entity.id,
                        user_id=user.id,
                        fwd_limit=0
                    ))
                    stats['success'] += 1
                    print(f"✅ @{username} ({stats['success']}/{i+1})")
                except FloodWaitError as e:
                    print(f"⏳ FloodWait: ждём {e.seconds} сек")
                    stats['limited'] += 1
                    await asyncio.sleep(e.seconds + 5)
                except Exception as e:
                    stats['failed'] += 1
                    print(f"❌ @{username}: {str(e)[:40]}")
                
                await asyncio.sleep(random.uniform(delay_min, delay_max))
            
            print(f"\n✅ Инвайт завершён!")
            print(f"   ✅ Успешно: {stats['success']}")
            print(f"   ❌ Ошибок: {stats['failed']}")
            print(f"   ⏳ Лимитов: {stats['limited']}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    async def join_by_link(self):
        """4. ВХОД ПО ССЫЛКЕ"""
        print("\n" + "="*60)
        print("🔗 ВХОД ПО ССЫЛКЕ-ПРИГЛАШЕНИЮ")
        print("="*60)
        
        link = input("\n📎 Ссылка-приглашение: ").strip()
        
        hash_match = re.search(r'(?:t\.me/|\+|joinchat/)(\+?[A-Za-z0-9_-]+)', link)
        if not hash_match:
            print("❌ Неверный формат ссылки!")
            return
        
        invite_hash = hash_match.group(1).lstrip('+')
        print(f"🔍 Хэш: {invite_hash}")
        
        try:
            invite_info = await self.client(CheckChatInviteRequest(invite_hash))
            if hasattr(invite_info, 'chat'):
                print(f"📊 Чат: {invite_info.chat.title}")
        except Exception as e:
            print(f"  ⚠️ Не удалось получить информацию: {e}")
        
        try:
            result = await self.client(ImportChatInviteRequest(invite_hash))
            if hasattr(result, 'chats') and result.chats:
                print(f"✅ Успешный вход в: {result.chats[0].title}")
            else:
                print("✅ Вход выполнен!")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    async def spam(self):
        """5. РАССЫЛКА"""
        print("\n" + "="*60)
        print("📨 РАССЫЛКА")
        print("="*60)
        
        db_path = input("\n📂 База получателей (.txt): ").strip()
        if not os.path.exists(db_path):
            print("❌ Файл не найден!")
            return
        
        print("\n✉️ Текст сообщения (Ctrl+D для завершения):")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        message = "\n".join(lines)
        
        if not message.strip():
            print("❌ Сообщение пустое!")
            return
        
        delay_min = int(input("\n⏱ Мин. задержка (сек): ") or "60")
        delay_max = int(input("⏱ Макс. задержка (сек): ") or "120")
        
        with open(db_path, 'r', encoding="utf-8") as f:
            usernames = [line.strip().replace("@", "") for line in f if line.strip()]
        
        print(f"\n🚀 Рассылка запущена ({len(usernames)} получателей)...")
        stats = {'success': 0, 'failed': 0}
        
        for i, username in enumerate(usernames):
            try:
                user = await self.client.get_entity(username)
                await self.client.send_message(user, message)
                stats['success'] += 1
                print(f"✅ @{username} ({stats['success']}/{i+1})")
            except FloodWaitError as e:
                print(f"⏳ FloodWait: {e.seconds} сек")
                stats['failed'] += 1
                await asyncio.sleep(e.seconds + 5)
            except Exception as e:
                stats['failed'] += 1
                print(f"❌ @{username}: {str(e)[:40]}")
            
            await asyncio.sleep(random.uniform(delay_min, delay_max))
        
        print(f"\n✅ Рассылка завершена!")
        print(f"   ✅ Успешно: {stats['success']}")
        print(f"   ❌ Ошибок: {stats['failed']}")
    
    async def warm(self):
        """6. ПРОГРЕВ"""
        print("\n" + "="*60)
        print("🔥 ПРОГРЕВ")
        print("="*60)
        
        print("\n📋 Каналы для активности (каждый с новой строки, Ctrl+D для завершения):")
        lines = []
        try:
            while True:
                line = input().strip().replace("@", "")
                if line:
                    lines.append(line)
        except EOFError:
            pass
        
        if not lines:
            print("❌ Нет каналов!")
            return
        
        print(f"\n🔥 Запуск прогрева для {len(lines)} каналов...")
        stats = {'subscribed': 0, 'liked': 0}
        
        for channel in lines:
            try:
                entity = await self.client.get_entity(channel)
                print(f"\n📊 {getattr(entity, 'title', channel)}")
                
                try:
                    await self.client.join_chat(channel)
                    stats['subscribed'] += 1
                    print("  ✅ Подписка")
                except:
                    print("  ⚠️ Уже подписан или ошибка")
                
                try:
                    async for msg in self.client.iter_messages(entity, limit=3):
                        await msg.react('👍')
                        stats['liked'] += 1
                        await asyncio.sleep(2)
                except:
                    print("  ⚠️ Лайки недоступны")
                
                await asyncio.sleep(random.uniform(5, 15))
            except Exception as e:
                print(f"  ❌ Ошибка: {str(e)[:40]}")
        
        print(f"\n✅ Прогрев завершён!")
        print(f"   ✅ Подписок: {stats['subscribed']}")
        print(f"   ❤️ Лайков: {stats['liked']}")
    
    async def autorespond(self):
        """7. АВТООТВЕТЧИК"""
        print("\n" + "="*60)
        print("🤖 АВТООТВЕТЧИК")
        print("="*60)
        
        print("\n💬 Текст автоответа (Ctrl+D для завершения):")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        message = "\n".join(lines)
        
        keywords = input("\n🔑 Ключевые слова (через запятую, или пусто для всех): ").strip()
        keyword_list = [k.strip().lower() for k in keywords.split(",")] if keywords else []
        
        chats = input("📋 Чаты для мониторинга (через запятую): ").strip()
        chat_list = [c.strip().replace("@", "") for c in chats.split(",")] if chats else None
        
        print(f"\n🤖 Автоответчик запущен...")
        print(f"   📋 Чаты: {', '.join(chat_list) if chat_list else 'Все'}")
        print(f"   🔑 Ключевые слова: {', '.join(keyword_list) if keyword_list else 'Все'}")
        print(f"   💬 Ответ: {message[:50]}...")
        print(f"\n💡 Нажмите Ctrl+C для остановки\n")
        
        @self.client.on(events.NewMessage(chats=chat_list))
        async def handler(event):
            if event.sender_id == (await self.client.get_me()).id:
                return
            
            text = event.message.text.lower()
            
            if keyword_list and not any(kw in text for kw in keyword_list):
                return
            
            await event.respond(message)
            print(f"💬 Ответ пользователю {event.sender_id}")
        
        try:
            await self.client.run_until_disconnected()
        except KeyboardInterrupt:
            print("\n🛑 Автоответчик остановлен")
    
    async def collect_contacts(self):
        """8. СБОР КОНТАКТОВ"""
        print("\n" + "="*60)
        print("📞 СБОР КОНТАКТОВ")
        print("="*60)
        
        chat = input("\n📋 Чат для сбора: ").strip().replace("@", "")
        print(f"\n🔍 Сбор контактов из @{chat}...")
        
        contacts = []
        async for user in self.client.iter_participants(chat):
            phone = getattr(user, 'phone', None)
            if phone:
                contacts.append({
                    'phone': phone,
                    'username': user.username,
                    'name': f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
                })
                print(f"  📱 {phone} - @{user.username or 'N/A'}")
        
        if contacts:
            filepath = f"parsed_data/contacts_{chat}.csv"
            os.makedirs("parsed_data", exist_ok=True)
            with open(filepath, 'w', newline='', encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=['phone', 'username', 'name'])
                writer.writeheader()
                writer.writerows(contacts)
            
            print(f"\n✅ Найдено {len(contacts)} контактов")
            print(f"💾 Сохранено в: {filepath}")
        else:
            print("❌ Контакты не найдены")
    
    async def show_stats(self):
        """9. СТАТИСТИКА АККАУНТА"""
        print("\n" + "="*60)
        print("📊 СТАТИСТИКА")
        print("="*60)
        
        me = await self.client.get_me()
        print(f"\n👤 Аккаунт: {me.first_name} {me.last_name or ''}")
        print(f"   Username: @{me.username or 'N/A'}")
        print(f"   ID: {me.id}")
        print(f"   Premium: {getattr(me, 'premium', False)}")
        print(f"   Бот: {me.bot}")
        print(f"   Verified: {me.verified}")
        
        dialogs_count = 0
        async for _ in self.client.iter_dialogs():
            dialogs_count += 1
        
        print(f"\n📋 Диалогов: {dialogs_count}")
        print(f"📁 Папка parsed_data: {len(os.listdir('parsed_data')) if os.path.exists('parsed_data') else 0} файлов")
    
    async def show_menu(self):
        """Показать меню"""
        print("\n" + "="*60)
        print("⚡ TELEGRAM TOOLS")
        print("="*60)
        print("\n📱 Функции:")
        print("  1. 🔍 Парсинг участников")
        print("  2. 📢 Поиск чатов")
        print("  3. 👥 Инвайтер")
        print("  4. 🔗 Вход по ссылке")
        print("  5. 📨 Рассылка")
        print("  6. 🔥 Прогрев")
        print("  7. 🤖 Автоответчик")
        print("  8. 📞 Сбор контактов")
        print("  9. 📊 Статистика")
        print("  0. 🚪 Выход")

async def main():
    tools = TelegramTools()
    await tools.connect()
    
    while True:
        await tools.show_menu()
        choice = input("\nВыберите функцию (0-9): ").strip()
        
        functions = {
            "1": tools.parse_users,
            "2": tools.search_chats,
            "3": tools.invite_users,
            "4": tools.join_by_link,
            "5": tools.spam,
            "6": tools.warm,
            "7": tools.autorespond,
            "8": tools.collect_contacts,
            "9": tools.show_stats,
            "0": None
        }
        
        if choice == "0":
            print("\n👋 До свидания!")
            break
        
        func = functions.get(choice)
        if func:
            try:
                await func()
            except Exception as e:
                print(f"\n❌ Ошибка: {e}")
            
            input("\nНажмите Enter для продолжения...")
        else:
            print("❌ Неверный выбор!")
    
    await tools.disconnect()

asyncio.run(main())
