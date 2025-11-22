"""
Пример использования контент-завода
"""

from content_factory.config.database import db
from content_factory.modules.planning import ContentPlanner
from content_factory.modules.preparation import SpecGenerator
from content_factory.modules.production import ContentProducer
from content_factory.modules.quality_control import QualityController
from content_factory.modules.packaging import ContentPackager
from content_factory.modules.distribution import ContentDistributor
from content_factory.modules.analytics import ContentAnalytics


def example_workflow():
    """Пример полного рабочего процесса"""
    
    print("🏭 Пример работы контент-завода\n")
    
    # 1. Фундамент
    print("1. Создание фундамента...")
    goal_id = db.add_goal(
        name="Привлечение трафика на сайт",
        description="Увеличение органического трафика через контент-маркетинг",
        target_metric="visitors",
        target_value=10000.0
    )
    print(f"   ✓ Цель создана (ID: {goal_id})")
    
    audience_id = db.add_audience(
        name="Предприниматели",
        description="Владельцы малого и среднего бизнеса, 25-45 лет",
        demographics={"age": "25-45", "profession": "business_owner"},
        pain_points=["нехватка времени", "поиск эффективных решений"],
        preferred_channels=["telegram", "vk", "website"],
        language="ru"
    )
    print(f"   ✓ Аудитория создана (ID: {audience_id})")
    
    topic_id = db.add_topic(
        name="Маркетинг для малого бизнеса",
        description="Практические советы по маркетингу",
        goal_id=goal_id,
        audience_id=audience_id,
        priority=1
    )
    print(f"   ✓ Тема создана (ID: {topic_id})\n")
    
    # 2. Планирование
    print("2. Планирование контента...")
    planner = ContentPlanner()
    ideas = planner.collect_ideas(topic_id, sources=["seo", "questions"])
    planner.save_ideas(ideas)
    print(f"   ✓ Собрано {len(ideas)} идей")
    
    # Одобряем первую идею (в реальности это делается через интерфейс)
    # idea_id = ideas[0] if ideas else None
    
    plan = planner.create_content_plan(days_ahead=7)
    print(f"   ✓ Создан контент-план на {plan['total_items']} единиц\n")
    
    # 3. Подготовка ТЗ
    print("3. Создание ТЗ...")
    spec_generator = SpecGenerator()
    if plan['plan']:
        first_plan_id = list(plan['plan'].values())[0]['plan_id']
        try:
            spec = spec_generator.generate_spec(first_plan_id)
            print(f"   ✓ ТЗ создано: {spec['title']}\n")
        except Exception as e:
            print(f"   ⚠ Ошибка создания ТЗ: {e}\n")
    
    # 4. Производство
    print("4. Производство контента...")
    producer = ContentProducer()
    specs = db.get_specs()
    if specs:
        try:
            content = producer.create_content(specs[0]['id'])
            print(f"   ✓ Контент создан: {content['title']}")
            print(f"   ✓ Длина: {len(content['content'].split())} слов\n")
        except Exception as e:
            print(f"   ⚠ Ошибка производства: {e}\n")
    
    # 5. Контроль качества
    print("5. Контроль качества...")
    quality = QualityController()
    content_items = db.get_content_items()
    if content_items:
        try:
            result = quality.check_content(content_items[0]['id'])
            print(f"   ✓ Проверка завершена")
            print(f"   ✓ Оценка: {result['overall_score']:.2%}")
            print(f"   ✓ Статус: {result['status']}\n")
        except Exception as e:
            print(f"   ⚠ Ошибка проверки: {e}\n")
    
    # 6. Упаковка
    print("6. Упаковка контента...")
    packager = ContentPackager()
    if content_items:
        try:
            cover = packager.create_cover(
                content_items[0]['id'],
                content_items[0]['title']
            )
            print(f"   ✓ Обложка создана: {cover['file_path']}\n")
        except Exception as e:
            print(f"   ⚠ Ошибка упаковки: {e}\n")
    
    # 7. Аналитика
    print("7. Аналитика...")
    analytics = ContentAnalytics()
    plan_analytics = analytics.get_content_plan_analytics()
    print(f"   ✓ Всего в плане: {plan_analytics['total_items']}")
    print(f"   ✓ По форматам: {plan_analytics['by_format']}\n")
    
    print("✅ Пример завершен!")
    print("\nДля полного использования запустите веб-интерфейс:")
    print("   python content_factory/main.py --mode web")


if __name__ == "__main__":
    example_workflow()
