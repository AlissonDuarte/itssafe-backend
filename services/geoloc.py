from typing import List
from shapely.geometry import MultiPoint, Polygon, Point
import math
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2 import WKTElement
from geoalchemy2.functions import ST_DWithin
from models import models

class ClusteringResult:
    def __init__(self):
        return

    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371  # Raio da Terra em km
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c 

    def region_query(self, point, points, eps):
        neighbors = []
        for i, p in enumerate(points):
            if self.haversine(point[0], point[1], p[0], p[1]) <= eps:
                neighbors.append(i)
        return neighbors

    def dbscan(self, points: List[List[float]], eps: float, min_samples: int):
        n = len(points)
        labels = [-1] * n
        cluster_id = 0

        for i in range(n):
            if labels[i] != -1:
                continue

            neighbors = self.region_query(points[i], points, eps)

            if len(neighbors) < min_samples:
                labels[i] = -1
                continue

            cluster_id += 1
            labels[i] = cluster_id

            to_visit = neighbors[:]
            to_visit.remove(i)
            while to_visit:
                current_point = to_visit.pop()

                if labels[current_point] == -1:
                    labels[current_point] = cluster_id 
                if labels[current_point] != 0:
                    continue

                new_neighbors = self.region_query(points[current_point], points, eps)
                if len(new_neighbors) >= min_samples:
                    to_visit.extend(new_neighbors)
                    to_visit = list(set(to_visit))
                    labels[current_point] = cluster_id

        return labels

    def is_significantly_overlapping(self, new_polygon, existing_polygons, overlap_threshold=0.3):
        """Verifica se há sobreposição significativa (acima do threshold)"""
        for existing in existing_polygons:
            intersection_area = new_polygon.intersection(existing).area
            smaller_area = min(new_polygon.area, existing.area)
            if smaller_area > 0 and (intersection_area / smaller_area) > overlap_threshold:
                return True
        return False

    def simplify_polygon(self, polygon, tolerance=0.01):
        return polygon.simplify(tolerance, preserve_topology=True)

    def generate_geojson_cluster_polygons(self, points: List[List[float]], eps: float, min_samples: int):
        if not points:
            return []

        labels = self.dbscan(points, eps, min_samples)

        # Agrupa pontos por cluster
        clusters = {}
        for i, label in enumerate(labels):
            if label != -1:
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(points[i])

        # Ordena clusters por tamanho (maiores primeiro)
        sorted_clusters = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)

        geojson = []
        clusters_polygons = []

        for cluster_id, cluster_points in sorted_clusters:
            if len(cluster_points) < 3:  # Mínimo 3 pontos para formar um polígono
                # Cria um buffer ao redor do ponto ou par de pontos
                if len(cluster_points) == 1:
                    center = Point(cluster_points[0])
                    polygon = center.buffer(0.0001)  # Pequeno buffer (~11 metros)
                else:
                    multipoint = MultiPoint(cluster_points)
                    polygon = multipoint.convex_hull.buffer(0.0001)
            else:
                multipoint = MultiPoint(cluster_points)
                polygon = multipoint.convex_hull

            occurrence_count = len(cluster_points)

            if occurrence_count <= 10:
                risk_level = "low"
            elif occurrence_count <= 30:
                risk_level = "medium"
            else:
                risk_level = "high"

            simplified_polygon = self.simplify_polygon(polygon)

            # Verifica sobreposição significativa com clusters existentes
            if not self.is_significantly_overlapping(simplified_polygon, clusters_polygons):
                if isinstance(simplified_polygon, Polygon):
                    geojson.append({
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [list(simplified_polygon.exterior.coords)]
                        },
                        "properties": {
                            "cluster_id": cluster_id,
                            "risk_level": risk_level,
                            "occurrence_count": occurrence_count
                        }
                    })
                    clusters_polygons.append(simplified_polygon)
                elif isinstance(simplified_polygon, Point):
                    geojson.append({
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [simplified_polygon.x, simplified_polygon.y]
                        },
                        "properties": {
                            "cluster_id": cluster_id,
                            "risk_level": risk_level,
                            "occurrence_count": occurrence_count
                        }
                    })

        return geojson

class Scans():
    def __init__(self, db:Session):
        self.db = db

    def user_location(self, base_location: list, radius_meters: float = 1000, raw_occurrence_type: list = [], raw_shifts: list = []):
        latitude, longitude = base_location

        user_location = WKTElement(f'POINT({latitude} {longitude})', srid=4326)

        query = self.db.query(models.Occurrence).filter(
            ST_DWithin(
                func.ST_GeographyFromText(func.ST_AsText(models.Occurrence.local)),
                user_location,
                radius_meters
            )
        )
        
        if raw_occurrence_type:
            occurrence_options = [ocr.value for ocr in models.Occurrence.OccurrenceType]
            occurrence_type = [occurrence for occurrence in raw_occurrence_type if occurrence in occurrence_options]
            if occurrence_type:
                query = query.filter(models.Occurrence.type.in_(occurrence_type))

        if raw_shifts:
            shifts_options = [shf.value for shf in models.Occurrence.ShiftOptions]
            shifts = [shift for shift in raw_shifts if shift in shifts_options]
            if shifts:
                query = query.filter(models.Occurrence.shift.in_(shifts))

        results = query.all()
        data = [item.coordinates for item in results if hasattr(item, 'coordinates') and item.coordinates]
        return data