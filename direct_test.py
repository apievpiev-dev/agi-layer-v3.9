#!/usr/bin/env python3
"""
Прямой тест генерации изображения
"""

import asyncio
import os
import sys
from pathlib import Path

# Добавляем путь
sys.path.append(str(Path(__file__).parent))

async def test_image_generation():
    """Тест генерации изображения"""
    try:
        print("🎨 Тест генерации изображения...")
        
        from intelligent_telegram_bot import IntelligentAGI
        
        # Создаем экземпляр
        agi = IntelligentAGI()
        
        # Инициализируем модели
        print("📥 Инициализация моделей...")
        await agi.initialize_ai_models()
        
        if agi.models_ready:
            print("✅ Модели готовы!")
            
            # Тест генерации
            print("🖼️ Генерируем изображение...")
            image_path = await agi._generate_real_image("красивый закат над океаном")
            
            if image_path and os.path.exists(image_path):
                print(f"✅ Изображение создано: {image_path}")
                
                # Проверяем размер файла
                size = os.path.getsize(image_path)
                print(f"📊 Размер файла: {size} байт")
                
                return True
            else:
                print("❌ Изображение не создано")
                return False
        else:
            print("❌ Модели не готовы")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def test_text_generation():
    """Тест генерации текста"""
    try:
        print("\n💬 Тест генерации текста...")
        
        from intelligent_telegram_bot import IntelligentAGI
        
        agi = IntelligentAGI()
        await agi.initialize_ai_models()
        
        if agi.models_ready:
            response = await agi.generate_intelligent_response("Привет! Как дела?")
            print(f"🤖 Ответ ИИ: {response}")
            return True
        else:
            print("❌ Модели не готовы")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def main():
    """Основная функция"""
    print("🧪 Прямое тестирование ИИ функций\n")
    
    # Тест текста
    text_ok = await test_text_generation()
    
    # Тест изображений  
    image_ok = await test_image_generation()
    
    print(f"\n📊 Результаты:")
    print(f"Генерация текста: {'✅' if text_ok else '❌'}")
    print(f"Генерация изображений: {'✅' if image_ok else '❌'}")
    
    if text_ok and image_ok:
        print("\n🎉 Все функции работают!")
    else:
        print("\n⚠️ Есть проблемы с некоторыми функциями")

if __name__ == "__main__":
    asyncio.run(main())