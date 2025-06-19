import math
from pyglm.glm import vec3, radians, normalize, cross, lookAt
import pygame

"""
First-person camera controller for navigating a 3D scene.
Handles position, orientation (yaw, pitch), and movement based on mouse and keyboard input.
"""
class Camera:
    """
           Initialize camera parameters.

           Args:
               position (vec3): Initial position in world space.
               up (vec3): World up vector.
               yaw (float): Initial yaw angle (degrees).
               pitch (float): Initial pitch angle (degrees).
               speed (float): Movement speed multiplier.
               sensitivity (float): Mouse sensitivity multiplier.
    """
    def __init__(self,
                 position=vec3(0.0, -60.0, 20.0),
                 up=vec3(0.0, 0.0, 1.0),
                 yaw=90.0,
                 pitch=0.0,
                 speed=30.0,
                 sensitivity=0.2):

        self.position  = position
        self.worldUp   = up
        self.yaw       = yaw
        self.pitch     = pitch
        self.front     = vec3(0.0, 1.0, 0.0)
        self.right     = normalize(cross(self.front, self.worldUp))
        self.up        = normalize(cross(self.right, self.front))
        self.moveSpeed = speed
        self.mouseSens = sensitivity
    """
    Update yaw and pitch based on mouse movement deltas and recompute orientation vectors.

    Args:
        dx (float): Mouse delta in x-direction.
        dy (float): Mouse delta in y-direction.
    """
    def process_mouse_delta(self, dx, dy):

        xoffset = -dx * self.mouseSens
        yoffset = -dy * self.mouseSens
        self.yaw   += xoffset
        self.pitch = max(-89.0, min(89.0, self.pitch + yoffset))

        fx = math.cos(radians(self.yaw)) * math.cos(radians(self.pitch))
        fy = math.sin(radians(self.yaw)) * math.cos(radians(self.pitch))
        fz = math.sin(radians(self.pitch))
        self.front = normalize(vec3(fx, fy, fz))
        self.right = normalize(cross(self.front, self.worldUp))
        self.up    = normalize(cross(self.right, self.front))

    """
            Move the camera position based on pressed keys and elapsed time.

            Args:
                keys (Sequence[bool]): Keyboard state array from pygame.key.get_pressed().
                dt (float): Delta time since last frame in seconds.
    """
    def process_keyboard(self, keys, dt):
        velocity = self.moveSpeed * dt
        if keys[pygame.K_w]: self.position += self.front * velocity
        if keys[pygame.K_s]: self.position -= self.front * velocity
        if keys[pygame.K_a]: self.position -= self.right * velocity
        if keys[pygame.K_d]: self.position += self.right * velocity
        if keys[pygame.K_SPACE]:   # ascend
            self.position += self.worldUp * velocity
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:  # descend
            self.position -= self.worldUp * velocity
    """
    Compute the view matrix for the current camera orientation and position.

    Returns:
        mat4: 4x4 view matrix transforming world to camera space.
    """
    def get_view_matrix(self):
        return lookAt(self.position,
                      self.position + self.front,
                      self.up)