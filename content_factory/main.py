"""
Главный модуль запуска контент-завода
"""

import sys
import os
from pathlib import Path

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent))

from content_factory.config.settings import settings
from content_factory.config.database import db
import argparse


def init_system():
    """Инициализация системы"""
    print("🏭 Инициализация контент-завода...")
    
    # Проверяем создание БД
    print("✓ База данных инициализирована")
    
    # Создаем необходимые директории
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    os.makedirs(settings.TEMPLATES_DIR, exist_ok=True)
    os.makedirs(settings.STATIC_DIR, exist_ok=True)
    print("✓ Директории созданы")
    
    print("✅ Система готова к работе!")


def run_web_ui():
    """Запуск веб-интерфейса"""
    import subprocess
    import streamlit.web.cli as stcli
    
    print(f"🌐 Запуск веб-интерфейса на http://{settings.WEB_HOST}:{settings.WEB_PORT}")
    
    # Запускаем Streamlit
    web_ui_path = Path(__file__).parent / "web_ui.py"
    os.system(f"streamlit run {web_ui_path} --server.port {settings.WEB_PORT} --server.address {settings.WEB_HOST}")


def run_cli():
    """Запуск CLI интерфейса"""
    from content_factory.modules.planning import ContentPlanner
    from content_factory.modules.preparation import SpecGenerator
    from content_factory.modules.production import ContentProducer
    from content_factory.modules.quality_control import QualityController
    
    planner = ContentPlanner()
    spec_generator = SpecGenerator()
    producer = ContentProducer()
    quality = QualityController()
    
    print("🏭 Контент-завод - CLI режим")
    print("=" * 50)
    
    while True:
        print("\nВыберите действие:")
        print("1. Собрать идеи")
        print("2. Создать контент-план")
        print("3. Создать ТЗ")
        print("4. Произвести контент")
        print("5. Проверить качество")
        print("6. Выход")
        
        choice = input("\nВаш выбор: ").strip()
        
        if choice == "1":
            topics = db.get_topics()
            if not topics:
                print("❌ Нет тем. Создайте тему в веб-интерфейсе.")
                continue
            
            print("\nДоступные темы:")
            for i, topic in enumerate(topics, 1):
                print(f"{i}. {topic['name']}")
            
            try:
                topic_idx = int(input("Выберите тему (номер): ")) - 1
                selected_topic = topics[topic_idx]
                
                print(f"\nСобираю идеи для темы: {selected_topic['name']}")
                ideas = planner.collect_ideas(selected_topic['id'])
                planner.save_ideas(ideas)
                print(f"✅ Собрано {len(ideas)} идей!")
            except (ValueError, IndexError):
                print("❌ Неверный выбор")
        
        elif choice == "2":
            print("\nСоздаю контент-план...")
            plan = planner.create_content_plan()
            print(f"✅ Создан план на {plan['total_items']} единиц контента")
        
        elif choice == "3":
            plan_items = db.get_content_plan()
            if not plan_items:
                print("❌ Нет записей в контент-плане")
                continue
            
            print("\nДоступные планы:")
            for i, item in enumerate(plan_items[:10], 1):
                print(f"{i}. {item['publish_date']} - {item['format']}")
            
            try:
                plan_idx = int(input("Выберите план (номер): ")) - 1
                selected_plan = plan_items[plan_idx]
                
                print("\nСоздаю ТЗ...")
                spec = spec_generator.generate_spec(selected_plan['id'])
                print(f"✅ ТЗ создано: {spec['title']}")
            except (ValueError, IndexError) as e:
                print(f"❌ Ошибка: {e}")
        
        elif choice == "4":
            specs = db.get_specs()
            if not specs:
                print("❌ Нет ТЗ")
                continue
            
            print("\nДоступные ТЗ:")
            for i, spec in enumerate(specs[:10], 1):
                print(f"{i}. {spec['title']}")
            
            try:
                spec_idx = int(input("Выберите ТЗ (номер): ")) - 1
                selected_spec = specs[spec_idx]
                
                print("\nПроизвожу контент...")
                content = producer.create_content(selected_spec['id'])
                print(f"✅ Контент создан: {content['title']}")
                print(f"   Длина: {len(content['content'].split())} слов")
            except (ValueError, IndexError) as e:
                print(f"❌ Ошибка: {e}")
        
        elif choice == "5":
            content_items = db.get_content_items(status="draft")
            if not content_items:
                print("❌ Нет контента для проверки")
                continue
            
            print("\nДоступный контент:")
            for i, item in enumerate(content_items[:10], 1):
                print(f"{i}. {item['title']}")
            
            try:
                content_idx = int(input("Выберите контент (номер): ")) - 1
                selected_content = content_items[content_idx]
                
                print("\nПроверяю качество...")
                result = quality.check_content(selected_content['id'])
                print(f"✅ Проверка завершена")
                print(f"   Оценка: {result['overall_score']:.2%}")
                print(f"   Статус: {result['status']}")
                
                if result['recommendations']:
                    print("\nРекомендации:")
                    for rec in result['recommendations'][:5]:
                        print(f"   • {rec}")
            except (ValueError, IndexError) as e:
                print(f"❌ Ошибка: {e}")
        
        elif choice == "6":
            print("👋 До свидания!")
            break
        
        else:
            print("❌ Неверный выбор")


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description="Контент-завод - система производства контента")
    parser.add_argument(
        "--mode",
        choices=["web", "cli", "init"],
        default="web",
        help="Режим работы (web, cli, init)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "init":
        init_system()
    elif args.mode == "web":
        init_system()
        run_web_ui()
    elif args.mode == "cli":
        init_system()
        run_cli()


if __name__ == "__main__":
    main()
