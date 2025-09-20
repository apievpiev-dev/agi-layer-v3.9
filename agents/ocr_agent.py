"""
OCRAgent - распознавание текста с помощью EasyOCR (CPU-only)
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import cv2
import numpy as np
from PIL import Image
import easyocr
from .base_agent import BaseAgent, Task


class OCRAgent(BaseAgent):
    """Агент для распознавания текста (OCR)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("ocr_agent", config)
        self.model_path = config.get('models_path', '/app/models')
        self.reader: Optional[easyocr.Reader] = None
        self.languages = ['en', 'ru']  # Поддерживаемые языки
        
    async def _initialize_agent(self):
        """Инициализация OCRAgent"""
        self.logger.info("Инициализация OCRAgent")
        
        # Загрузка модели EasyOCR
        await self._load_model()
        
        self.logger.info("OCRAgent успешно инициализирован")
    
    async def _load_model(self):
        """Загрузка модели EasyOCR"""
        try:
            self.logger.info("Загрузка EasyOCR модели")
            
            # Инициализация EasyOCR
            self.reader = easyocr.Reader(
                self.languages,
                gpu=False,  # CPU-only
                model_storage_directory=self.model_path
            )
            
            self.logger.info("EasyOCR модель загружена успешно")
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели: {e}")
            raise
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Обработка задач OCR"""
        if task.task_type == "text_extraction":
            return await self._extract_text(task)
        elif task.task_type == "text_detection":
            return await self._detect_text_regions(task)
        elif task.task_type == "document_analysis":
            return await self._analyze_document(task)
        elif task.task_type == "table_extraction":
            return await self._extract_table(task)
        
        return {"status": "unknown_task_type"}
    
    async def _extract_text(self, task: Task) -> Dict[str, Any]:
        """Извлечение текста из изображения"""
        try:
            image_path = task.data.get("image_path")
            languages = task.data.get("languages", self.languages)
            detail = task.data.get("detail", 1)  # 0 - только текст, 1 - с координатами
            
            if not image_path or not os.path.exists(image_path):
                return {"status": "error", "error": "Файл изображения не найден"}
            
            self.logger.info(f"Извлечение текста из {image_path}")
            
            # Выполнение OCR
            results = self.reader.readtext(
                image_path,
                detail=detail,
                paragraph=False
            )
            
            # Обработка результатов
            extracted_texts = []
            full_text = ""
            confidence_scores = []
            
            for result in results:
                if detail == 1:
                    bbox, text, confidence = result
                    extracted_texts.append({
                        "text": text,
                        "confidence": confidence,
                        "bbox": bbox,
                        "position": {
                            "x": int(bbox[0][0]),
                            "y": int(bbox[0][1]),
                            "width": int(bbox[2][0] - bbox[0][0]),
                            "height": int(bbox[2][1] - bbox[0][1])
                        }
                    })
                    confidence_scores.append(confidence)
                else:
                    text = result
                    extracted_texts.append({"text": text})
                
                full_text += text + " "
            
            # Расчет средней уверенности
            avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
            
            return {
                "status": "success",
                "full_text": full_text.strip(),
                "extracted_texts": extracted_texts,
                "text_count": len(extracted_texts),
                "average_confidence": float(avg_confidence),
                "languages": languages,
                "image_path": image_path,
                "metadata": {
                    "extracted_at": datetime.now().isoformat(),
                    "model": "EasyOCR",
                    "detail_level": detail
                }
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка извлечения текста: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _detect_text_regions(self, task: Task) -> Dict[str, Any]:
        """Обнаружение областей с текстом"""
        try:
            image_path = task.data.get("image_path")
            
            if not image_path or not os.path.exists(image_path):
                return {"status": "error", "error": "Файл изображения не найден"}
            
            self.logger.info(f"Обнаружение текстовых областей в {image_path}")
            
            # Выполнение OCR с координатами
            results = self.reader.readtext(
                image_path,
                detail=1,
                paragraph=True  # Группировка в параграфы
            )
            
            # Обработка результатов
            text_regions = []
            
            for result in results:
                bbox, text, confidence = result
                
                # Расчет размеров и позиции
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                
                region = {
                    "text": text,
                    "confidence": confidence,
                    "bbox": bbox,
                    "position": {
                        "x": int(min(x_coords)),
                        "y": int(min(y_coords)),
                        "width": int(max(x_coords) - min(x_coords)),
                        "height": int(max(y_coords) - min(y_coords))
                    },
                    "center": {
                        "x": int(np.mean(x_coords)),
                        "y": int(np.mean(y_coords))
                    }
                }
                
                text_regions.append(region)
            
            return {
                "status": "success",
                "text_regions": text_regions,
                "region_count": len(text_regions),
                "image_path": image_path,
                "metadata": {
                    "detected_at": datetime.now().isoformat(),
                    "model": "EasyOCR"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка обнаружения текстовых областей: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _analyze_document(self, task: Task) -> Dict[str, Any]:
        """Анализ документа"""
        try:
            image_path = task.data.get("image_path")
            
            if not image_path or not os.path.exists(image_path):
                return {"status": "error", "error": "Файл изображения не найден"}
            
            self.logger.info(f"Анализ документа {image_path}")
            
            # Извлечение текста
            text_result = await self._extract_text(task)
            if text_result["status"] != "success":
                return text_result
            
            # Обнаружение областей
            regions_result = await self._detect_text_regions(task)
            if regions_result["status"] != "success":
                return regions_result
            
            # Анализ структуры документа
            analysis = await self._analyze_document_structure(regions_result["text_regions"])
            
            return {
                "status": "success",
                "full_text": text_result["full_text"],
                "text_regions": regions_result["text_regions"],
                "document_analysis": analysis,
                "image_path": image_path,
                "metadata": {
                    "analyzed_at": datetime.now().isoformat(),
                    "model": "EasyOCR"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа документа: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _analyze_document_structure(self, text_regions: List[Dict]) -> Dict[str, Any]:
        """Анализ структуры документа"""
        try:
            if not text_regions:
                return {"structure": "empty"}
            
            # Группировка по строкам
            lines = {}
            for region in text_regions:
                y = region["position"]["y"]
                line_key = y // 20  # Группировка по вертикальным позициям
                if line_key not in lines:
                    lines[line_key] = []
                lines[line_key].append(region)
            
            # Сортировка строк
            sorted_lines = []
            for line_key in sorted(lines.keys()):
                line_regions = lines[line_key]
                line_regions.sort(key=lambda r: r["position"]["x"])
                sorted_lines.append(line_regions)
            
            # Анализ структуры
            structure = {
                "line_count": len(sorted_lines),
                "total_regions": len(text_regions),
                "average_line_height": np.mean([
                    np.mean([r["position"]["height"] for r in line]) 
                    for line in sorted_lines
                ]) if sorted_lines else 0,
                "text_density": len(text_regions) / max(len(sorted_lines), 1)
            }
            
            # Определение возможных заголовков (больший шрифт)
            if text_regions:
                avg_height = np.mean([r["position"]["height"] for r in text_regions])
                headers = [r for r in text_regions if r["position"]["height"] > avg_height * 1.5]
                structure["possible_headers"] = len(headers)
                structure["header_texts"] = [h["text"] for h in headers[:5]]  # Первые 5
            
            return structure
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа структуры: {e}")
            return {"structure": "error", "error": str(e)}
    
    async def _extract_table(self, task: Task) -> Dict[str, Any]:
        """Извлечение таблицы из изображения"""
        try:
            image_path = task.data.get("image_path")
            
            if not image_path or not os.path.exists(image_path):
                return {"status": "error", "error": "Файл изображения не найден"}
            
            self.logger.info(f"Извлечение таблицы из {image_path}")
            
            # Обнаружение текстовых областей
            regions_result = await self._detect_text_regions(task)
            if regions_result["status"] != "success":
                return regions_result
            
            text_regions = regions_result["text_regions"]
            
            # Простое определение таблицы по выравниванию
            table_structure = await self._detect_table_structure(text_regions)
            
            return {
                "status": "success",
                "table_structure": table_structure,
                "text_regions": text_regions,
                "image_path": image_path,
                "metadata": {
                    "extracted_at": datetime.now().isoformat(),
                    "model": "EasyOCR"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка извлечения таблицы: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _detect_table_structure(self, text_regions: List[Dict]) -> Dict[str, Any]:
        """Определение структуры таблицы"""
        try:
            if not text_regions:
                return {"is_table": False}
            
            # Группировка по строкам
            lines = {}
            for region in text_regions:
                y = region["position"]["y"]
                line_key = y // 30  # Более широкие группы для строк таблицы
                if line_key not in lines:
                    lines[line_key] = []
                lines[line_key].append(region)
            
            # Сортировка строк
            sorted_lines = []
            for line_key in sorted(lines.keys()):
                line_regions = lines[line_key]
                line_regions.sort(key=lambda r: r["position"]["x"])
                sorted_lines.append(line_regions)
            
            # Анализ выравнивания колонок
            if len(sorted_lines) >= 2:
                # Определение колонок по X-координатам
                all_x_positions = []
                for line in sorted_lines:
                    for region in line:
                        all_x_positions.append(region["position"]["x"])
                
                # Группировка близких X-координат
                column_groups = []
                for x in sorted(all_x_positions):
                    found_group = False
                    for group in column_groups:
                        if abs(x - np.mean(group)) < 50:  # Порог для колонки
                            group.append(x)
                            found_group = True
                            break
                    if not found_group:
                        column_groups.append([x])
                
                # Определение, является ли это таблицей
                is_table = len(column_groups) >= 2 and len(sorted_lines) >= 2
                
                # Извлечение данных таблицы
                table_data = []
                for line in sorted_lines:
                    row_data = []
                    for region in line:
                        row_data.append({
                            "text": region["text"],
                            "confidence": region["confidence"],
                            "x": region["position"]["x"]
                        })
                    table_data.append(row_data)
                
                return {
                    "is_table": is_table,
                    "columns": len(column_groups),
                    "rows": len(sorted_lines),
                    "table_data": table_data,
                    "column_positions": [int(np.mean(group)) for group in column_groups]
                }
            
            return {"is_table": False, "reason": "insufficient_data"}
            
        except Exception as e:
            self.logger.error(f"Ошибка определения структуры таблицы: {e}")
            return {"is_table": False, "error": str(e)}
    
    async def _cleanup_agent(self):
        """Очистка ресурсов OCRAgent"""
        if self.reader:
            del self.reader
        
        self.logger.info("OCRAgent очищен")
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Получение информации о модели"""
        return {
            "model_name": "EasyOCR",
            "languages": self.languages,
            "loaded": self.reader is not None,
            "gpu_enabled": False  # CPU-only
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья агента"""
        return {
            "status": "healthy" if self.reader is not None else "error",
            "model_loaded": self.reader is not None,
            "languages": self.languages,
            "gpu_enabled": False
        }

