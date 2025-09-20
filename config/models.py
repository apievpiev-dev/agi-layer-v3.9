"""
Конфигурация моделей для AGI Layer v3.9 (CPU-only)
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """Конфигурация модели"""
    name: str
    type: str  # llm, vision, image_gen, ocr, embedding
    url: str
    filename: str
    size_mb: int
    dependencies: List[str]
    cpu_only: bool = True
    memory_required: int = 0  # MB


# Конфигурация всех CPU-only моделей
MODELS = {
    "stable_diffusion_1_5": ModelConfig(
        name="stable_diffusion_1_5",
        type="image_gen",
        url="https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.ckpt",
        filename="v1-5-pruned-emaonly.ckpt",
        size_mb=4200,
        dependencies=["torch", "diffusers", "transformers"],
        cpu_only=True,
        memory_required=2048
    ),
    
    "phi_2": ModelConfig(
        name="phi_2",
        type="llm",
        url="https://huggingface.co/microsoft/phi-2/resolve/main/pytorch_model.bin",
        filename="phi-2-pytorch_model.bin",
        size_mb=5600,
        dependencies=["torch", "transformers"],
        cpu_only=True,
        memory_required=1024
    ),
    
    "blip2": ModelConfig(
        name="blip2",
        type="vision",
        url="https://huggingface.co/Salesforce/blip2-opt-2.7b/resolve/main/pytorch_model.bin",
        filename="blip2-pytorch_model.bin",
        size_mb=5200,
        dependencies=["torch", "transformers", "sentencepiece"],
        cpu_only=True,
        memory_required=1536
    ),
    
    "easyocr": ModelConfig(
        name="easyocr",
        type="ocr",
        url="https://github.com/JaidedAI/EasyOCR/releases/download/v1.6.2/latin_g2.pth",
        filename="latin_g2.pth",
        size_mb=45,
        dependencies=["torch", "easyocr", "opencv-python"],
        cpu_only=True,
        memory_required=256
    ),
    
    "sentence_transformers": ModelConfig(
        name="sentence_transformers",
        type="embedding",
        url="https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/pytorch_model.bin",
        filename="all-MiniLM-L6-v2-pytorch_model.bin",
        size_mb=90,
        dependencies=["torch", "sentence-transformers"],
        cpu_only=True,
        memory_required=256
    )
}


def get_model_config(model_name: str) -> ModelConfig:
    """Получение конфигурации модели"""
    if model_name not in MODELS:
        raise ValueError(f"Модель {model_name} не найдена")
    return MODELS[model_name]


def get_models_by_type(model_type: str) -> List[ModelConfig]:
    """Получение моделей по типу"""
    return [model for model in MODELS.values() if model.type == model_type]


def get_all_models() -> Dict[str, ModelConfig]:
    """Получение всех моделей"""
    return MODELS


def get_total_size_mb() -> int:
    """Общий размер всех моделей в MB"""
    return sum(model.size_mb for model in MODELS.values())


def get_total_memory_required() -> int:
    """Общая требуемая память в MB"""
    return sum(model.memory_required for model in MODELS.values())


# Настройки для конкретных агентов
AGENT_MODELS = {
    "image_agent": ["stable_diffusion_1_5"],
    "text_agent": ["phi_2"],
    "vision_agent": ["blip2"],
    "ocr_agent": ["easyocr"],
    "embedding_agent": ["sentence_transformers"]
}

