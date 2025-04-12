import gpxpy
import matplotlib.pyplot as plt
import contextily as ctx
from django.conf import settings
from matplotlib_scalebar.scalebar import ScaleBar
import os
from shapely.geometry import LineString, Point
import geopandas as gpd
import geopy.distance
from typing import List, Tuple


class GPXVisualizer:
    def __init__(self, gpx_file: str, output_file: str = None):
        self.gpx_file = gpx_file
        self.output_file = (
            output_file
            if output_file
            else os.path.join(
                settings.MEDIA_ROOT, "gpx", gpx_file.split(".")[0] + ".png"
            )
        )
        self.points: List[Tuple[float, float]] = []  # Список точок (lon, lat)
        self.km_markers: List[Tuple[float, float, float]] = (
            []
        )  # Список маркерів (lat, lon, dist)
        self.total_distance: float = 0.0  # Загальна відстань
        self.gdf_track = None
        self.gdf_markers = None
        self.gdf_track_webmerc = None
        self.gdf_markers_webmerc = None

    @staticmethod
    def calculate_distance(
        point1: Tuple[float, float], point2: Tuple[float, float]
    ) -> float:
        """Обчислює відстань між двома точками у форматі (lat, lon) в кілометрах"""
        return geopy.distance.geodesic(point1, point2).kilometers

    def parse_gpx(self) -> None:
        """Парсить GPX-файл і збирає точки маршруту з треків або маршрутів"""
        try:
            with open(self.gpx_file, "r") as f:
                gpx = gpxpy.parse(f)

                # Спочатку спробуємо отримати точки з треків
                for track in gpx.tracks:
                    for segment in track.segments:
                        for point in segment.points:
                            self.points.append(
                                (point.longitude, point.latitude)
                            )

                # Якщо точок у треках не знайдено, спробуємо отримати точки з маршрутів
                if not self.points and gpx.routes:
                    for route in gpx.routes:
                        for point in route.points:
                            self.points.append(
                                (point.longitude, point.latitude)
                            )

                if not self.points:
                    raise ValueError("Не знайдено точок у GPX файлі.")
        except FileNotFoundError:
            raise FileNotFoundError(f"Файл '{self.gpx_file}' не знайдено.")
        except Exception as e:
            raise RuntimeError(f"Помилка при парсингу GPX-файлу: {e}")

    def create_kilometer_markers(self, step: float = 1.0) -> None:
        """Створює кілометрові маркери вздовж маршруту"""
        if not self.points:
            raise ValueError(
                "Список точок маршруту порожній. Спочатку виконайте parse_gpx()."
            )

        markers = [(self.points[0][1], self.points[0][0], 0)]
        total_distance, last_marker_distance = 0.0, 0.0

        for i in range(1, len(self.points)):
            prev_point = (
                self.points[i - 1][1],
                self.points[i - 1][0],
            )  # (lat, lon)
            current_point = (
                self.points[i][1],
                self.points[i][0],
            )  # (lat, lon)
            segment_distance = self.calculate_distance(
                prev_point, current_point
            )
            total_distance += segment_distance

            while total_distance - last_marker_distance >= step:
                ratio = (
                    step
                    - (
                        total_distance
                        - last_marker_distance
                        - segment_distance
                    )
                ) / segment_distance
                marker_lat = prev_point[0] + ratio * (
                    current_point[0] - prev_point[0]
                )
                marker_lon = prev_point[1] + ratio * (
                    current_point[1] - prev_point[1]
                )
                last_marker_distance += step
                markers.append(
                    (marker_lat, marker_lon, round(last_marker_distance, 1))
                )

        markers.append(
            (self.points[-1][1], self.points[-1][0], round(total_distance, 1))
        )
        self.km_markers = markers
        self.total_distance = total_distance

    def prepare_geodataframes(self) -> None:
        """Готує геодатафрейми для маршруту та маркерів"""
        track_line = LineString(self.points)
        self.gdf_track = gpd.GeoDataFrame(
            geometry=[track_line], crs="EPSG:4326"
        )
        self.gdf_track_webmerc = self.gdf_track.to_crs(epsg=3857)

        marker_points = [Point(m[1], m[0]) for m in self.km_markers]
        marker_distances = [m[2] for m in self.km_markers]
        self.gdf_markers = gpd.GeoDataFrame(
            {"distance": marker_distances},
            geometry=marker_points,
            crs="EPSG:4326",
        )
        self.gdf_markers_webmerc = self.gdf_markers.to_crs(epsg=3857)

    def _generate_plot(self) -> None:
        """Генерує фігуру з маршрутом та маркерами"""
        fig, ax = plt.subplots(figsize=(12, 10))
        self.gdf_track_webmerc.plot(ax=ax, color="red", linewidth=3)

        for idx, row in self.gdf_markers_webmerc.iterrows():
            distance = row["distance"]
            if idx == 0:
                label, color, markersize = "Старт", "green", 100
            elif idx == len(self.gdf_markers_webmerc) - 1:
                label, color, markersize = (
                    f"Фініш ({distance} км)",
                    "blue",
                    100,
                )
            elif distance.is_integer():
                label, color, markersize = f"{int(distance)} км", "purple", 70
            else:
                continue

            ax.scatter(
                row.geometry.x,
                row.geometry.y,
                s=markersize,
                color=color,
                zorder=5,
            )
            ax.annotate(
                label,
                (row.geometry.x, row.geometry.y),
                fontsize=9,
                fontweight="bold",
                color="black",
                ha="center",
                va="center",
                bbox=dict(
                    boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8
                ),
                xytext=(0, 10),
                textcoords="offset points",
                zorder=6,
            )

        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
        bounds = self.gdf_track_webmerc.geometry.total_bounds
        buffer = max((bounds[2] - bounds[0]), (bounds[3] - bounds[1])) * 0.05
        ax.set_xlim([bounds[0] - buffer, bounds[2] + buffer])
        ax.set_ylim([bounds[1] - buffer, bounds[3] + buffer])
        ax.set_axis_off()
        ax.add_artist(ScaleBar(dx=1.0, location="lower right"))
        ax.set_title(
            f"CrossRunChe GPX Track: {os.path.basename(self.gpx_file)}\n"
            f"Загальна відстань: {self.total_distance:.2f} км",
            fontsize=12,
        )
        plt.savefig(self.output_file, bbox_inches="tight", dpi=300)
        plt.close()
        print(f"Карту збережено як '{self.output_file}'")
        print(f"Загальна відстань: {self.total_distance:.2f} км")

    def visualize(self, step: float = 1.0) -> None:
        """Головний метод для візуалізації маршруту"""
        self.parse_gpx()
        self.create_kilometer_markers(step=step)
        self.prepare_geodataframes()
        self._generate_plot()
