import asyncio

from aiogram import types
from celery import shared_task

from robot.services.gpx_vizualizer import GPXVisualizer


@shared_task()
def visualize_gpx(
    gpx_file: str, output_file: str = None) -> None:
    """Функція для візуалізації маршруту з GPX-файлу"""
    try:
        visualizer = GPXVisualizer(gpx_file, output_file)
        visualizer.visualize()
    except Exception as e:
        print(f"Помилка при візуалізації маршруту: {e}", flush=True)
        return
