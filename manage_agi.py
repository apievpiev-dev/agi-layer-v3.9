#!/usr/bin/env python3
"""
Управление системой AGI Layer v3.9
"""

import os
import sys
import subprocess
import time
from datetime import datetime

def run_command(cmd):
    """Выполнение команды"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_bot_status():
    """Проверка статуса бота"""
    success, stdout, stderr = run_command("ps aux | grep advanced_telegram_bot | grep -v grep")
    if success and stdout.strip():
        print("🟢 Telegram бот работает")
        for line in stdout.strip().split('\n'):
            if 'python' in line:
                parts = line.split()
                pid = parts[1]
                print(f"   PID: {pid}")
        return True
    else:
        print("🔴 Telegram бот не запущен")
        return False

def start_bot():
    """Запуск бота"""
    print("🚀 Запуск Telegram бота...")
    
    # Активация виртуального окружения и запуск
    cmd = "source venv/bin/activate && nohup python advanced_telegram_bot.py > telegram_bot.log 2>&1 &"
    success, stdout, stderr = run_command(cmd)
    
    if success:
        time.sleep(3)  # Ждем запуска
        if check_bot_status():
            print("✅ Бот успешно запущен")
        else:
            print("❌ Ошибка запуска бота")
            show_logs()
    else:
        print(f"❌ Ошибка команды запуска: {stderr}")

def stop_bot():
    """Остановка бота"""
    print("⏹️ Остановка Telegram бота...")
    success, stdout, stderr = run_command("pkill -f advanced_telegram_bot.py")
    
    time.sleep(2)
    if not check_bot_status():
        print("✅ Бот остановлен")
    else:
        print("❌ Не удалось остановить бота")

def restart_bot():
    """Перезапуск бота"""
    print("🔄 Перезапуск Telegram бота...")
    stop_bot()
    time.sleep(2)
    start_bot()

def show_logs():
    """Показать логи"""
    print("📋 Последние логи:")
    success, stdout, stderr = run_command("tail -20 telegram_bot.log")
    if success:
        print(stdout)
    else:
        print("❌ Не удалось прочитать логи")

def test_system():
    """Тестирование системы"""
    print("🧪 Запуск тестирования системы...")
    success, stdout, stderr = run_command("source venv/bin/activate && python test_telegram_system.py")
    if success:
        print(stdout)
    else:
        print(f"❌ Ошибка тестирования: {stderr}")

def show_system_info():
    """Информация о системе"""
    print("📊 Информация о системе AGI Layer v3.9")
    print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Статус бота
    check_bot_status()
    print()
    
    # Проверка файлов
    files_to_check = [
        '.env',
        'advanced_telegram_bot.py', 
        'telegram_bot.log',
        'models_status.txt'
    ]
    
    print("📁 Файлы системы:")
    for file in files_to_check:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"   ✅ {file} ({size} байт)")
        else:
            print(f"   ❌ {file} (отсутствует)")
    
    print()
    
    # Папки
    dirs_to_check = ['models', 'output/images', 'logs', 'venv']
    print("📂 Директории:")
    for dir in dirs_to_check:
        if os.path.exists(dir):
            print(f"   ✅ {dir}/")
        else:
            print(f"   ❌ {dir}/ (отсутствует)")

def main_menu():
    """Главное меню"""
    while True:
        print("\n" + "="*50)
        print("🤖 AGI Layer v3.9 - Управление системой")
        print("="*50)
        print("1. 📊 Статус системы")
        print("2. 🚀 Запустить бота")
        print("3. ⏹️  Остановить бота") 
        print("4. 🔄 Перезапустить бота")
        print("5. 📋 Показать логи")
        print("6. 🧪 Тестировать систему")
        print("7. ❌ Выход")
        print()
        
        try:
            choice = input("Выберите действие (1-7): ").strip()
            
            if choice == '1':
                show_system_info()
            elif choice == '2':
                start_bot()
            elif choice == '3':
                stop_bot()
            elif choice == '4':
                restart_bot()
            elif choice == '5':
                show_logs()
            elif choice == '6':
                test_system()
            elif choice == '7':
                print("👋 До свидания!")
                break
            else:
                print("❌ Неверный выбор. Попробуйте снова.")
                
        except KeyboardInterrupt:
            print("\n👋 До свидания!")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")

def main():
    """Основная функция"""
    if len(sys.argv) > 1:
        # Командная строка
        cmd = sys.argv[1].lower()
        
        if cmd == 'status':
            show_system_info()
        elif cmd == 'start':
            start_bot()
        elif cmd == 'stop':
            stop_bot()
        elif cmd == 'restart':
            restart_bot()
        elif cmd == 'logs':
            show_logs()
        elif cmd == 'test':
            test_system()
        else:
            print("❌ Неизвестная команда")
            print("Доступные команды: status, start, stop, restart, logs, test")
    else:
        # Интерактивное меню
        main_menu()

if __name__ == "__main__":
    main()