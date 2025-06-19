from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from pyglm.glm import (mat4, value_ptr)
import pygame

SKYBOX_VERT_SHADER = """
#version 330 core
layout(location = 0) in vec3 a_position;
out vec3 v_texCoord;
uniform mat4 u_projection;
uniform mat4 u_view;

void main() {
    v_texCoord = a_position;
    vec4 pos = u_projection * u_view * vec4(a_position, 1.0);
    gl_Position = pos.xyww;
}
"""

SKYBOX_FRAG_SHADER = """
#version 330 core
in vec3 v_texCoord;
out vec4 FragColor;
uniform samplerCube u_skybox;
uniform float u_exposure;

void main() {
    vec3 color = texture(u_skybox, v_texCoord).rgb;

    // Aplikuj ekspozycję
    color = color * u_exposure;

    // Opcjonalnie: tone mapping dla lepszego wyglądu
    // color = color / (color + vec3(1.0));

    FragColor = vec4(color, 1.0);
}
"""

# Poprawione vertices z właściwą orientacją dla skyboxa
skybox_vertices = [
    # Front face (+Z)
    -1.0, -1.0, 1.0,
    -1.0, 1.0, 1.0,
    1.0, 1.0, 1.0,
    1.0, 1.0, 1.0,
    1.0, -1.0, 1.0,
    -1.0, -1.0, 1.0,

    # Back face (-Z)
    1.0, -1.0, -1.0,
    1.0, 1.0, -1.0,
    -1.0, 1.0, -1.0,
    -1.0, 1.0, -1.0,
    -1.0, -1.0, -1.0,
    1.0, -1.0, -1.0,

    # Left face (-X)
    -1.0, -1.0, -1.0,
    -1.0, 1.0, -1.0,
    -1.0, 1.0, 1.0,
    -1.0, 1.0, 1.0,
    -1.0, -1.0, 1.0,
    -1.0, -1.0, -1.0,

    # Right face (+X)
    1.0, -1.0, 1.0,
    1.0, 1.0, 1.0,
    1.0, 1.0, -1.0,
    1.0, 1.0, -1.0,
    1.0, -1.0, -1.0,
    1.0, -1.0, 1.0,

    # Top face (+Y)
    -1.0, 1.0, 1.0,
    -1.0, 1.0, -1.0,
    1.0, 1.0, -1.0,
    1.0, 1.0, -1.0,
    1.0, 1.0, 1.0,
    -1.0, 1.0, 1.0,

    # Bottom face (-Y)
    -1.0, -1.0, -1.0,
    -1.0, -1.0, 1.0,
    1.0, -1.0, 1.0,
    1.0, -1.0, 1.0,
    1.0, -1.0, -1.0,
    -1.0, -1.0, -1.0
]


class SkyboxRenderer:
    def __init__(self, atlas_path, exposure=1.0):
        self.shader = compileProgram(
            compileShader(SKYBOX_VERT_SHADER, GL_VERTEX_SHADER),
            compileShader(SKYBOX_FRAG_SHADER, GL_FRAGMENT_SHADER)
        )
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        self.exposure = exposure  # Domyślna ekspozycja

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, len(skybox_vertices) * 4, (GLfloat * len(skybox_vertices))(*skybox_vertices),
                     GL_STATIC_DRAW)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

        glBindVertexArray(0)

        self.cubemap_texture = self.load_cubemap_from_atlas(atlas_path)

    def set_exposure(self, exposure):
        self.exposure = exposure

    def load_cubemap_from_atlas(self, atlas_path):
        atlas = pygame.image.load(atlas_path).convert_alpha()
        atlas_width = atlas.get_width()
        atlas_height = atlas.get_height()

        face_size = atlas_height // 3
        face_rects = [
            pygame.Rect(2 * face_size, face_size, face_size, face_size),  # +X (right)
            pygame.Rect(0 * face_size, face_size, face_size, face_size),  # -X (left)
            pygame.Rect(1 * face_size, face_size, face_size, face_size),  # +Z (front)
            pygame.Rect(3 * face_size, face_size, face_size, face_size),  # -Z (back)
            pygame.Rect(1 * face_size, 0 * face_size, face_size, face_size),  # +Y (top)
            pygame.Rect(1 * face_size, 2 * face_size, face_size, face_size),  # -Y (bottom)
        ]

        texID = glGenTextures(1)
        glBindTexture(GL_TEXTURE_CUBE_MAP, texID)

        for i, rect in enumerate(face_rects):
            if (rect.x + rect.width <= atlas_width and
                    rect.y + rect.height <= atlas_height):
                face_surface = atlas.subsurface(rect)

                if i == 0:  # +X (right)
                    face_surface = pygame.transform.rotate(face_surface, 90)
                elif i == 1:  # -X (left)
                    face_surface = pygame.transform.rotate(face_surface, 270)
                elif i == 3:  # -Z (back)
                    face_surface = pygame.transform.rotate(face_surface, 180)
                elif i == 5: face_surface = pygame.transform.rotate(face_surface, 180)

            else:
                face_surface = pygame.Surface((face_size, face_size), pygame.SRCALPHA)
                face_surface.fill((128, 128, 255, 255))  # Niebieski placeholder

            img_data = pygame.image.tostring(face_surface, "RGBA", True)
            glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL_RGBA,
                         face_surface.get_width(), face_surface.get_height(),
                         0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)

        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)

        return texID

    def render(self, proj_matrix, view_matrix):
        glDepthFunc(GL_LEQUAL)
        glUseProgram(self.shader)

        view_no_translation = mat4(view_matrix)
        view_no_translation[3][0] = 0.0
        view_no_translation[3][1] = 0.0
        view_no_translation[3][2] = 0.0

        proj_loc = glGetUniformLocation(self.shader, "u_projection")
        view_loc = glGetUniformLocation(self.shader, "u_view")
        exposure_loc = glGetUniformLocation(self.shader, "u_exposure")

        glUniformMatrix4fv(proj_loc, 1, GL_FALSE, value_ptr(proj_matrix))
        glUniformMatrix4fv(view_loc, 1, GL_FALSE, value_ptr(view_no_translation))
        glUniform1f(exposure_loc, self.exposure)  # Przekaż ekspozycję do shadera

        glBindVertexArray(self.vao)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_CUBE_MAP, self.cubemap_texture)
        glUniform1i(glGetUniformLocation(self.shader, "u_skybox"), 0)

        glDrawArrays(GL_TRIANGLES, 0, 36)

        glBindVertexArray(0)
        glUseProgram(0)
        glDepthFunc(GL_LESS)

    def cleanup(self):
        glDeleteVertexArrays(1, [self.vao])
        glDeleteBuffers(1, [self.vbo])
        glDeleteTextures(1, [self.cubemap_texture])