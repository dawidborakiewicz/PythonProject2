# scene_renderer.py

from OpenGL.GL import *
from pyglm.glm import value_ptr, mat4, vec3

"""
Wraps an OpenGL shader and GLTFScene for drawing static geometry.

Attributes:
    shader       (int): Compiled program handle.
    scene        (GLTFScene): Mesh & texture data.
    model_matrix (mat4): World transform for the scene.
    light_pos, light_color, ambient_color (vec3): Lighting parameters.
"""
class SceneRenderer:
    def __init__(self, shader, scene):
        self.shader = shader
        self.scene = scene
        self.model_matrix = mat4(1.0)  # Identity matrix

        self.light_pos = vec3(5.0, 5.0, 10.0)
        self.light_color = vec3(1.0, 1.0, 1.0)
        self.ambient_color = vec3(0.3, 0.3, 0.4)

    def set_model_matrix(self, matrix):
        self.model_matrix = matrix
    """
    Override lighting parameters (any subset).

    Args:
        light_pos (vec3): Position of the point light.
        light_color (vec3): Diffuse light color.
        ambient_color (vec3): Ambient light color.
    """
    def set_lighting(self, light_pos=None, light_color=None, ambient_color=None):
        if light_pos:
            self.light_pos = light_pos
        if light_color:
            self.light_color = light_color
        if ambient_color:
            self.ambient_color = ambient_color

    """
    Draws each VAO in self.scene.vao_list:

    1. Use shader, call _set_uniforms().
    2. For each mesh: apply base_color, bind texture if present,
       bind VAO and draw elements or arrays.
    3. Unbind shader.
    """
    def render(self, proj_matrix, view_matrix, camera_pos):
        glUseProgram(self.shader)

        self._set_uniforms(proj_matrix, view_matrix, camera_pos)

        for vao_data in self.scene.vao_list:
            self._render_mesh(vao_data)

        glUseProgram(0)
    """
    Upload core uniforms:
      - u_projection, u_view, u_model
      - u_lightPos, u_lightColor, u_ambientColor, u_viewPos
    """
    def _set_uniforms(self, proj_matrix, view_matrix, camera_pos):
        proj_loc = glGetUniformLocation(self.shader, "u_projection")
        view_loc = glGetUniformLocation(self.shader, "u_view")
        model_loc = glGetUniformLocation(self.shader, "u_model")

        glUniformMatrix4fv(proj_loc, 1, GL_FALSE, value_ptr(proj_matrix))
        glUniformMatrix4fv(view_loc, 1, GL_FALSE, value_ptr(view_matrix))
        glUniformMatrix4fv(model_loc, 1, GL_FALSE, value_ptr(self.model_matrix))

        light_pos_loc = glGetUniformLocation(self.shader, "u_lightPos")
        light_color_loc = glGetUniformLocation(self.shader, "u_lightColor")
        ambient_color_loc = glGetUniformLocation(self.shader, "u_ambientColor")
        view_pos_loc = glGetUniformLocation(self.shader, "u_viewPos")

        glUniform3fv(light_pos_loc, 1, value_ptr(self.light_pos))
        glUniform3fv(light_color_loc, 1, value_ptr(self.light_color))
        glUniform3fv(ambient_color_loc, 1, value_ptr(self.ambient_color))
        glUniform3fv(view_pos_loc, 1, value_ptr(camera_pos))
    """
    Per-mesh draw:
      - Set u_baseColor, u_hasTexture, bind u_texture if needed.
      - Bind VAO, glDrawElements or glDrawArrays.
      - Unbind VAO/texture.
    """
    def _render_mesh(self, vao_data):
        base_color_loc = glGetUniformLocation(self.shader, "u_baseColor")
        glUniform4f(base_color_loc, *vao_data['base_color'])

        has_texture_loc = glGetUniformLocation(self.shader, "u_hasTexture")
        if vao_data['texture'] is not None:
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, vao_data['texture'])
            glUniform1i(glGetUniformLocation(self.shader, "u_texture"), 0)
            glUniform1i(has_texture_loc, 1)
        else:
            glUniform1i(has_texture_loc, 0)

        glBindVertexArray(vao_data['vao'])

        if vao_data['has_indices']:
            glDrawElements(GL_TRIANGLES, vao_data['count'], GL_UNSIGNED_INT, None)
        else:
            glDrawArrays(GL_TRIANGLES, 0, vao_data['count'])

        glBindVertexArray(0)

        if vao_data['texture'] is not None:
            glBindTexture(GL_TEXTURE_2D, 0)