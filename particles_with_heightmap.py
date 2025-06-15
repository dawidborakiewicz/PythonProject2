import numpy as np
from config import *


class ParticleSystemWithHeightMap:
    def __init__(self, height_map=None):
        self.height_map = height_map

        self.positions = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
        self.velocities = np.zeros((NUM_PARTICLES, 3), dtype=np.float32)
        self.variants = np.random.randint(0, ATLAS_COLS,
                                          size=NUM_PARTICLES,
                                          dtype=np.int32)
        self.states = np.zeros(NUM_PARTICLES, dtype=np.int32)
        self.timers = np.zeros(NUM_PARTICLES, dtype=np.float32)
        self.flight_timers = np.zeros(NUM_PARTICLES, dtype=np.float32)

        # Nowe: wysokości terenu dla każdej cząsteczki
        self.ground_heights = np.full(NUM_PARTICLES, Z_GROUND, dtype=np.float32)

        self.init_particles()

    def set_height_map(self, height_map):
        """Ustawia mapę wysokości i przelicza wysokości terenu dla wszystkich cząstek"""
        self.height_map = height_map
        self._update_all_ground_heights()

    def init_particles(self):
        """Inicjalizuje pozycje i prędkości cząstek"""
        # Randomizuj pozycje spawnu
        self.positions[:, 0] = np.random.uniform(X_MIN, X_MAX, NUM_PARTICLES)
        self.positions[:, 1] = np.random.uniform(Y_MIN, Y_MAX, NUM_PARTICLES)
        self.positions[:, 2] = np.random.uniform(Z_SPAWN,
                                                 Z_SPAWN + Z_HEIGHT,
                                                 NUM_PARTICLES)

        # Początkowa prędkość w dół
        self.velocities[:] = (0.0, 0.0, -RAIN_SPEED)

        # Wszystkie cząstki zaczynają w fazie lotu (klatka 0)
        self.states[:] = 0
        self.timers[:] = 0.0
        self.flight_timers[:] = 0.0

        # Oblicz wysokości terenu dla każdej cząstki
        self._update_all_ground_heights()

    def _update_all_ground_heights(self):
        """Aktualizuje wysokości terenu dla wszystkich cząstek"""
        if self.height_map is None:
            self.ground_heights[:] = Z_GROUND
            return

        for i in range(NUM_PARTICLES):
            x, y = self.positions[i, 0], self.positions[i, 1]
            self.ground_heights[i] = self.height_map.get_height(x, y)

    def _update_ground_height_for_particle(self, idx):
        """Aktualizuje wysokość terenu dla pojedynczej cząstki"""
        if self.height_map is None:
            self.ground_heights[idx] = Z_GROUND
            return

        x, y = self.positions[idx, 0], self.positions[idx, 1]
        self.ground_heights[idx] = self.height_map.get_height(x, y)

    def update(self, dt):
        # 1) Przełączanie stanu lotu (0 <-> 1) dla cząstek w locie (state < 2)
        flight_mask = (self.states < 2)
        self.flight_timers[flight_mask] += dt
        toggle = flight_mask & (self.flight_timers >= FLIGHT_FRAME_T)
        if np.any(toggle):
            self.flight_timers[toggle] -= FLIGHT_FRAME_T
            self.states[toggle] = 1 - self.states[toggle]

        # 2) Poruszanie cząstek w locie (state 0 lub 1)
        flight = (self.states < 2)
        prev_z = self.positions[:, 2].copy()
        self.positions[flight, 2] += self.velocities[flight, 2] * dt

        # 3) Wykrycie kolizji z terenem i wejście w fazę splash (state 2)
        # Używamy indywidualnych wysokości terenu dla każdej cząstki
        hit = flight & (prev_z >= self.ground_heights) & (self.positions[:, 2] < self.ground_heights)
        if np.any(hit):
            self.states[hit] = 2
            self.timers[hit] = SPLAT_TIME
            self.positions[hit, 2] = self.ground_heights[hit]  # Ustaw dokładnie na poziom terenu
            self.flight_timers[hit] = 0.0

        # 4) Zmniejszanie timerów dla faz splash i przejście 2->3
        splat_mask = (self.states >= 2)
        if np.any(splat_mask):
            self.timers[splat_mask] -= dt
            to_splash = splat_mask & (self.states == 2) & (self.timers <= HALF_SPLAT)
            if np.any(to_splash):
                self.states[to_splash] = 3

        # 5) Po zakończeniu animacji splash (timer <= 0), resetuj cząstkę
        done = (self.states >= 2) & (self.timers <= 0.0)
        if np.any(done):
            self._respawn_particles(done)

    def _respawn_particles(self, mask):
        """Respawnuje cząstki które zakończyły animację"""
        indices = np.where(mask)[0]
        cnt = len(indices)

        # Nowe pozycje spawnu
        self.positions[mask, 0] = np.random.uniform(X_MIN, X_MAX, cnt)
        self.positions[mask, 1] = np.random.uniform(Y_MIN, Y_MAX, cnt)
        self.positions[mask, 2] = np.random.uniform(Z_SPAWN, Z_SPAWN + Z_HEIGHT, cnt)

        # Reset prędkości i stanów
        self.velocities[mask, 2] = -RAIN_SPEED
        self.states[mask] = 0
        self.timers[mask] = 0.0
        self.flight_timers[mask] = 0.0

        # Aktualizuj wysokości terenu dla nowych pozycji
        for idx in indices:
            self._update_ground_height_for_particle(idx)

    def get_stats(self):
        """Zwraca statystyki systemu cząstek"""
        states, counts = np.unique(self.states, return_counts=True)
        stats = dict(zip(states, counts))

        return {
            'total_particles': NUM_PARTICLES,
            'flying_particles': stats.get(0, 0) + stats.get(1, 0),
            'splashing_particles': stats.get(2, 0) + stats.get(3, 0),
            'height_range': f"{np.min(self.ground_heights):.2f} - {np.max(self.ground_heights):.2f}",
            'position_range_z': f"{np.min(self.positions[:, 2]):.2f} - {np.max(self.positions[:, 2]):.2f}"
        }