#!/usr/bin/env python3
"""
Простая демонстрация чат-системы AGI Layer v3.9
Работает без внешних зависимостей для тестирования
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List
import random


class SimpleChatCoordinator:
    """Упрощенный координатор чата для демонстрации"""
    
    def __init__(self):
        self.chat_sessions: Dict[int, Dict[str, Any]] = {}
        self.demo_mode = True
        
    async def get_chat_session(self, chat_id: int) -> Dict[str, Any]:
        """Получение или создание сессии чата"""
        if chat_id not in self.chat_sessions:
            self.chat_sessions[chat_id] = {
                'history': [],
                'mode': 'chat',
                'context': {},
                'created_at': datetime.now(),
                'message_count': 0,
                'preferences': {
                    'language': 'ru',
                    'response_style': 'detailed',
                    'max_history': 20
                }
            }
        return self.chat_sessions[chat_id]
    
    async def process_text_message(self, chat_id: int, message: str, user_name: str = "Пользователь") -> str:
        """Обработка текстового сообщения"""
        session = await self.get_chat_session(chat_id)
        
        # Добавляем сообщение в историю
        session['history'].append({
            'role': 'user',
            'content': message,
            'user_name': user_name,
            'timestamp': datetime.now().isoformat()
        })
        session['message_count'] += 1
        
        # Генерация ответа
        response = await self._generate_smart_response(session, message)
        
        # Добавляем ответ в историю
        session['history'].append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Ограничиваем историю
        max_history = session['preferences']['max_history']
        if len(session['history']) > max_history:
            session['history'] = session['history'][-max_history:]
        
        return response
    
    async def _generate_smart_response(self, session: Dict[str, Any], message: str) -> str:
        """Генерация умного ответа"""
        message_lower = message.lower()
        
        # Приветствия
        if any(word in message_lower for word in ['привет', 'здравствуй', 'добро пожаловать', 'хай']):
            responses = [
                "Привет! Я AGI Layer v3.9 - ваш персональный ИИ-ассистент. Готов помочь с любыми вопросами! 🤖",
                "Здравствуйте! Рад нашему знакомству. Чем могу быть полезен?",
                "Привет! Отличное настроение для продуктивного общения. О чем поговорим?"
            ]
            return random.choice(responses)
        
        # Вопросы о возможностях
        elif any(keyword in message_lower for keyword in ['что ты умеешь', 'возможности', 'функции', 'что можешь']):
            return """🤖 **Мои возможности в AGI Layer v3.9:**

🧠 **Интеллектуальный диалог**
• Отвечаю на вопросы по любым темам
• Поддерживаю естественную беседу
• Помогаю с анализом и решением задач

🎨 **Творческие задачи**
• Генерация изображений по описанию (Stable Diffusion)
• Анализ и описание фотографий (BLIP2)
• Помощь с творческими проектами

📚 **Обучение и работа**
• Объяснение сложных концепций
• Помощь с программированием
• Анализ текстов и документов

💡 **Практические задачи**
• Планирование и организация
• Поиск решений проблем
• Консультации по различным вопросам

Просто пишите, что нужно сделать - я подберу лучший способ помочь!"""
        
        # Технические вопросы
        elif any(keyword in message_lower for keyword in ['программирование', 'код', 'python', 'разработка', 'алгоритм']):
            return """💻 **Программирование - моя сильная сторона!**

Могу помочь с:
• **Python, JavaScript, C++** - синтаксис, best practices
• **Алгоритмами** - объяснение, оптимизация, реализация
• **Архитектурой** - проектирование систем и приложений
• **Отладкой** - поиск и исправление ошибок
• **Machine Learning** - модели, обучение, анализ данных
• **Web разработкой** - фронтенд и бэкенд

В AGI Layer используются:
🧠 Phi-2 для генерации кода
🎨 Stable Diffusion для UI/UX макетов
👁️ BLIP2 для анализа диаграмм

