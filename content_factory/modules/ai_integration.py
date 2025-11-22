"""
Интеграция с AI моделями для генерации контента
Поддержка нескольких бесплатных локальных моделей
"""

import os
from typing import Dict, Any, Optional, List
from content_factory.config.settings import settings

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class AIIntegration:
    """Класс для интеграции с различными AI моделями"""
    
    def __init__(self):
        self.settings = settings
        self.text_generator = None
        self.embedding_model = None
        self._init_models()
    
    def _init_models(self):
        """Инициализация моделей"""
        # Инициализация текстовой модели
        if TRANSFORMERS_AVAILABLE:
            try:
                model_name = self.settings.AI_MODELS["text_generation"]["model"]
                self.text_generator = pipeline(
                    "text-generation",
                    model=model_name,
                    device=-1,  # CPU
                    model_kwargs={"torch_dtype": "auto"}
                )
            except Exception as e:
                print(f"Не удалось загрузить локальную модель: {e}")
                self.text_generator = None
        
        # Инициализация модели эмбеддингов
        if TRANSFORMERS_AVAILABLE:
            try:
                from sentence_transformers import SentenceTransformer
                embedding_model_name = self.settings.AI_MODELS["text_embedding"]["model"]
                self.embedding_model = SentenceTransformer(embedding_model_name)
            except Exception as e:
                print(f"Не удалось загрузить модель эмбеддингов: {e}")
                self.embedding_model = None
    
    def generate_text(self, prompt: str, max_tokens: int = 1000, 
                     temperature: float = 0.7, **kwargs) -> str:
        """
        Генерация текста с помощью AI
        
        Args:
            prompt: Текст запроса
            max_tokens: Максимальное количество токенов
            temperature: Температура генерации
        """
        # Пробуем локальную модель
        if self.text_generator:
            try:
                result = self.text_generator(
                    prompt,
                    max_length=len(prompt.split()) + max_tokens,
                    temperature=temperature,
                    do_sample=True,
                    num_return_sequences=1
                )
                if result and len(result) > 0:
                    generated_text = result[0]['generated_text']
                    # Убираем оригинальный промпт из результата
                    if generated_text.startswith(prompt):
                        generated_text = generated_text[len(prompt):].strip()
                    return generated_text
            except Exception as e:
                print(f"Ошибка генерации локальной моделью: {e}")
        
        # Пробуем OpenAI (если есть API ключ)
        if OPENAI_AVAILABLE and self.settings.OPENAI_API_KEY:
            try:
                openai.api_key = self.settings.OPENAI_API_KEY
                response = openai.Completion.create(
                    model="gpt-3.5-turbo-instruct",
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].text.strip()
            except Exception as e:
                print(f"Ошибка генерации OpenAI: {e}")
        
        # Пробуем Yandex GPT (если есть API ключ)
        if REQUESTS_AVAILABLE and self.settings.YANDEX_GPT_API_KEY:
            try:
                return self._generate_with_yandex_gpt(prompt, max_tokens, temperature)
            except Exception as e:
                print(f"Ошибка генерации Yandex GPT: {e}")
        
        # Fallback - возвращаем шаблонный ответ
        return self._get_fallback_response(prompt)
    
    def _generate_with_yandex_gpt(self, prompt: str, max_tokens: int,
                                  temperature: float) -> str:
        """Генерация с помощью Yandex GPT"""
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Authorization": f"Api-Key {self.settings.YANDEX_GPT_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "modelUri": f"gpt://{self.settings.YANDEX_GPT_API_KEY}/yandexgpt/latest",
            "completionOptions": {
                "stream": False,
                "temperature": temperature,
                "maxTokens": str(max_tokens)
            },
            "messages": [
                {
                    "role": "user",
                    "text": prompt
                }
            ]
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        return result['result']['alternatives'][0]['message']['text']
    
    def _get_fallback_response(self, prompt: str) -> str:
        """Fallback ответ, если все модели недоступны"""
        # Простая шаблонная генерация на основе ключевых слов
        keywords = prompt.split()[:5]
        return f"Контент на тему: {', '.join(keywords)}. " \
               f"Это важная тема, требующая детального рассмотрения. " \
               f"Рекомендуется изучить различные аспекты данной темы."
    
    def generate_embedding(self, text: str) -> List[float]:
        """Генерация эмбеддинга для текста"""
        if self.embedding_model:
            try:
                return self.embedding_model.encode(text).tolist()
            except Exception as e:
                print(f"Ошибка генерации эмбеддинга: {e}")
        
        # Fallback - простой эмбеддинг
        return [0.0] * 384
    
    def analyze_seo(self, text: str, keywords: List[str]) -> Dict[str, Any]:
        """SEO-анализ текста"""
        text_lower = text.lower()
        keywords_lower = [kw.lower() for kw in keywords]
        
        # Подсчет вхождений ключевых слов
        keyword_counts = {}
        for keyword in keywords_lower:
            count = text_lower.count(keyword)
            keyword_counts[keyword] = count
        
        # Плотность ключевых слов
        total_words = len(text.split())
        keyword_density = {}
        for keyword, count in keyword_counts.items():
            keyword_density[keyword] = (count / total_words * 100) if total_words > 0 else 0
        
        # Проверка наличия в заголовках
        has_in_h1 = any(kw in text_lower for kw in keywords_lower)
        
        # Оценка SEO
        seo_score = 0.0
        if any(count > 0 for count in keyword_counts.values()):
            seo_score += 0.3
        if any(density > 1.0 and density < 3.0 for density in keyword_density.values()):
            seo_score += 0.3
        if has_in_h1:
            seo_score += 0.2
        if len(text) >= 1000:
            seo_score += 0.2
        
        return {
            "score": seo_score,
            "keyword_counts": keyword_counts,
            "keyword_density": keyword_density,
            "has_in_h1": has_in_h1,
            "recommendations": self._get_seo_recommendations(keyword_counts, keyword_density, has_in_h1)
        }
    
    def _get_seo_recommendations(self, keyword_counts: Dict, 
                                 keyword_density: Dict, has_in_h1: bool) -> List[str]:
        """Получение SEO-рекомендаций"""
        recommendations = []
        
        if not any(count > 0 for count in keyword_counts.values()):
            recommendations.append("Добавьте ключевые слова в текст")
        
        for keyword, density in keyword_density.items():
            if density < 1.0:
                recommendations.append(f"Увеличьте плотность ключевого слова '{keyword}'")
            elif density > 3.0:
                recommendations.append(f"Уменьшите плотность ключевого слова '{keyword}' (переоптимизация)")
        
        if not has_in_h1:
            recommendations.append("Добавьте ключевые слова в заголовок H1")
        
        return recommendations
    
    def summarize_text(self, text: str, max_length: int = 200) -> str:
        """Суммаризация текста"""
        prompt = f"Создай краткое резюме следующего текста (не более {max_length} слов):\n\n{text}"
        return self.generate_text(prompt, max_tokens=max_length // 2)
    
    def rewrite_text(self, text: str, style: str = "professional") -> str:
        """Переписывание текста в другом стиле"""
        style_prompts = {
            "professional": "Перепиши следующий текст в профессиональном стиле:",
            "casual": "Перепиши следующий текст в неформальном стиле:",
            "simple": "Упрости следующий текст, сделай его более понятным:",
            "engaging": "Перепиши следующий текст, сделай его более увлекательным:"
        }
        
        prompt = f"{style_prompts.get(style, style_prompts['professional'])}\n\n{text}"
        return self.generate_text(prompt, max_tokens=len(text.split()) * 2)
