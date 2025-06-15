# height_map.py - ZOPTYMALIZOWANA WERSJA
import numpy as np
from glm import vec3, vec4
import time
from collections import defaultdict


class HeightMap:
    def __init__(self, x_min, x_max, y_min, y_max, resolution=0.5):
        """
        Tworzy mapę wysokości dla danego obszaru

        Args:
            x_min, x_max, y_min, y_max: granice obszaru
            resolution: rozdzielczość mapy (im mniejsza wartość, tym więcej próbek)
        """
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.resolution = resolution

        # Oblicz wymiary siatki
        self.width = int((x_max - x_min) / resolution) + 1
        self.height = int((y_max - y_min) / resolution) + 1

        # Domyślna wysokość (grunt)
        self.default_height = 1.0

        # Mapa wysokości - początkowo wypełniona domyślną wartością
        self.heights = np.full((self.height, self.width), self.default_height, dtype=np.float32)

        print(f"Utworzono mapę wysokości {self.width}x{self.height} (rozdzielczość: {resolution})")

    def generate_from_scene(self, scene, model_matrix, max_height=50.0):
        """
        Generuje mapę wysokości na podstawie sceny 3D - WERSJA ZOPTYMALIZOWANA
        """
        print("Generowanie mapy wysokości (zoptymalizowane)...")
        start_time = time.time()

        triangles = self._extract_triangles_from_scene(scene, model_matrix)
        print(f"Wyekstraktowano {len(triangles)} trójkątów ze sceny")

        # OPTYMALIZACJA 1: Spatial partitioning - podziel trójkąty na sektory
        print("Tworzenie spatial hash...")
        spatial_hash = self._create_spatial_hash(triangles)

        # OPTYMALIZACJA 2: Przetwarzaj w blokach z progress
        block_size = 100
        total_points = self.width * self.height
        processed = 0

        # Dla każdego punktu na siatce
        for gy in range(self.height):
            for gx_start in range(0, self.width, block_size):
                gx_end = min(gx_start + block_size, self.width)

                # Przetwórz blok punktów
                for gx in range(gx_start, gx_end):
                    # Przelicz współrzędne siatki na współrzędne świata
                    world_x = self.x_min + gx * self.resolution
                    world_y = self.y_min + gy * self.resolution

                    # OPTYMALIZACJA 3: Sprawdzaj tylko trójkąty w pobliskim sektorze
                    nearby_triangles = self._get_nearby_triangles(spatial_hash, world_x, world_y)

                    # Znajdź najwyższą wysokość w tym punkcie
                    max_z = self.default_height

                    # Sprawdź kolizję tylko z pobliskimi trójkątami
                    for tri in nearby_triangles:
                        z = self._ray_triangle_intersection_fast(world_x, world_y, max_height, tri)
                        if z is not None and z > max_z:
                            max_z = z

                    self.heights[gy, gx] = max_z
                    processed += 1

                # Progress update co blok
                if gx_start % (block_size * 10) == 0:
                    progress = (processed / total_points) * 100
                    print(f"Progress: {progress:.1f}% ({processed}/{total_points})")

        end_time = time.time()
        print(f"Mapa wysokości wygenerowana w {end_time - start_time:.2f} sekund")
        print(f"Zakres wysokości: {np.min(self.heights):.2f} - {np.max(self.heights):.2f}")

    def _create_spatial_hash(self, triangles, grid_size=5.0):
        """
        Tworzy spatial hash do przyspieszenia wyszukiwania trójkątów
        """
        spatial_hash = defaultdict(list)

        for i, triangle in enumerate(triangles):
            # Oblicz bounding box trójkąta
            v0, v1, v2 = triangle
            min_x = min(v0[0], v1[0], v2[0])
            max_x = max(v0[0], v1[0], v2[0])
            min_y = min(v0[1], v1[1], v2[1])
            max_y = max(v0[1], v1[1], v2[1])

            # Dodaj trójkąt do wszystkich sektorów które pokrywa
            start_x = int(min_x // grid_size)
            end_x = int(max_x // grid_size)
            start_y = int(min_y // grid_size)
            end_y = int(max_y // grid_size)

            for gx in range(start_x, end_x + 1):
                for gy in range(start_y, end_y + 1):
                    spatial_hash[(gx, gy)].append(triangle)

        print(f"Utworzono spatial hash z {len(spatial_hash)} sektorami")
        return spatial_hash

    def _get_nearby_triangles(self, spatial_hash, world_x, world_y, grid_size=5.0):
        """
        Pobiera trójkąty z sektora zawierającego dany punkt
        """
        sector_x = int(world_x // grid_size)
        sector_y = int(world_y // grid_size)

        # Pobierz trójkąty z głównego sektora i sąsiadujących
        nearby_triangles = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                sector_key = (sector_x + dx, sector_y + dy)
                nearby_triangles.extend(spatial_hash.get(sector_key, []))

        return nearby_triangles

    def _extract_triangles_from_scene(self, scene, model_matrix):
        """Wyciąga wszystkie trójkąty ze sceny i transformuje je do przestrzeni świata"""
        triangles = []

        for mesh_data in scene.meshes:
            positions = mesh_data['positions']
            indices = mesh_data['indices']

            # Transformuj pozycje do przestrzeni świata (batch processing)
            world_positions = self._transform_positions_batch(positions, model_matrix)

            # Utwórz trójkąty
            if indices is not None:
                # Z indeksami
                for i in range(0, len(indices), 3):
                    if i + 2 < len(indices):
                        v0 = world_positions[indices[i]]
                        v1 = world_positions[indices[i + 1]]
                        v2 = world_positions[indices[i + 2]]
                        triangles.append((v0, v1, v2))
            else:
                # Bez indeksów
                for i in range(0, len(world_positions), 3):
                    if i + 2 < len(world_positions):
                        triangles.append((
                            world_positions[i],
                            world_positions[i + 1],
                            world_positions[i + 2]
                        ))

        return triangles

    def _transform_positions_batch(self, positions, model_matrix):
        """Transformuje pozycje w batchu dla lepszej wydajności"""
        world_positions = []
        for pos in positions:
            world_pos4 = model_matrix * vec4(pos[0], pos[1], pos[2], 1.0)
            world_positions.append((world_pos4.x, world_pos4.y, world_pos4.z))
        return world_positions

    def _ray_triangle_intersection_fast(self, ray_x, ray_y, ray_start_z, triangle):
        """
        Szybsza wersja ray-triangle intersection z early exit
        """
        v0, v1, v2 = triangle

        # Quick bounding box check
        min_x = min(v0[0], v1[0], v2[0])
        max_x = max(v0[0], v1[0], v2[0])
        min_y = min(v0[1], v1[1], v2[1])
        max_y = max(v0[1], v1[1], v2[1])

        if ray_x < min_x or ray_x > max_x or ray_y < min_y or ray_y > max_y:
            return None

        # Kierunek promienia (w dół)
        ray_dir = (0.0, 0.0, -1.0)
        ray_origin = (ray_x, ray_y, ray_start_z)

        # Algorytm Möller-Trumbore
        edge1 = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
        edge2 = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])

        # Iloczyn wektorowy ray_dir × edge2
        h = (
            ray_dir[1] * edge2[2] - ray_dir[2] * edge2[1],
            ray_dir[2] * edge2[0] - ray_dir[0] * edge2[2],
            ray_dir[0] * edge2[1] - ray_dir[1] * edge2[0]
        )

        # Iloczyn skalarny edge1 · h
        a = edge1[0] * h[0] + edge1[1] * h[1] + edge1[2] * h[2]

        if abs(a) < 1e-8:  # Promień równoległy do trójkąta
            return None

        f = 1.0 / a
        s = (ray_origin[0] - v0[0], ray_origin[1] - v0[1], ray_origin[2] - v0[2])

        # Iloczyn skalarny s · h
        u = f * (s[0] * h[0] + s[1] * h[1] + s[2] * h[2])

        if u < 0.0 or u > 1.0:
            return None

        # Iloczyn wektorowy s × edge1
        q = (
            s[1] * edge1[2] - s[2] * edge1[1],
            s[2] * edge1[0] - s[0] * edge1[2],
            s[0] * edge1[1] - s[1] * edge1[0]
        )

        # Iloczyn skalarny ray_dir · q
        v = f * (ray_dir[0] * q[0] + ray_dir[1] * q[1] + ray_dir[2] * q[2])

        if v < 0.0 or u + v > 1.0:
            return None

        # Oblicz t (odległość wzdłuż promienia)
        t = f * (edge2[0] * q[0] + edge2[1] * q[1] + edge2[2] * q[2])

        if t > 1e-8:  # Przecięcie przed promieniem
            # Oblicz współrzędną Z przecięcia
            intersection_z = ray_start_z - t
            return intersection_z

        return None

    def get_height(self, x, y):
        """
        Pobiera wysokość terenu w danym punkcie
        Używa interpolacji bilinearnej dla płynnego przejścia
        """
        # Sprawdź czy punkt jest w granicach mapy
        if x < self.x_min or x > self.x_max or y < self.y_min or y > self.y_max:
            return self.default_height

        # Przelicz na współrzędne siatki
        fx = (x - self.x_min) / self.resolution
        fy = (y - self.y_min) / self.resolution

        # Znajdź indeksy sąsiadujących punktów
        gx0 = int(fx)
        gy0 = int(fy)
        gx1 = min(gx0 + 1, self.width - 1)
        gy1 = min(gy0 + 1, self.height - 1)

        # Oblicz wagi dla interpolacji
        wx = fx - gx0
        wy = fy - gy0

        # Pobierz wysokości z czterech sąsiadujących punktów
        h00 = self.heights[gy0, gx0]
        h10 = self.heights[gy0, gx1]
        h01 = self.heights[gy1, gx0]
        h11 = self.heights[gy1, gx1]

        # Interpolacja bilinearna
        h0 = h00 * (1 - wx) + h10 * wx
        h1 = h01 * (1 - wx) + h11 * wx
        height = h0 * (1 - wy) + h1 * wy

        return height

    def save_to_file(self, filename):
        """Zapisuje mapę wysokości do pliku"""
        np.save(filename, self.heights)
        print(f"Mapa wysokości zapisana do {filename}")

    def load_from_file(self, filename):
        """Wczytuje mapę wysokości z pliku"""
        self.heights = np.load(filename)
        print(f"Mapa wysokości wczytana z {filename}")

    def get_debug_info(self):
        """Zwraca informacje debugowe o mapie"""
        return {
            'size': f"{self.width}x{self.height}",
            'resolution': self.resolution,
            'bounds': f"X: {self.x_min}-{self.x_max}, Y: {self.y_min}-{self.y_max}",
            'height_range': f"{np.min(self.heights):.2f} - {np.max(self.heights):.2f}",
            'memory_usage': f"{self.heights.nbytes / 1024:.1f} KB"
        }