Какая конкретно область вас интересует?"""
        
        # Научные вопросы
        elif any(keyword in message_lower for keyword in ['космос', 'физика', 'химия', 'биология', 'математика', 'наука']):
            return """🔬 **Наука - увлекательная область знаний!**

Готов обсудить:
• **Физику** - от квантовой механики до астрофизики
• **Математику** - алгебру, геометрию, статистику, ML
• **Биологию** - от молекулярного уровня до экосистем
• **Химию** - реакции, соединения, новые материалы
• **Космос** - планеты, звезды, галактики, черные дыры
• **ИИ и нейронауки** - как работает мозг и нейросети

Интересный факт: AGI Layer использует принципы нейронных сетей, 
похожие на работу человеческого мозга!

О какой области науки хотели бы узнать больше? 🌟"""
        
        # Творческие запросы
        elif any(keyword in message_lower for keyword in ['создай', 'придумай', 'напиши', 'сочини', 'творчество', 'идея']):
            return """🎨 **Творчество - это здорово!**

Могу помочь с:
• **Генерацией идей** - для проектов, бизнеса, творчества
• **Написанием текстов** - статьи, рассказы, сценарии
• **Созданием концепций** - продуктов, дизайна, решений
• **Мозговым штурмом** - поиск нестандартных подходов

🎨 **В полной версии AGI Layer:**
• Stable Diffusion создаст изображения по вашему описанию
• BLIP2 проанализирует референсы
• Phi-2 поможет с текстами и сценариями

Расскажите подробнее, что хотите создать! ✨"""
        
        # Помощь
        elif any(keyword in message_lower for keyword in ['помоги', 'помощь', 'не знаю', 'как сделать', 'проблема']):
            return """🤝 **Конечно помогу!**

Чтобы дать наилучший совет, расскажите:
• **Какая задача** стоит перед вами?
• **В какой области** нужна помощь?
• **Что уже пробовали** делать?
• **Какой результат** хотите получить?

🎯 **Области помощи AGI Layer:**
📚 Учеба и образование
💼 Рабочие задачи  
💡 Решение проблем
🎯 Планирование и цели
🛠️ Технические вопросы
🎨 Творческие проекты

Чем подробнее опишете ситуацию, тем точнее будет моя помощь!"""
        
        # Вопросы о системе
        elif any(keyword in message_lower for keyword in ['agi layer', 'система', 'как работаешь', 'архитектура']):
            return f"""🤖 **AGI Layer v3.9 - Архитектура системы**

🧠 **Нейросетевые модели:**
• **Phi-2** (Microsoft) - текстовая модель, 2.7B параметров
• **Stable Diffusion 1.5** - генерация изображений  
• **BLIP2** (Salesforce) - анализ изображений

⚙️ **Компоненты системы:**
• **ChatCoordinator** - управление диалогами
• **MetaAgent** - координация всех агентов
• **TelegramAgent** - интерфейс с пользователем
• **ImageAgent, TextAgent, VisionAgent** - специализированные модули

📊 **Текущий статус:**
• Активных чатов: {len(self.chat_sessions)}
• Режим: Демо (полный режим через Docker)
• Время работы: {datetime.now().strftime('%H:%M:%S')}

