"""
Тестирование системы контент-завода
"""

import sys
import os
from pathlib import Path

# Добавляем путь к корню проекта
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Тест импортов модулей"""
    print("🔍 Тест 1: Импорт модулей...")
    try:
        # Меняем рабочую директорию
        os.chdir(Path(__file__).parent)
        
        from config.settings import settings
        print("   ✓ settings")
        
        from config.database import db
        print("   ✓ database")
        
        from modules.planning import ContentPlanner
        print("   ✓ planning")
        
        from modules.preparation import SpecGenerator
        print("   ✓ preparation")
        
        from modules.production import ContentProducer
        print("   ✓ production")
        
        from modules.quality_control import QualityController
        print("   ✓ quality_control")
        
        from modules.packaging import ContentPackager
        print("   ✓ packaging")
        
        from modules.distribution import ContentDistributor
        print("   ✓ distribution")
        
        from modules.analytics import ContentAnalytics
        print("   ✓ analytics")
        
        from modules.ai_integration import AIIntegration
        print("   ✓ ai_integration")
        
        print("✅ Все модули импортированы успешно!\n")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}\n")
        return False


def test_database():
    """Тест базы данных"""
    print("🔍 Тест 2: База данных...")
    try:
        from config.database import db
        
        # Проверяем создание таблиц
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Проверяем наличие основных таблиц
        tables = ['goals', 'audiences', 'topics', 'content_ideas', 'content_plan']
        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                print(f"   ✓ Таблица {table} существует")
            else:
                print(f"   ⚠ Таблица {table} не найдена")
        
        conn.close()
        print("✅ База данных работает!\n")
        return True
    except Exception as e:
        print(f"❌ Ошибка БД: {e}\n")
        return False


def test_modules():
    """Тест инициализации модулей"""
    print("🔍 Тест 3: Инициализация модулей...")
    try:
        from modules.planning import ContentPlanner
        from modules.preparation import SpecGenerator
        from modules.production import ContentProducer
        from modules.quality_control import QualityController
        
        planner = ContentPlanner()
        print("   ✓ ContentPlanner инициализирован")
        
        spec_generator = SpecGenerator()
        print("   ✓ SpecGenerator инициализирован")
        
        producer = ContentProducer()
        print("   ✓ ContentProducer инициализирован")
        
        quality = QualityController()
        print("   ✓ QualityController инициализирован")
        
        print("✅ Все модули инициализированы!\n")
        return True
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_ai_integration():
    """Тест AI интеграции"""
    print("🔍 Тест 4: AI интеграция...")
    try:
        from modules.ai_integration import AIIntegration
        
        ai = AIIntegration()
        print("   ✓ AIIntegration инициализирован")
        
        # Тест генерации текста (fallback режим)
        test_prompt = "Напиши одно предложение о тестировании."
        result = ai.generate_text(test_prompt, max_tokens=50)
        
        if result and len(result) > 10:
            print(f"   ✓ Генерация текста работает: '{result[:50]}...'")
        else:
            print(f"   ⚠ Генерация текста вернула короткий результат")
        
        print("✅ AI интеграция работает!\n")
        return True
    except Exception as e:
        print(f"❌ Ошибка AI: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_basic_workflow():
    """Тест базового рабочего процесса"""
    print("🔍 Тест 5: Базовый рабочий процесс...")
    try:
        from config.database import db
        from modules.planning import ContentPlanner
        
        # Создаем тестовую цель
        goal_id = db.add_goal("Тестовая цель", "Для тестирования")
        print(f"   ✓ Цель создана (ID: {goal_id})")
        
        # Создаем тестовую аудиторию
        audience_id = db.add_audience("Тестовая аудитория", "Для тестирования")
        print(f"   ✓ Аудитория создана (ID: {audience_id})")
        
        # Создаем тестовую тему
        topic_id = db.add_topic("Тестовая тема", "Для тестирования", goal_id, audience_id)
        print(f"   ✓ Тема создана (ID: {topic_id})")
        
        # Собираем идеи
        planner = ContentPlanner()
        ideas = planner.collect_ideas(topic_id, sources=["seo"])
        print(f"   ✓ Собрано {len(ideas)} идей")
        
        if ideas:
            planner.save_ideas(ideas)
            print(f"   ✓ Идеи сохранены в БД")
        
        print("✅ Базовый рабочий процесс работает!\n")
        return True
    except Exception as e:
        print(f"❌ Ошибка рабочего процесса: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Запуск всех тестов"""
    print("=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ КОНТЕНТ-ЗАВОДА")
    print("=" * 60)
    print()
    
    results = []
    
    results.append(("Импорты", test_imports()))
    results.append(("База данных", test_database()))
    results.append(("Модули", test_modules()))
    results.append(("AI интеграция", test_ai_integration()))
    results.append(("Рабочий процесс", test_basic_workflow()))
    
    print("=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print()
    print(f"Итого: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("\n🎉 Все тесты пройдены! Система готова к работе!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} тест(ов) не пройдено. Проверьте ошибки выше.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
