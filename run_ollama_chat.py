#!/usr/bin/env python3
"""
Запуск веб-чата с Ollama через Streamlit
"""

import subprocess
import sys
import os


def main():
    """Запуск веб-чата"""
    print("🤖 Запуск веб-чата с Ollama...")
    
    # Проверка наличия streamlit
    try:
        import streamlit
        print("✅ Streamlit установлен")
    except ImportError:
        print("❌ Streamlit не установлен")
        print("💡 Установите: pip install streamlit")
        return 1
    
    # Проверка наличия aiohttp
    try:
        import aiohttp
        print("✅ aiohttp установлен")
    except ImportError:
        print("❌ aiohttp не установлен")
        print("💡 Установите: pip install aiohttp")
        return 1
    
    # Запуск streamlit
    script_path = os.path.join(os.path.dirname(__file__), "start_ollama_chat.py")
    
    cmd = [
        sys.executable, "-m", "streamlit", "run", 
        script_path,
        "--server.port=8501",
        "--server.address=0.0.0.0",
        "--server.headless=true"
    ]
    
    print("🚀 Запуск веб-сервера...")
    print("🌐 Веб-чат будет доступен по адресу: http://localhost:8501")
    print("⏹️ Для остановки нажмите Ctrl+C")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Завершение работы...")
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка запуска: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())