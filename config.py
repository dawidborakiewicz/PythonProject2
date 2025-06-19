# Configuration constants for particle counts, spawn bounds, timing, and texture atlas layout.
NUM_PARTICLES   = 50000          # Total number of raindrop particles
X_MIN, X_MAX    = -20.0, 20.0    # Horizontal spawn area in X
Y_MIN, Y_MAX    = -20.0, 20.0    # Horizontal spawn area in Y
Z_SPAWN, Z_HEIGHT = 20.0, 40.0   # Vertical spawn region base and height
Z_GROUND        = 1.0            # Default ground plane height if no terrain map
RAIN_SPEED      = 20.0           # Downward velocity of raindrops

ATLAS_ROWS      = 4              # Rows in sprite atlas
ATLAS_COLS      = 4              # Columns in sprite atlas

SPLAT_TIME      = 0.2            # Total splash duration
HALF_SPLAT      = SPLAT_TIME / 4.0  # Time until transition to final frame

FLIGHT_FRAME_T  = 0.1            # Time per frame for falling animation toggle :contentReference[oaicite:1]{index=1}
