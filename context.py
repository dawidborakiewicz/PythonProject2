import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *

"""
Initialize Pygame window and OpenGL context with core profile settings.

Args:
    width (int): Window width in pixels.
    height (int): Window height in pixels.
    title (str): Window title.

Returns:
    pygame.Surface: Pygame display surface.
"""
def init_context(width=800, height=600, title="Deszcz Point-Sprite"):
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                    pygame.GL_CONTEXT_PROFILE_CORE)
    screen = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption(title)

    glEnable(GL_PROGRAM_POINT_SIZE)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    print("OpenGL version:", glGetString(GL_VERSION).decode())
    return screen