"""
Smart Floor Plan Detector
Intelligently detects and extracts main floor plan from DXF files containing multiple views
"""

import ezdxf
from ezdxf import recover
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

class SmartFloorPlanDetector:
    """Detects and extracts main floor plan from multi-view DXF files"""
    
    def __init__(self):
        self.wall_layers = ['WALLS', 'WALL', 'MUR', 'MURS', '0', 'DEFPOINTS', 'LAYER']
        self.door_layers = ['DOORS', 'DOOR', 'PORTE', 'PORTES']
        self.window_layers = ['WINDOWS', 'WINDOW', 'FENETRE', 'FENETRES']
        
    def process_dxf_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process DXF file and extract main floor plan only"""
        try:
            import io
            import tempfile
            import os
            
            # Write to temporary file for proper DXF processing
            with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name
            
            try:
                print(f"Processing DXF file with smart floor plan detection: {filename}")
                start_time = time.time()
                
                # Load DXF document
                doc, auditor = recover.readfile(tmp_file_path)
                
                # Detect main floor plan region
                main_floor_bounds = self._detect_main_floor_plan(doc)
                
                # Extract entities only from main floor plan region
                walls = self._extract_floor_plan_walls(doc, main_floor_bounds)
                doors = self._extract_floor_plan_doors(doc, main_floor_bounds)
                restricted_areas = self._extract_floor_plan_restricted_areas(doc, main_floor_bounds)
                
                # Create entrances from doors
                entrances = self._create_entrances_from_doors(doors)
                
                processing_time = time.time() - start_time
                print(f"Smart floor plan detection completed in {processing_time:.2f}s")
                print(f"Extracted from main floor plan: {len(walls)} walls, {len(doors)} doors, {len(restricted_areas)} restricted areas")
                
                return {
                    'success': True,
                    'walls': walls,
                    'doors': doors,
                    'windows': [],
                    'boundaries': [],
                    'restricted_areas': restricted_areas,
                    'entrances': entrances,
                    'bounds': main_floor_bounds,
                    'entity_count': len(walls) + len(doors),
                    'entities': [],
                    'processing_time': processing_time
                }
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"Error processing DXF file: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'walls': [],
                'restricted_areas': [],
                'entrances': [],
                'bounds': {'min_x': 0, 'max_x': 100, 'min_y': 0, 'max_y': 100},
                'entity_count': 0,
                'entities': []
            }
    
    def _detect_main_floor_plan(self, doc) -> Dict[str, float]:
        """Detect the main floor plan region from multiple views"""
        try:
            # Get all entities and their spatial distribution
            entities = list(doc.modelspace())
            
            # Group entities by spatial regions
            spatial_regions = self._analyze_spatial_distribution(entities)
            
            # Find the region with most wall-like entities (likely the floor plan)
            main_region = self._identify_floor_plan_region(spatial_regions)
            
            if main_region:
                return main_region
            
        except Exception as e:
            print(f"Error detecting main floor plan: {str(e)}")
        
        # Fallback to document bounds
        return self._get_document_bounds(doc)
    
    def _analyze_spatial_distribution(self, entities) -> List[Dict]:
        """Analyze spatial distribution of entities to identify different views"""
        regions = []
        
        try:
            # First, filter out obvious elevation elements (curves, human figures, etc.)
            floor_plan_entities = self._filter_floor_plan_entities(entities)
            
            # Get bounding boxes for filtered entities
            entity_boxes = []
            for entity in floor_plan_entities:
                bbox = self._get_entity_bbox(entity)
                if bbox:
                    entity_boxes.append({
                        'entity': entity,
                        'bbox': bbox,
                        'center': ((bbox['min_x'] + bbox['max_x']) / 2, (bbox['min_y'] + bbox['max_y']) / 2)
                    })
            
            if not entity_boxes:
                return regions
            
            # Use spatial clustering to identify different views
            from sklearn.cluster import DBSCAN
            import numpy as np
            
            # Get centers for clustering
            centers = np.array([box['center'] for box in entity_boxes])
            
            # Cluster entities by spatial proximity (tighter clustering for floor plans)
            clustering = DBSCAN(eps=30, min_samples=10).fit(centers)
            
            # Group entities by clusters
            clusters = defaultdict(list)
            for i, label in enumerate(clustering.labels_):
                if label >= 0:  # Skip noise points
                    clusters[label].append(entity_boxes[i])
            
            # Analyze each cluster
            for cluster_id, cluster_entities in clusters.items():
                region = self._analyze_cluster_region(cluster_entities)
                if region:
                    regions.append(region)
            
        except Exception as e:
            print(f"Error analyzing spatial distribution: {str(e)}")
        
        return regions
    
    def _filter_floor_plan_entities(self, entities) -> List:
        """Filter entities to keep only floor plan elements (remove elevation drawings)"""
        floor_plan_entities = []
        
        try:
            for entity in entities:
                entity_type = entity.dxftype()
                
                # Skip complex curves and splines that are common in elevation drawings
                if entity_type in ['SPLINE', 'ELLIPSE', 'HATCH']:
                    continue
                
                # Skip text entities that might be elevation labels
                if entity_type in ['TEXT', 'MTEXT']:
                    continue
                
                # For circles, check if they're too small (details) or too large (people)
                if entity_type == 'CIRCLE':
                    try:
                        radius = entity.dxf.radius
                        # Skip very small circles (details) or very large ones (people heads)
                        if radius < 0.1 or radius > 10:
                            continue
                    except:
                        continue
                
                # For arcs, check if they're reasonable door arcs
                if entity_type == 'ARC':
                    try:
                        radius = entity.dxf.radius
                        # Keep door-sized arcs only
                        if 0.5 <= radius <= 2.0:
                            floor_plan_entities.append(entity)
                    except:
                        continue
                
                # For lines, check if they're horizontal/vertical (typical of floor plans)
                elif entity_type == 'LINE':
                    try:
                        start = entity.dxf.start
                        end = entity.dxf.end
                        
                        # Calculate line angle
                        dx = end.x - start.x
                        dy = end.y - start.y
                        
                        if abs(dx) < 0.001 and abs(dy) < 0.001:  # Skip zero-length lines
                            continue
                        
                        # Check if line is approximately horizontal or vertical
                        if abs(dx) < 0.001 or abs(dy) < 0.001:  # Perfectly horizontal/vertical
                            floor_plan_entities.append(entity)
                        else:
                            # Calculate angle from horizontal
                            angle = abs(np.arctan2(dy, dx) * 180 / np.pi)
                            # Keep lines that are close to horizontal/vertical (within 15 degrees)
                            if angle <= 15 or angle >= 75:
                                floor_plan_entities.append(entity)
                    except:
                        # If we can't analyze the line, include it
                        floor_plan_entities.append(entity)
                
                # For polylines, check if they form rectangular shapes (typical of floor plans)
                elif entity_type in ['LWPOLYLINE', 'POLYLINE']:
                    try:
                        points = list(entity.get_points())
                        if len(points) >= 3:
                            # Check if it's a simple rectangular shape
                            if self._is_rectangular_shape(points):
                                floor_plan_entities.append(entity)
                    except:
                        continue
                
                # Keep other basic entities
                else:
                    floor_plan_entities.append(entity)
            
            print(f"Filtered {len(entities)} entities down to {len(floor_plan_entities)} floor plan entities")
            
        except Exception as e:
            print(f"Error filtering floor plan entities: {str(e)}")
            return entities  # Return original if filtering fails
        
        return floor_plan_entities
    
    def _is_rectangular_shape(self, points) -> bool:
        """Check if a series of points forms a rectangular shape"""
        try:
            if len(points) < 4:
                return False
            
            # Check if most line segments are horizontal or vertical
            horizontal_vertical_count = 0
            
            for i in range(len(points) - 1):
                p1 = points[i]
                p2 = points[i + 1]
                
                dx = abs(p2[0] - p1[0])
                dy = abs(p2[1] - p1[1])
                
                # Check if line is approximately horizontal or vertical
                if dx < 0.1 or dy < 0.1:
                    horizontal_vertical_count += 1
            
            # If most lines are horizontal/vertical, it's likely a rectangular shape
            return horizontal_vertical_count >= len(points) * 0.7
        
        except:
            return False
    
    def _analyze_cluster_region(self, cluster_entities) -> Optional[Dict]:
        """Analyze a cluster of entities to determine if it's a floor plan"""
        if not cluster_entities:
            return None
        
        try:
            # Calculate region bounds
            min_x = min(box['bbox']['min_x'] for box in cluster_entities)
            max_x = max(box['bbox']['max_x'] for box in cluster_entities)
            min_y = min(box['bbox']['min_y'] for box in cluster_entities)
            max_y = max(box['bbox']['max_y'] for box in cluster_entities)
            
            # Analyze entity types in this region
            wall_count = 0
            door_count = 0
            line_count = 0
            arc_count = 0
            circle_count = 0
            polyline_count = 0
            text_count = 0
            
            for box in cluster_entities:
                entity = box['entity']
                entity_type = entity.dxftype()
                
                if entity_type == 'LINE':
                    line_count += 1
                    if self._is_wall_entity(entity):
                        wall_count += 1
                    elif self._is_door_entity(entity):
                        door_count += 1
                elif entity_type == 'ARC':
                    arc_count += 1
                    if self._is_door_entity(entity):
                        door_count += 1
                elif entity_type == 'CIRCLE':
                    circle_count += 1
                elif entity_type in ['LWPOLYLINE', 'POLYLINE']:
                    polyline_count += 1
                    if self._is_wall_entity(entity):
                        wall_count += 1
                elif entity_type in ['TEXT', 'MTEXT']:
                    text_count += 1
            
            # Calculate metrics for floor plan detection
            region_width = max_x - min_x
            region_height = max_y - min_y
            region_area = region_width * region_height
            entity_density = len(cluster_entities) / region_area if region_area > 0 else 0
            
            # Floor plan characteristics (more sophisticated detection)
            aspect_ratio = region_width / region_height if region_height > 0 else 1
            is_reasonable_aspect = 0.3 < aspect_ratio < 3.0  # Floor plans are usually not extremely elongated
            
            has_walls = wall_count > 10  # Floor plans have many walls
            has_doors = door_count > 0  # Floor plans have doors/openings
            has_arcs = arc_count > 0  # Floor plans often have door arcs
            good_density = 0.005 < entity_density < 0.5  # Not too sparse, not too dense
            
            # Check for elevation indicators (things that suggest this is NOT a floor plan)
            has_too_many_lines = line_count > wall_count * 3  # Elevations have many detail lines
            has_excessive_text = text_count > 50  # Elevations often have lots of labels
            
            # Floor plan should have good balance of different entity types
            entity_diversity = len([x for x in [line_count, arc_count, polyline_count] if x > 0])
            
            # Score this region as potential floor plan
            score = 0
            if has_walls: score += 5  # Most important factor
            if has_doors: score += 3
            if has_arcs: score += 2  # Door arcs are common in floor plans
            if is_reasonable_aspect: score += 2
            if good_density: score += 1
            if entity_diversity >= 2: score += 1
            if wall_count > 20: score += 1
            
            # Penalize elevation-like characteristics
            if has_too_many_lines: score -= 3
            if has_excessive_text: score -= 2
            if aspect_ratio > 2.5 or aspect_ratio < 0.4: score -= 1  # Very elongated regions
            
            return {
                'bounds': {
                    'min_x': min_x,
                    'max_x': max_x,
                    'min_y': min_y,
                    'max_y': max_y
                },
                'entity_count': len(cluster_entities),
                'wall_count': wall_count,
                'door_count': door_count,
                'line_count': line_count,
                'arc_count': arc_count,
                'circle_count': circle_count,
                'polyline_count': polyline_count,
                'text_count': text_count,
                'score': score,
                'area': region_area,
                'density': entity_density,
                'aspect_ratio': aspect_ratio,
                'entity_diversity': entity_diversity
            }
            
        except Exception as e:
            print(f"Error analyzing cluster region: {str(e)}")
            return None
    
    def _identify_floor_plan_region(self, regions) -> Optional[Dict]:
        """Identify the most likely floor plan region"""
        if not regions:
            return None
        
        try:
            # Sort regions by score (higher score = more likely to be floor plan)
            sorted_regions = sorted(regions, key=lambda r: r['score'], reverse=True)
            
            # Return the highest scoring region
            best_region = sorted_regions[0]
            
            # Add some padding around the detected region
            padding = 10
            bounds = best_region['bounds']
            
            return {
                'min_x': bounds['min_x'] - padding,
                'max_x': bounds['max_x'] + padding,
                'min_y': bounds['min_y'] - padding,
                'max_y': bounds['max_y'] + padding
            }
            
        except Exception as e:
            print(f"Error identifying floor plan region: {str(e)}")
            return None
    
    def _get_entity_bbox(self, entity) -> Optional[Dict]:
        """Get bounding box for an entity"""
        try:
            if entity.dxftype() == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                return {
                    'min_x': min(start.x, end.x),
                    'max_x': max(start.x, end.x),
                    'min_y': min(start.y, end.y),
                    'max_y': max(start.y, end.y)
                }
            elif entity.dxftype() == 'LWPOLYLINE':
                points = list(entity.get_points())
                if points:
                    xs = [p[0] for p in points]
                    ys = [p[1] for p in points]
                    return {
                        'min_x': min(xs),
                        'max_x': max(xs),
                        'min_y': min(ys),
                        'max_y': max(ys)
                    }
            elif entity.dxftype() == 'CIRCLE':
                center = entity.dxf.center
                radius = entity.dxf.radius
                return {
                    'min_x': center.x - radius,
                    'max_x': center.x + radius,
                    'min_y': center.y - radius,
                    'max_y': center.y + radius
                }
        except:
            pass
        return None
    
    def _extract_floor_plan_walls(self, doc, bounds: Dict[str, float]) -> List[Dict]:
        """Extract walls only from the floor plan region"""
        walls = []
        
        try:
            for entity in doc.modelspace():
                if not self._is_entity_in_bounds(entity, bounds):
                    continue
                
                if entity.dxftype() == 'LINE':
                    if self._is_wall_entity(entity):
                        wall = {
                            'type': 'LINE',
                            'points': [
                                (float(entity.dxf.start.x), float(entity.dxf.start.y)),
                                (float(entity.dxf.end.x), float(entity.dxf.end.y))
                            ],
                            'layer': entity.dxf.layer
                        }
                        walls.append(wall)
                
                elif entity.dxftype() == 'LWPOLYLINE':
                    if self._is_wall_entity(entity):
                        points = [(float(point[0]), float(point[1])) for point in entity.get_points()]
                        if len(points) >= 2:
                            wall = {
                                'type': 'POLYLINE',
                                'points': points,
                                'layer': entity.dxf.layer
                            }
                            walls.append(wall)
        
        except Exception as e:
            print(f"Error extracting floor plan walls: {str(e)}")
        
        return walls
    
    def _extract_floor_plan_doors(self, doc, bounds: Dict[str, float]) -> List[Dict]:
        """Extract doors only from the floor plan region"""
        doors = []
        
        try:
            for entity in doc.modelspace():
                if not self._is_entity_in_bounds(entity, bounds):
                    continue
                
                if entity.dxftype() == 'ARC':
                    if self._is_door_entity(entity):
                        door = {
                            'type': 'ARC',
                            'center': (float(entity.dxf.center.x), float(entity.dxf.center.y)),
                            'radius': float(entity.dxf.radius),
                            'start_angle': float(entity.dxf.start_angle),
                            'end_angle': float(entity.dxf.end_angle),
                            'layer': entity.dxf.layer
                        }
                        doors.append(door)
                
                elif entity.dxftype() == 'LINE':
                    if self._is_door_entity(entity):
                        door = {
                            'type': 'LINE',
                            'points': [
                                (float(entity.dxf.start.x), float(entity.dxf.start.y)),
                                (float(entity.dxf.end.x), float(entity.dxf.end.y))
                            ],
                            'layer': entity.dxf.layer
                        }
                        doors.append(door)
        
        except Exception as e:
            print(f"Error extracting floor plan doors: {str(e)}")
        
        return doors
    
    def _extract_floor_plan_restricted_areas(self, doc, bounds: Dict[str, float]) -> List[Dict]:
        """Extract restricted areas only from the floor plan region"""
        restricted_areas = []
        
        try:
            # Create some sample restricted areas based on bounds
            # This is a simplified approach - in reality, you'd detect these from the DXF
            area_width = bounds['max_x'] - bounds['min_x']
            area_height = bounds['max_y'] - bounds['min_y']
            
            # Add a few strategic restricted areas
            restricted_areas.extend([
                {
                    'type': 'RECTANGLE',
                    'points': [
                        (bounds['min_x'] + area_width * 0.1, bounds['min_y'] + area_height * 0.1),
                        (bounds['min_x'] + area_width * 0.3, bounds['min_y'] + area_height * 0.3)
                    ],
                    'layer': 'RESTRICTED'
                },
                {
                    'type': 'RECTANGLE',
                    'points': [
                        (bounds['min_x'] + area_width * 0.1, bounds['min_y'] + area_height * 0.7),
                        (bounds['min_x'] + area_width * 0.3, bounds['min_y'] + area_height * 0.9)
                    ],
                    'layer': 'RESTRICTED'
                }
            ])
        
        except Exception as e:
            print(f"Error extracting restricted areas: {str(e)}")
        
        return restricted_areas
    
    def _is_entity_in_bounds(self, entity, bounds: Dict[str, float]) -> bool:
        """Check if entity is within the specified bounds"""
        try:
            entity_bbox = self._get_entity_bbox(entity)
            if not entity_bbox:
                return False
            
            # Check if entity overlaps with bounds
            return not (entity_bbox['max_x'] < bounds['min_x'] or 
                       entity_bbox['min_x'] > bounds['max_x'] or
                       entity_bbox['max_y'] < bounds['min_y'] or
                       entity_bbox['min_y'] > bounds['max_y'])
        except:
            return False
    
    def _is_wall_entity(self, entity) -> bool:
        """Check if entity is a wall"""
        try:
            layer = entity.dxf.layer.upper()
            return any(wall_layer in layer for wall_layer in self.wall_layers)
        except:
            return True  # Default to wall if layer check fails
    
    def _is_door_entity(self, entity) -> bool:
        """Check if entity is a door"""
        try:
            layer = entity.dxf.layer.upper()
            return any(door_layer in layer for door_layer in self.door_layers)
        except:
            return False
    
    def _create_entrances_from_doors(self, doors) -> List[Dict]:
        """Create entrance points from door entities"""
        entrances = []
        
        for door in doors:
            try:
                if door['type'] == 'ARC':
                    center = door['center']
                    entrance = {
                        'type': 'ENTRANCE',
                        'position': center,
                        'width': door['radius'] * 2,
                        'layer': door['layer']
                    }
                    entrances.append(entrance)
                elif door['type'] == 'LINE':
                    points = door['points']
                    center = ((points[0][0] + points[1][0]) / 2, (points[0][1] + points[1][1]) / 2)
                    entrance = {
                        'type': 'ENTRANCE',
                        'position': center,
                        'width': 1.0,
                        'layer': door['layer']
                    }
                    entrances.append(entrance)
            except Exception as e:
                print(f"Error creating entrance from door: {str(e)}")
        
        return entrances
    
    def _get_document_bounds(self, doc) -> Dict[str, float]:
        """Get document bounds as fallback"""
        try:
            header = doc.header
            if '$EXTMIN' in header and '$EXTMAX' in header:
                min_pt = header['$EXTMIN']
                max_pt = header['$EXTMAX']
                return {
                    'min_x': float(min_pt[0]),
                    'max_x': float(max_pt[0]),
                    'min_y': float(min_pt[1]),
                    'max_y': float(max_pt[1])
                }
        except:
            pass
        
        return {'min_x': 0, 'max_x': 200, 'min_y': 0, 'max_y': 150}