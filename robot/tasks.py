from celery import shared_task

from robot.services.gpx_vizualizer import GPXVisualizer


@shared_task(bind=True)
def visualize_gpx(self, gpx_file: str, output_file: str = None):
    """Функція для візуалізації маршруту з GPX-файлу"""
    visualizer = GPXVisualizer(gpx_file, output_file)
    visualizer.visualize()
    return visualizer.output_file
