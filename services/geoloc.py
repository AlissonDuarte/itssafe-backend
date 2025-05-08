import math
from typing import List
from models import models

from shapely.geometry import MultiPoint
from shapely.geometry.polygon import Polygon
from shapely.ops import unary_union

from sqlalchemy.orm import Session

from sqlalchemy import func
from geoalchemy2 import WKTElement
from geoalchemy2.functions import ST_DWithin



from shapely.geometry import Polygon

from shapely.geometry import MultiPoint, Polygon
import math
from typing import List


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
        labels = [-1] * n  # Todos os pontos começam como "não visitados"
        cluster_id = 0

        for i in range(n):
            if labels[i] != -1:
                continue

            neighbors = self.region_query(points[i], points, eps)

            if len(neighbors) < min_samples:
                labels[i] = -1  # Marca como ruído
                continue

            cluster_id += 1
            labels[i] = cluster_id

            to_visit = neighbors[:]
            to_visit.remove(i)  # Remove o próprio ponto da lista de visitação
            while to_visit:
                current_point = to_visit.pop()

                if labels[current_point] == -1:
                    labels[current_point] = cluster_id 
                if labels[current_point] != 0:
                    continue

                new_neighbors = self.region_query(points[current_point], points, eps)
                if len(new_neighbors) >= min_samples:
                    to_visit.extend(new_neighbors)
                    to_visit = list(set(to_visit))  # Elimina duplicatas
                    labels[current_point] = cluster_id

        return labels

    def is_overlapping(self, new_polygon, clusters_polygons):
        for existing_polygon in clusters_polygons:
            if new_polygon.intersects(existing_polygon):  # Verifica se há interseção
                return True
        return False

    def simplify_polygon(self, polygon, tolerance=0.01):
        return polygon.simplify(tolerance, preserve_topology=True)

    def generate_geojson_cluster_polygons(self, points: List[List[float]], eps: float, min_samples: int, risk_level_filter: List[str] = []):
        labels = self.dbscan(points, eps, min_samples)

        clusters = {}
        for i, label in enumerate(labels):
            if label != -1:
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(points[i])

        geojson = []
        clusters_polygons = []

        for cluster_id, cluster_points in clusters.items():
            multipoint = MultiPoint(cluster_points)
            convex_hull = multipoint.convex_hull
            occurrence_count = len(cluster_points)

            if occurrence_count <= 10:
                continue
            elif occurrence_count > 10 and occurrence_count <=50:
                risk_level = "low"
            elif occurrence_count > 50 and occurrence_count <=100:
                risk_level = "medium"
            else:
                risk_level = "high"

            if risk_level_filter and risk_level in risk_level_filter:
                continue
            
            if isinstance(convex_hull, Polygon):
                simplified_polygon = self.simplify_polygon(convex_hull)

                # Verifica se há interseção com polígonos existentes
                overlapping = [p for p in clusters_polygons if p.intersects(simplified_polygon)]

                if overlapping:
                    # Une os polígonos sobrepostos com o novo
                    overlapping.append(simplified_polygon)
                    merged = unary_union(overlapping)

                    # Remove os antigos e adiciona o novo unificado
                    clusters_polygons = [p for p in clusters_polygons if not any(p.equals(o) for o in overlapping)]
                    clusters_polygons.append(merged)

                    geojson.append({
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": list(merged.exterior.coords)
                        },
                        "properties": {
                            "cluster_id": cluster_id,
                            "risk_level": risk_level,
                            "occurrence_count": occurrence_count
                        }
                    })
                else:
                    clusters_polygons.append(simplified_polygon)
                    geojson.append({
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": list(simplified_polygon.exterior.coords)
                        },
                        "properties": {
                            "cluster_id": cluster_id,
                            "risk_level": risk_level,
                            "occurrence_count": occurrence_count
                        }
                    })

            else:
                # Caso não forme um polígono (ex: apenas dois pontos)
                geojson.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": list(convex_hull.coords)
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
        data = [item.coordinates for item in results]
        return data
        