#!/usr/bin/env python3
"""
AGI Layer v3.9 - Быстрый запуск
==============================

Простой скрипт для тестирования всех возможностей системы
"""

import subprocess
import time

def test_models():
    """Быстрое тестирование всех моделей"""
    print("🚀 AGI Layer v3.9 - Быстрый тест")
    print("=" * 40)
    
    tests = [
        {
            "name": "💬 Llama 3.2 (быстрая)",
            "command": ["ollama", "run", "llama3.2:3b", "Привет! Как дела?"],
            "timeout": 10
        },
        {
            "name": "🔧 Qwen 2.5 (программирование)",
            "command": ["ollama", "run", "qwen2.5:7b", "def hello(): # допиши функцию"],
            "timeout": 15
        },
        {
            "name": "💻 CodeLlama (код)",
            "command": ["ollama", "run", "codellama:7b", "// Создай функцию на JavaScript"],
            "timeout": 15
        },
        {
            "name": "🧠 Phi-3 (Microsoft)",
            "command": ["ollama", "run", "phi3:3.8b", "Объясни искусственный интеллект"],
            "timeout": 20
        }
    ]
    
    for test in tests:
        print(f"\n{test['name']}:")
        print("-" * 30)
        
        try:
            start_time = time.time()
            result = subprocess.run(
                test["command"],
                capture_output=True,
                text=True,
                timeout=test["timeout"]
            )
            duration = time.time() - start_time
            
            if result.returncode == 0:
                response = result.stdout.strip()
                print(f"✅ Ответ ({duration:.1f}с): {response[:150]}...")
            else:
                print(f"❌ Ошибка: {result.stderr.strip()}")
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout ({test['timeout']}с) - модель медленная на CPU")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    print("\n" + "=" * 40)
    print("✅ Тестирование завершено!")
    print("\n🌐 Доступ к системе:")
    print("• Web UI: http://ваш-IP:8501")
    print("• API: http://ваш-IP:8080/docs") 
    print("• Чат: ollama run llama3.2:3b 'ваш вопрос'")


if __name__ == "__main__":
    test_models()