🚀 **Особенности:**
• CPU-оптимизированные модели
• Асинхронная обработка
• Модульная архитектура
• Контекстная память"""
        
        # Общие вопросы
        else:
            # Анализируем контекст из истории
            context_topics = []
            if len(session['history']) > 2:
                for msg in session['history'][-5:]:
                    if msg['role'] == 'user':
                        context_topics.append(msg['content'])
            
            # Генерируем контекстуальный ответ
            if 'технология' in message_lower or 'компьютер' in message_lower:
                base_response = f"Интересный технический вопрос! {message[:100]}{'...' if len(message) > 100 else ''}"
                base_response += "\n\n💻 Если нужны детали по программированию или технологиям - готов углубиться!"
                
            elif 'творчество' in message_lower or 'искусство' in message_lower:
                base_response = f"Творческая тема! {message[:100]}{'...' if len(message) > 100 else ''}"
                base_response += "\n\n🎨 Для творческих задач могу предложить множество интересных решений!"
                
            elif '?' in message:
                base_response = f"Хороший вопрос! Позвольте подумать над этим."
                base_response += f"\n\n{message[:150]}{'...' if len(message) > 150 else ''} - это действительно важная тема."
                base_response += "\n\n❓ Если нужны дополнительные разъяснения, спрашивайте!"
                
            else:
                responses = [
                    f"Понимаю вашу мысль. {message[:100]}{'...' if len(message) > 100 else ''} - интересная тема для обсуждения.",
                    f"Спасибо за сообщение! Я анализирую информацию и готов поделиться мыслями.",
                    f"Отличная тема! Давайте разберем это подробнее с разных сторон.",
                    f"Интересное наблюдение! Могу предложить несколько вариантов развития этой идеи."
                ]
                base_response = random.choice(responses)
            
            return base_response
    
    async def get_status(self) -> Dict[str, Any]:
        """Получение статуса системы"""
        return {
            "demo_mode": self.demo_mode,
            "active_chats": len(self.chat_sessions),
            "agents": {
                "text_agent": False,
                "vision_agent": False, 
                "image_agent": False
            },
            "timestamp": datetime.now().isoformat()
        }


async def simulate_chat_session():
    """Симуляция чат-сессии для демонстрации"""
    coordinator = SimpleChatCoordinator()
    chat_id = 12345
    user_name = "Тестовый пользователь"
    
    print("🤖 AGI Layer v3.9 - Демонстрация чат-системы")
    print("=" * 50)
    print()
    
    # Тестовые сообщения
    test_messages = [
        "Привет!",
        "Что ты умеешь?", 
        "Расскажи про программирование на Python",
        "Как создать нейросеть?",
        "Помоги с творческим проектом",
        "Что такое AGI Layer?"
    ]
    
    for i, message in enumerate(test_messages):
        print(f"👤 Пользователь: {message}")
        print()
        
        # Обработка сообщения
        response = await coordinator.process_text_message(chat_id, message, user_name)
        
        print(f"🤖 AGI Bot: {response}")
        print()
        print("-" * 50)
        print()
        
        # Пауза для читаемости
        await asyncio.sleep(0.5)
    
    # Показ статуса
    status = await coordinator.get_status()
    print("📊 Статус системы:")
    print(json.dumps(status, indent=2, ensure_ascii=False, default=str))
    print()
    print("✅ Демонстрация завершена!")


async def interactive_chat():
    """Интерактивный чат для тестирования"""
    coordinator = SimpleChatCoordinator()
    chat_id = 12345
    
    print("🤖 AGI Layer v3.9 - Интерактивный чат")
    print("=" * 50)
    print("Введите 'quit' для выхода")
    print()
    
    while True:
        try:
            user_input = input("👤 Вы: ").strip()
            
            if user_input.lower() in ['quit', 'выход', 'exit']:
                break
                
            if user_input:
                response = await coordinator.process_text_message(chat_id, user_input)
                print(f"🤖 AGI Bot: {response}")
                print()
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    print("👋 До свидания!")


async def main():
    """Главная функция"""
    print("Выберите режим:")
    print("1. Демонстрация (автоматические сообщения)")
    print("2. Интерактивный чат")
    print()
    
    try:
        choice = input("Введите номер (1 или 2): ").strip()
        print()
        
        if choice == "1":
            await simulate_chat_session()
        elif choice == "2":
            await interactive_chat()
        else:
            print("Запуск демонстрации по умолчанию...")
            await simulate_chat_session()
            
    except KeyboardInterrupt:
        print("\n👋 Программа завершена")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main())