import numpy as np
from config import *

"""
Simulates raindrop particles falling and splashing based on a terrain height map.
Manages particle states, positions, velocities, and splash animation timing.
"""
class ParticleSystemWithHeightMap:
    """Initialize particle arrays and optionally assign height map."""
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

        self.ground_heights = np.full(NUM_PARTICLES, Z_GROUND, dtype=np.float32)

        self.init_particles()

    """Assign a HeightMap instance and update all ground heights."""
    def set_height_map(self, height_map):
        self.height_map = height_map
        self._update_all_ground_heights()

    """Randomize initial positions above terrain and reset states."""
    def init_particles(self):
        self.positions[:, 0] = np.random.uniform(X_MIN, X_MAX, NUM_PARTICLES)
        self.positions[:, 1] = np.random.uniform(Y_MIN, Y_MAX, NUM_PARTICLES)
        self.positions[:, 2] = np.random.uniform(Z_SPAWN,
                                                 Z_SPAWN + Z_HEIGHT,
                                                 NUM_PARTICLES)

        self.velocities[:] = (0.0, 0.0, -RAIN_SPEED)

        self.states[:] = 0
        self.timers[:] = 0.0
        self.flight_timers[:] = 0.0

        self._update_all_ground_heights()

    def _update_all_ground_heights(self):
        if self.height_map is None:
            self.ground_heights[:] = Z_GROUND
            return

        for i in range(NUM_PARTICLES):
            x, y = self.positions[i, 0], self.positions[i, 1]
            self.ground_heights[i] = self.height_map.get_height(x, y)

    def _update_ground_height_for_particle(self, idx):
        if self.height_map is None:
            self.ground_heights[idx] = Z_GROUND
            return

        x, y = self.positions[idx, 0], self.positions[idx, 1]
        self.ground_heights[idx] = self.height_map.get_height(x, y)
    """
    Advance the simulation by dt:
     - toggle the flight frame (0 or 1),
     - move each particle downward,
     - detect ground collision and transition to the splash state,
     - play the splash animation and respawn the particle once it finishes.
    """
    def update(self, dt):
        flight_mask = (self.states < 2)
        self.flight_timers[flight_mask] += dt
        toggle = flight_mask & (self.flight_timers >= FLIGHT_FRAME_T)
        if np.any(toggle):
            self.flight_timers[toggle] -= FLIGHT_FRAME_T
            self.states[toggle] = 1 - self.states[toggle]

        flight = (self.states < 2)
        prev_z = self.positions[:, 2].copy()
        self.positions[flight, 2] += self.velocities[flight, 2] * dt

        hit = flight & (prev_z >= self.ground_heights) & (self.positions[:, 2] < self.ground_heights)
        if np.any(hit):
            self.states[hit] = 2
            self.timers[hit] = SPLAT_TIME
            self.positions[hit, 2] = self.ground_heights[hit]  # Ustaw dokładnie na poziom terenu
            self.flight_timers[hit] = 0.0

        splat_mask = (self.states >= 2)
        if np.any(splat_mask):
            self.timers[splat_mask] -= dt
            to_splash = splat_mask & (self.states == 2) & (self.timers <= HALF_SPLAT)
            if np.any(to_splash):
                self.states[to_splash] = 3

        done = (self.states >= 2) & (self.timers <= 0.0)
        if np.any(done):
            self._respawn_particles(done)

    def _respawn_particles(self, mask):
        indices = np.where(mask)[0]
        cnt = len(indices)

        self.positions[mask, 0] = np.random.uniform(X_MIN, X_MAX, cnt)
        self.positions[mask, 1] = np.random.uniform(Y_MIN, Y_MAX, cnt)
        self.positions[mask, 2] = np.random.uniform(Z_SPAWN, Z_SPAWN + Z_HEIGHT, cnt)

        self.velocities[mask, 2] = -RAIN_SPEED
        self.states[mask] = 0
        self.timers[mask] = 0.0
        self.flight_timers[mask] = 0.0

        for idx in indices:
            self._update_ground_height_for_particle(idx)
    """
    Return particle statistics, including:
        total_particles,
        flying_particles,
        splashing_particles,
        height_range,
        position_range_z
    """
    def get_stats(self):
        states, counts = np.unique(self.states, return_counts=True)
        stats = dict(zip(states, counts))

        return {
            'total_particles': NUM_PARTICLES,
            'flying_particles': stats.get(0, 0) + stats.get(1, 0),
            'splashing_particles': stats.get(2, 0) + stats.get(3, 0),
            'height_range': f"{np.min(self.ground_heights):.2f} - {np.max(self.ground_heights):.2f}",
            'position_range_z': f"{np.min(self.positions[:, 2]):.2f} - {np.max(self.positions[:, 2]):.2f}"
        }