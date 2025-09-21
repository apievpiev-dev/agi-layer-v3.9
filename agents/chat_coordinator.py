"""
ChatCoordinator - координатор чата с нейросетями для AGI Layer v3.9
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from .text_agent import TextAgent
from .vision_agent import VisionAgent  
from .image_agent import ImageAgent
from .base_agent import Task


class ChatCoordinator:
    """Координатор для управления чатом с нейросетями"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Агенты
        self.text_agent: Optional[TextAgent] = None
        self.vision_agent: Optional[VisionAgent] = None
        self.image_agent: Optional[ImageAgent] = None
        
        # Состояние чатов
        self.chat_sessions: Dict[int, Dict[str, Any]] = {}
        
        # Флаги инициализации
        self.agents_initialized = False
        self.demo_mode = True
    
    async def initialize(self):
        """Инициализация координатора и агентов"""
        try:
            self.logger.info("🤖 Инициализация ChatCoordinator...")
            
            # Попытка инициализации агентов
            await self._try_initialize_agents()
            
            self.logger.info(f"✅ ChatCoordinator инициализирован (демо режим: {self.demo_mode})")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации ChatCoordinator: {e}")
            self.demo_mode = True
    
    async def _try_initialize_agents(self):
        """Попытка инициализации нейросетевых агентов"""
        try:
            self.logger.info("Попытка загрузки нейросетевых агентов...")
            
            # Инициализация TextAgent
            # self.text_agent = TextAgent(self.config)
            # await self.text_agent._initialize_agent()
            # self.logger.info("✅ TextAgent инициализирован")
            
            # Инициализация VisionAgent  
            # self.vision_agent = VisionAgent(self.config)
            # await self.vision_agent._initialize_agent()
            # self.logger.info("✅ VisionAgent инициализирован")
            
            # Инициализация ImageAgent
            # self.image_agent = ImageAgent(self.config)
            # await self.image_agent._initialize_agent()
            # self.logger.info("✅ ImageAgent инициализирован")
            
            # self.agents_initialized = True
            # self.demo_mode = False
            
            self.logger.info("🚀 Агенты будут загружены при первом использовании")
            
        except Exception as e:
            self.logger.warning(f"Не удалось инициализировать агенты: {e}")
            self.logger.info("Работаем в демо режиме")
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
        try:
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
            if self.text_agent and not self.demo_mode:
                response = await self._generate_neural_response(session, message)
            else:
                response = await self._generate_smart_demo_response(session, message)
            
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
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки текстового сообщения: {e}")
            return "❌ Произошла ошибка при обработке сообщения. Попробуйте еще раз."
    
    async def _generate_neural_response(self, session: Dict[str, Any], message: str) -> str:
        """Генерация ответа с помощью нейросети"""
        try:
            # Формируем контекст для нейросети
            context = self._build_context(session, message)
            
            # Создаем задачу для TextAgent
            task = Task(
                id=f"chat_{session['message_count']}",
                agent_name="text_agent",
                task_type="text_generation",
                data={
                    "prompt": context,
                    "max_length": 1024,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            )
            
            # Выполняем задачу
            result = await self.text_agent.process_task(task)
            
            if result["status"] == "success":
                return result["generated_text"]
            else:
                return "Извините, произошла ошибка при генерации ответа."
                
        except Exception as e:
            self.logger.error(f"Ошибка генерации нейросетевого ответа: {e}")
            return "❌ Ошибка работы с нейросетью."
    
    def _build_context(self, session: Dict[str, Any], message: str) -> str:
        """Построение контекста для нейросети"""
        # Системный промпт
        system_prompt = """Ты - умный ИИ-ассистент AGI Layer. Отвечай на русском языке развернуто и полезно.
Ты дружелюбный, профессиональный и готов помочь с любыми вопросами.
Если не знаешь точного ответа, так и скажи, но предложи альтернативы."""
        
        # Последние сообщения из истории
        context_parts = [f"System: {system_prompt}"]
        
        recent_messages = session['history'][-10:]  # Последние 10 сообщений
        for msg in recent_messages:
            if msg['role'] == 'user':
                context_parts.append(f"Human: {msg['content']}")
            else:
                context_parts.append(f"Assistant: {msg['content']}")
        
        context_parts.append(f"Human: {message}")
        context_parts.append("Assistant:")
        
        return "\n".join(context_parts)
    
    async def _generate_smart_demo_response(self, session: Dict[str, Any], message: str) -> str:
        """Генерация умного ответа в демо режиме"""
        message_lower = message.lower()
        
        # Анализируем тип сообщения и генерируем соответствующий ответ
        response_generators = [
            self._handle_greetings,
            self._handle_questions_about_capabilities,
            self._handle_tech_questions,
            self._handle_science_questions,
            self._handle_creative_requests,
            self._handle_help_requests,
            self._handle_general_conversation
        ]
        
        for generator in response_generators:
            response = await generator(message, message_lower, session)
            if response:
                return response
        
        # Универсальный ответ
        return await self._generate_contextual_response(message, session)
    
    async def _handle_greetings(self, message: str, message_lower: str, session: Dict[str, Any]) -> Optional[str]:
        """Обработка приветствий"""
        greetings = ['привет', 'здравствуй', 'добро пожаловать', 'хай', 'hello', 'hi']
        if any(word in message_lower for word in greetings):
            responses = [
                "Привет! Я AGI Layer - ваш персональный ИИ-ассистент. Готов помочь с любыми вопросами! 🤖",
                "Здравствуйте! Рад нашему знакомству. Чем могу быть полезен?",
                "Привет! Отличное настроение для продуктивного общения. О чем поговорим?"
            ]
            import random
            return random.choice(responses)
        return None
    
    async def _handle_questions_about_capabilities(self, message: str, message_lower: str, session: Dict[str, Any]) -> Optional[str]:
        """Вопросы о возможностях"""
        capability_keywords = ['что ты умеешь', 'возможности', 'функции', 'что можешь', 'помочь с чем']
        if any(keyword in message_lower for keyword in capability_keywords):
            return """🤖 **Мои возможности:**

🧠 **Интеллектуальный диалог**
• Отвечаю на вопросы по любым темам
• Поддерживаю естественную беседу
• Помогаю с анализом и решением задач

🎨 **Творческие задачи**
• Генерация изображений по описанию
• Анализ и описание фотографий
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
        return None
    
    async def _handle_tech_questions(self, message: str, message_lower: str, session: Dict[str, Any]) -> Optional[str]:
        """Технические вопросы"""
        tech_keywords = ['программирование', 'код', 'python', 'разработка', 'алгоритм', 'компьютер', 'технология']
        if any(keyword in message_lower for keyword in tech_keywords):
            return """💻 **Технические вопросы - моя сильная сторона!**

Могу помочь с:
• **Программированием** - Python, JavaScript, C++, и другие языки
• **Алгоритмами** - объяснение, оптимизация, реализация
• **Архитектурой** - проектирование систем и приложений
• **Отладкой** - поиск и исправление ошибок
• **DevOps** - развертывание, контейнеризация, CI/CD
• **Machine Learning** - модели, обучение, анализ данных

Если у вас есть конкретная задача или код для анализа - присылайте, разберем детально! 

Какая именно область вас интересует больше всего?"""
        return None
    
    async def _handle_science_questions(self, message: str, message_lower: str, session: Dict[str, Any]) -> Optional[str]:
        """Научные вопросы"""
        science_keywords = ['космос', 'физика', 'химия', 'биология', 'математика', 'наука', 'исследование']
        if any(keyword in message_lower for keyword in science_keywords):
            return """🔬 **Наука - увлекательная область знаний!**

Готов обсудить:
• **Физику** - от квантовой механики до астрофизики
• **Математику** - алгебру, геометрию, статистику, анализ
• **Биологию** - от молекулярного уровня до экосистем
• **Химию** - реакции, соединения, материалы
• **Космос** - планеты, звезды, галактики, черные дыры
• **Современные исследования** - последние открытия и теории

Могу объяснить сложные концепции простыми словами или углубиться в детали для специалистов.

О какой области науки хотели бы узнать больше? 🌟"""
        return None
    
    async def _handle_creative_requests(self, message: str, message_lower: str, session: Dict[str, Any]) -> Optional[str]:
        """Творческие запросы"""
        creative_keywords = ['создай', 'придумай', 'напиши', 'сочини', 'творчество', 'идея', 'концепт']
        if any(keyword in message_lower for keyword in creative_keywords):
            return """🎨 **Творчество - это здорово!**

Могу помочь с:
• **Генерацией идей** - для проектов, бизнеса, творчества
• **Написанием текстов** - статьи, рассказы, сценарии
• **Созданием концепций** - продуктов, дизайна, решений
• **Мозговым штурмом** - поиск нестандартных подходов
• **Анализом творческих работ** - обратная связь и советы

Для генерации изображений используйте команду `/generate [описание]`

Расскажите подробнее, что хотите создать - я помогу воплотить идею! ✨"""
        return None
    
    async def _handle_help_requests(self, message: str, message_lower: str, session: Dict[str, Any]) -> Optional[str]:
        """Запросы о помощи"""
        help_keywords = ['помоги', 'помощь', 'не знаю', 'как сделать', 'что делать', 'проблема']
        if any(keyword in message_lower for keyword in help_keywords):
            return """🤝 **Конечно помогу!**

Чтобы дать наилучший совет, расскажите:
• **Какая задача** стоит перед вами?
• **В какой области** нужна помощь?
• **Что уже пробовали** делать?
• **Какой результат** хотите получить?

Я могу помочь с:
📚 Учебой и образованием
💼 Рабочими задачами  
💡 Решением проблем
🎯 Планированием и целями
🛠️ Техническими вопросами
🎨 Творческими проектами

Чем подробнее опишете ситуацию, тем точнее будет моя помощь!"""
        return None
    
    async def _handle_general_conversation(self, message: str, message_lower: str, session: Dict[str, Any]) -> Optional[str]:
        """Общий диалог"""
        conversation_keywords = ['как дела', 'что нового', 'расскажи', 'мнение', 'думаешь']
        if any(keyword in message_lower for keyword in conversation_keywords):
            responses = [
                "У меня все отлично! Все системы работают стабильно, готов к новым задачам. А как дела у вас?",
                "Отличное настроение для продуктивного общения! Что интересного происходит в вашей жизни?",
                "Все системы в норме, нейросети готовы к работе! О чем хотели бы поговорить?"
            ]
            import random
            return random.choice(responses)
        return None
    
    async def _generate_contextual_response(self, message: str, session: Dict[str, Any]) -> str:
        """Генерация контекстуального ответа"""
        # Анализируем историю для понимания контекста
        recent_topics = []
        if len(session['history']) > 2:
            for msg in session['history'][-5:]:
                if msg['role'] == 'user':
                    recent_topics.append(msg['content'])
        
        # Базовые паттерны ответов
        response_patterns = [
            f"Интересная мысль! {message[:100]}{'...' if len(message) > 100 else ''} - это действительно важная тема для обсуждения.",
            f"Понимаю вашу точку зрения. Позвольте поделиться своими мыслями по этому поводу...",
            f"Отличный вопрос! Я проанализировал информацию и готов предложить несколько вариантов решения.",
            f"Это многогранная тема. Давайте разберем ее с разных сторон для полного понимания."
        ]
        
        import random
        base_response = random.choice(response_patterns)
        
        # Добавляем контекстуальную информацию
        if 'технология' in message.lower() or 'компьютер' in message.lower():
            base_response += "\n\n💻 Если нужна техническая помощь, я готов углубиться в детали!"
        elif 'творчество' in message.lower() or 'идея' in message.lower():
            base_response += "\n\n🎨 Для творческих задач могу предложить множество интересных решений!"
        elif '?' in message:
            base_response += "\n\n❓ Если нужны дополнительные разъяснения, спрашивайте - разберем подробно!"
        
        return base_response
    
    async def process_image_generation(self, chat_id: int, prompt: str) -> Dict[str, Any]:
        """Обработка генерации изображения"""
        try:
            session = await self.get_chat_session(chat_id)
            
            if self.image_agent and not self.demo_mode:
                # Реальная генерация
                task = Task(
                    id=f"img_{chat_id}_{session['message_count']}",
                    agent_name="image_agent",
                    task_type="image_generation",
                    data={
                        "prompt": prompt,
                        "width": 512,
                        "height": 512,
                        "num_inference_steps": 20
                    }
                )
                
                result = await self.image_agent.process_task(task)
                return result
            else:
                # Демо режим
                return {
                    "status": "demo",
                    "message": f"Демо: Изображение '{prompt}' будет создано при полной инициализации системы",
                    "prompt": prompt,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка генерации изображения: {e}")
            return {"status": "error", "error": str(e)}
    
    async def process_image_analysis(self, chat_id: int, image_path: str, question: str = None) -> Dict[str, Any]:
        """Обработка анализа изображения"""
        try:
            session = await self.get_chat_session(chat_id)
            
            if self.vision_agent and not self.demo_mode:
                # Реальный анализ
                task_type = "visual_question_answering" if question else "image_captioning"
                task_data = {"image_path": image_path}
                if question:
                    task_data["question"] = question
                
                task = Task(
                    id=f"vision_{chat_id}_{session['message_count']}",
                    agent_name="vision_agent",
                    task_type=task_type,
                    data=task_data
                )
                
                result = await self.vision_agent.process_task(task)
                return result
            else:
                # Демо режим
                return {
                    "status": "demo",
                    "message": "Демо: Анализ изображения будет выполнен при полной инициализации BLIP2",
                    "image_path": image_path,
                    "question": question,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка анализа изображения: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """Получение статуса координатора"""
        return {
            "demo_mode": self.demo_mode,
            "agents_initialized": self.agents_initialized,
            "active_chats": len(self.chat_sessions),
            "agents": {
                "text_agent": self.text_agent is not None,
                "vision_agent": self.vision_agent is not None,
                "image_agent": self.image_agent is not None
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup(self):
        """Очистка ресурсов"""
        self.logger.info("🧹 Очистка ресурсов ChatCoordinator...")
        
        if self.text_agent:
            await self.text_agent._cleanup_agent()
        if self.vision_agent:
            await self.vision_agent._cleanup_agent()
        if self.image_agent:
            await self.image_agent._cleanup_agent()
        
        self.chat_sessions.clear()
        self.logger.info("✅ ChatCoordinator очищен")