"""
Модуль подготовки ТЗ (Шаг 2: Цех подготовки)
"""

from typing import Dict, Any, List, Optional

try:
    from content_factory.config.database import db
    from content_factory.modules.ai_integration import AIIntegration
except ImportError:
    from config.database import db
    from modules.ai_integration import AIIntegration


class SpecGenerator:
    """Класс для генерации технических заданий"""
    
    def __init__(self):
        self.db = db
        self.ai = AIIntegration()
    
    def generate_spec(self, plan_id: int) -> Dict[str, Any]:
        """
        Генерация ТЗ для контента
        
        Args:
            plan_id: ID записи в контент-плане
        """
        # Получаем информацию о плане
        plan_items = self.db.get_content_plan()
        plan_item = None
        for item in plan_items:
            if item['id'] == plan_id:
                plan_item = item
                break
        
        if not plan_item:
            raise ValueError(f"План с ID {plan_id} не найден")
        
        # Получаем идею
        ideas = self.db.get_ideas()
        idea = None
        for i in ideas:
            if i['id'] == plan_item['idea_id']:
                idea = i
                break
        
        if not idea:
            raise ValueError(f"Идея с ID {plan_item['idea_id']} не найдена")
        
        # Получаем тему
        topics = self.db.get_topics()
        topic = None
        for t in topics:
            if t['id'] == idea.get('topic_id'):
                topic = t
                break
        
        # Получаем аудиторию
        audiences = self.db.get_audiences()
        audience = None
        if topic and topic.get('audience_id'):
            for a in audiences:
                if a['id'] == topic['audience_id']:
                    audience = a
                    break
        
        # Генерируем структуру с помощью AI
        structure = self._generate_structure(idea, topic, audience, plan_item['format'])
        
        # Генерируем основные тезисы
        main_points = self._generate_main_points(idea, topic, audience)
        
        # Извлекаем ключевые слова
        keywords = []
        if idea.get('keywords'):
            import json
            keywords = json.loads(idea['keywords'])
        
        # Генерируем цель контента
        goal = self._generate_goal(idea, topic, audience)
        
        # Создаем ТЗ
        spec_id = self.db.add_spec(
            plan_id=plan_id,
            title=idea['title'],
            structure=structure,
            goal=goal,
            target_audience=audience['name'] if audience else "Общая аудитория",
            keywords=keywords,
            main_points=main_points,
            references=[],  # Ссылки на источники
            requirements=self._generate_requirements(plan_item['format'])
        )
        
        return {
            "spec_id": spec_id,
            "title": idea['title'],
            "structure": structure,
            "goal": goal,
            "main_points": main_points
        }
    
    def _generate_structure(self, idea: Dict, topic: Dict = None, 
                           audience: Dict = None, format: str = "article") -> Dict[str, Any]:
        """Генерация структуры контента"""
        
        # Базовая структура статьи
        if format == "article":
            structure = {
                "type": "article",
                "sections": [
                    {
                        "type": "introduction",
                        "title": "Введение",
                        "description": "Краткое введение в тему, привлечение внимания",
                        "length": "200-300 слов"
                    },
                    {
                        "type": "main_content",
                        "title": "Основной контент",
                        "description": "Раскрытие темы, основные тезисы",
                        "subsections": []
                    },
                    {
                        "type": "conclusion",
                        "title": "Заключение",
                        "description": "Резюме, призыв к действию",
                        "length": "100-200 слов"
                    }
                ]
            }
            
            # Генерируем подразделы с помощью AI
            prompt = f"""
            Создай структуру статьи на тему: {idea['title']}
            
            Тема: {topic['name'] if topic else 'Общая'}
            Аудитория: {audience['name'] if audience else 'Общая'}
            
            Создай 3-5 подразделов для основной части статьи.
            Верни только список подразделов, каждый с названием и кратким описанием.
            Формат: JSON массив объектов с полями "title" и "description"
            """
            
            try:
                ai_response = self.ai.generate_text(prompt, max_tokens=500)
                # Парсим ответ AI (упрощенная версия)
                # В реальности нужен более надежный парсинг
                import json
                import re
                json_match = re.search(r'\[.*\]', ai_response, re.DOTALL)
                if json_match:
                    subsections = json.loads(json_match.group())
                    structure["sections"][1]["subsections"] = subsections[:5]
            except:
                # Если AI не сработал, используем шаблон
                structure["sections"][1]["subsections"] = [
                    {"title": "Основной раздел 1", "description": "Описание первого раздела"},
                    {"title": "Основной раздел 2", "description": "Описание второго раздела"},
                    {"title": "Основной раздел 3", "description": "Описание третьего раздела"}
                ]
        
        elif format == "post":
            structure = {
                "type": "post",
                "sections": [
                    {"type": "hook", "description": "Цепляющий заголовок"},
                    {"type": "body", "description": "Основной текст поста"},
                    {"type": "cta", "description": "Призыв к действию"}
                ]
            }
        else:
            structure = {"type": format, "sections": []}
        
        return structure
    
    def _generate_main_points(self, idea: Dict, topic: Dict = None,
                             audience: Dict = None) -> List[str]:
        """Генерация основных тезисов"""
        
        prompt = f"""
        Создай 5-7 основных тезисов для контента на тему: {idea['title']}
        
        Тема: {topic['name'] if topic else 'Общая'}
        Аудитория: {audience['name'] if audience else 'Общая'}
        
        Верни только список тезисов, каждый с новой строки, начинающийся с "-"
        """
        
        try:
            ai_response = self.ai.generate_text(prompt, max_tokens=300)
            # Извлекаем тезисы из ответа
            points = [line.strip("- ").strip() for line in ai_response.split("\n") 
                     if line.strip().startswith("-")]
            return points[:7] if points else self._get_default_points(idea)
        except:
            return self._get_default_points(idea)
    
    def _get_default_points(self, idea: Dict) -> List[str]:
        """Получение тезисов по умолчанию"""
        return [
            f"Введение в тему: {idea['title']}",
            "Основные концепции и принципы",
            "Практические примеры и кейсы",
            "Рекомендации и лучшие практики",
            "Заключение и выводы"
        ]
    
    def _generate_goal(self, idea: Dict, topic: Dict = None,
                      audience: Dict = None) -> str:
        """Генерация цели контента"""
        
        goals = self.db.get_goals()
        if goals and topic:
            # Пытаемся найти цель, связанную с темой
            for goal in goals:
                if goal.get('id') == topic.get('goal_id'):
                    return goal['name']
        
        # Генерируем цель с помощью AI
        prompt = f"""
        Определи цель контента на тему: {idea['title']}
        
        Верни только краткое описание цели (1-2 предложения)
        """
        
        try:
            return self.ai.generate_text(prompt, max_tokens=100).strip()
        except:
            return "Информировать и помочь аудитории разобраться в теме"
    
    def _generate_requirements(self, format: str) -> Dict[str, Any]:
        """Генерация требований к контенту"""
        
        base_requirements = {
            "min_length": 1000,
            "max_length": 5000,
            "seo_required": True,
            "images_required": True,
            "links_required": True
        }
        
        if format == "post":
            base_requirements.update({
                "min_length": 200,
                "max_length": 1000
            })
        elif format == "video":
            base_requirements.update({
                "min_length": 300,
                "max_length": 2000,
                "video_script": True
            })
        
        return base_requirements
    
    def get_spec(self, spec_id: int) -> Optional[Dict[str, Any]]:
        """Получение ТЗ по ID"""
        specs = self.db.get_specs()
        for spec in specs:
            if spec['id'] == spec_id:
                return spec
        return None
