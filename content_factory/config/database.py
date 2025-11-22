"""
База данных для контент-завода
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from content_factory.config.settings import settings


class ContentFactoryDB:
    """Класс для работы с базой данных контент-завода"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DB_PATH
        self._init_database()
    
    def _init_database(self):
        """Инициализация базы данных и создание таблиц"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица целей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                target_metric TEXT,
                target_value REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица аудиторий
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                demographics TEXT,  -- JSON
                pain_points TEXT,  -- JSON
                preferred_channels TEXT,  -- JSON
                language TEXT DEFAULT 'ru',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица ключевых тем
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                goal_id INTEGER,
                audience_id INTEGER,
                priority INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES goals(id),
                FOREIGN KEY (audience_id) REFERENCES audiences(id)
            )
        """)
        
        # Таблица идей контента
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                topic_id INTEGER,
                source TEXT,  -- откуда пришла идея
                keywords TEXT,  -- JSON массив
                seo_potential REAL DEFAULT 0.0,
                priority INTEGER DEFAULT 1,
                status TEXT DEFAULT 'new',  -- new, approved, rejected
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (topic_id) REFERENCES topics(id)
            )
        """)
        
        # Таблица контент-плана
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_plan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idea_id INTEGER,
                publish_date DATE NOT NULL,
                format TEXT NOT NULL,  -- article, post, video, etc.
                platform TEXT,  -- где публикуем
                keyword TEXT,
                responsible TEXT,
                status TEXT DEFAULT 'planned',  -- planned, in_progress, ready, published
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (idea_id) REFERENCES content_ideas(id)
            )
        """)
        
        # Таблица технических заданий
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_specs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER,
                title TEXT NOT NULL,
                structure TEXT,  -- JSON структура статьи
                goal TEXT,
                target_audience TEXT,
                keywords TEXT,  -- JSON массив
                main_points TEXT,  -- JSON массив
                references TEXT,  -- JSON массив ссылок
                requirements TEXT,  -- JSON дополнительные требования
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plan_id) REFERENCES content_plan(id)
            )
        """)
        
        # Таблица готового контента
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spec_id INTEGER,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                format TEXT NOT NULL,
                metadata TEXT,  -- JSON
                status TEXT DEFAULT 'draft',  -- draft, review, approved, published
                quality_score REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (spec_id) REFERENCES content_specs(id)
            )
        """)
        
        # Таблица проверок качества
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id INTEGER,
                check_type TEXT NOT NULL,  -- editing, proofreading, factcheck, seo
                status TEXT DEFAULT 'pending',  -- pending, passed, failed
                issues TEXT,  -- JSON массив проблем
                score REAL DEFAULT 0.0,
                checked_by TEXT,
                checked_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (content_id) REFERENCES content_items(id)
            )
        """)
        
        # Таблица дизайна
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS design_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id INTEGER,
                asset_type TEXT NOT NULL,  -- cover, infographic, illustration
                file_path TEXT NOT NULL,
                metadata TEXT,  -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (content_id) REFERENCES content_items(id)
            )
        """)
        
        # Таблица публикаций
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS publications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id INTEGER,
                platform TEXT NOT NULL,
                url TEXT,
                published_at TIMESTAMP,
                status TEXT DEFAULT 'scheduled',  -- scheduled, published, failed
                metadata TEXT,  -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (content_id) REFERENCES content_items(id)
            )
        """)
        
        # Таблица аналитики
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id INTEGER,
                publication_id INTEGER,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                date DATE NOT NULL,
                metadata TEXT,  -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (content_id) REFERENCES content_items(id),
                FOREIGN KEY (publication_id) REFERENCES publications(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Получение соединения с БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # Методы для работы с целями
    def add_goal(self, name: str, description: str = "", target_metric: str = "", target_value: float = 0.0) -> int:
        """Добавление цели"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO goals (name, description, target_metric, target_value)
            VALUES (?, ?, ?, ?)
        """, (name, description, target_metric, target_value))
        goal_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return goal_id
    
    def get_goals(self) -> List[Dict[str, Any]]:
        """Получение всех целей"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM goals ORDER BY created_at DESC")
        goals = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return goals
    
    # Методы для работы с аудиториями
    def add_audience(self, name: str, description: str = "", demographics: Dict = None,
                    pain_points: List[str] = None, preferred_channels: List[str] = None,
                    language: str = "ru") -> int:
        """Добавление аудитории"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audiences (name, description, demographics, pain_points, preferred_channels, language)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            name,
            description,
            json.dumps(demographics or {}),
            json.dumps(pain_points or []),
            json.dumps(preferred_channels or []),
            language
        ))
        audience_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return audience_id
    
    def get_audiences(self) -> List[Dict[str, Any]]:
        """Получение всех аудиторий"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audiences ORDER BY created_at DESC")
        audiences = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return audiences
    
    # Методы для работы с темами
    def add_topic(self, name: str, description: str = "", goal_id: int = None,
                  audience_id: int = None, priority: int = 1) -> int:
        """Добавление темы"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO topics (name, description, goal_id, audience_id, priority)
            VALUES (?, ?, ?, ?, ?)
        """, (name, description, goal_id, audience_id, priority))
        topic_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return topic_id
    
    def get_topics(self) -> List[Dict[str, Any]]:
        """Получение всех тем"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM topics ORDER BY priority DESC, created_at DESC")
        topics = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return topics
    
    # Методы для работы с идеями
    def add_idea(self, title: str, description: str = "", topic_id: int = None,
                source: str = "", keywords: List[str] = None, seo_potential: float = 0.0,
                priority: int = 1) -> int:
        """Добавление идеи"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO content_ideas (title, description, topic_id, source, keywords, seo_potential, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            description,
            topic_id,
            source,
            json.dumps(keywords or []),
            seo_potential,
            priority
        ))
        idea_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return idea_id
    
    def get_ideas(self, status: str = None) -> List[Dict[str, Any]]:
        """Получение идей"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM content_ideas WHERE status = ? ORDER BY priority DESC, created_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM content_ideas ORDER BY priority DESC, created_at DESC")
        ideas = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return ideas
    
    # Методы для работы с контент-планом
    def add_to_plan(self, idea_id: int, publish_date: str, format: str, platform: str = None,
                   keyword: str = None, responsible: str = None) -> int:
        """Добавление в контент-план"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO content_plan (idea_id, publish_date, format, platform, keyword, responsible)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (idea_id, publish_date, format, platform, keyword, responsible))
        plan_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return plan_id
    
    def get_content_plan(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """Получение контент-плана"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if start_date and end_date:
            cursor.execute("""
                SELECT * FROM content_plan 
                WHERE publish_date BETWEEN ? AND ?
                ORDER BY publish_date ASC
            """, (start_date, end_date))
        else:
            cursor.execute("SELECT * FROM content_plan ORDER BY publish_date ASC")
        plan = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return plan
    
    # Методы для работы с ТЗ
    def add_spec(self, plan_id: int, title: str, structure: Dict = None, goal: str = "",
                target_audience: str = "", keywords: List[str] = None,
                main_points: List[str] = None, references: List[str] = None,
                requirements: Dict = None) -> int:
        """Добавление ТЗ"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO content_specs (plan_id, title, structure, goal, target_audience, keywords, main_points, references, requirements)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            plan_id,
            title,
            json.dumps(structure or {}),
            goal,
            target_audience,
            json.dumps(keywords or []),
            json.dumps(main_points or []),
            json.dumps(references or []),
            json.dumps(requirements or {})
        ))
        spec_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return spec_id
    
    def get_specs(self, plan_id: int = None) -> List[Dict[str, Any]]:
        """Получение ТЗ"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if plan_id:
            cursor.execute("SELECT * FROM content_specs WHERE plan_id = ?", (plan_id,))
        else:
            cursor.execute("SELECT * FROM content_specs ORDER BY created_at DESC")
        specs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return specs
    
    # Методы для работы с контентом
    def add_content(self, spec_id: int, title: str, content: str, format: str,
                   metadata: Dict = None, status: str = "draft") -> int:
        """Добавление контента"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO content_items (spec_id, title, content, format, metadata, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            spec_id,
            title,
            content,
            format,
            json.dumps(metadata or {}),
            status
        ))
        content_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return content_id
    
    def get_content_items(self, status: str = None) -> List[Dict[str, Any]]:
        """Получение контента"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM content_items WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM content_items ORDER BY created_at DESC")
        items = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return items
    
    def update_content_status(self, content_id: int, status: str):
        """Обновление статуса контента"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE content_items SET status = ? WHERE id = ?", (status, content_id))
        conn.commit()
        conn.close()
    
    # Методы для работы с аналитикой
    def add_analytics(self, content_id: int, publication_id: int, metric_name: str,
                     metric_value: float, date: str, metadata: Dict = None):
        """Добавление метрики"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analytics (content_id, publication_id, metric_name, metric_value, date, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            content_id,
            publication_id,
            metric_name,
            metric_value,
            date,
            json.dumps(metadata or {})
        ))
        conn.commit()
        conn.close()
    
    def get_analytics(self, content_id: int = None, start_date: str = None,
                     end_date: str = None) -> List[Dict[str, Any]]:
        """Получение аналитики"""
        conn = self.get_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM analytics WHERE 1=1"
        params = []
        
        if content_id:
            query += " AND content_id = ?"
            params.append(content_id)
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date DESC"
        cursor.execute(query, params)
        analytics = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return analytics


# Глобальный экземпляр БД
db = ContentFactoryDB()
