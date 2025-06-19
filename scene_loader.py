# scene_loader.py
import os
import numpy as np
from PIL import Image
from pygltflib import GLTF2
from OpenGL.GL import *

"""
Loads objects and textures from a glTF file and converts them into a format ready for rendering.
Stores raw mesh data (positions, normals, UVs, indices) as well as generated textures.
"""
class GLTFScene:
    def __init__(self):
        self.meshes = []
        self.textures = {}
        self.vao_list = []

    def load(self, path):

        base = os.path.dirname(path) or '.'
        gltf = GLTF2().load(path)

        with open(os.path.join(base, gltf.buffers[0].uri), 'rb') as f:
            blob = f.read()

        self._load_textures(gltf, base)

        for mesh in gltf.meshes:
            for prim in mesh.primitives:
                mesh_data = self._process_primitive(gltf, blob, prim)
                if mesh_data:
                    self.meshes.append(mesh_data)

    """
    For each texture:
     - load the image file via PIL,
     - create an OpenGL texture, set wrap and filter parameters,
     - upload the image data and generate mipmaps.
    """
    def _load_textures(self, gltf, base_path):
        for i, img in enumerate(gltf.images):
            img_path = os.path.join(base_path, img.uri)
            try:
                im = Image.open(img_path).convert('RGBA')
                tex = glGenTextures(1)
                glBindTexture(GL_TEXTURE_2D, tex)

                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

                data = im.transpose(Image.FLIP_TOP_BOTTOM).tobytes()
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, im.width, im.height,
                             0, GL_RGBA, GL_UNSIGNED_BYTE, data)
                glGenerateMipmap(GL_TEXTURE_2D)

                self.textures[i] = tex
            except Exception as e:
                print(f"Błąd ładowania tekstury {img.uri}: {e}")

        glBindTexture(GL_TEXTURE_2D, 0)

    def _extract_accessor(self, gltf, blob, acc_idx):
        acc = gltf.accessors[acc_idx]
        bv = gltf.bufferViews[acc.bufferView]

        type_sizes = {5126: 4, 5125: 4, 5123: 2}  # FLOAT, UINT, USHORT
        type_components = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
        type_dtypes = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}

        start = (bv.byteOffset or 0) + (acc.byteOffset or 0)
        count = acc.count * type_sizes[acc.componentType] * type_components[acc.type]

        arr = np.frombuffer(blob[start:start + count], dtype=type_dtypes[acc.componentType])
        return arr.reshape((acc.count, type_components[acc.type]))

    """
    Extract accessors (POSITION, NORMAL, TEXCOORD_0, INDICES)
    and build a mesh_data dictionary for a single mesh.
    """
    def _process_primitive(self, gltf, blob, prim):
        try:
            pos = self._extract_accessor(gltf, blob, prim.attributes.POSITION).astype(np.float32)

            norm = None
            if hasattr(prim.attributes, 'NORMAL') and prim.attributes.NORMAL is not None:
                norm = self._extract_accessor(gltf, blob, prim.attributes.NORMAL).astype(np.float32)

            uv = None
            if hasattr(prim.attributes, 'TEXCOORD_0') and prim.attributes.TEXCOORD_0 is not None:
                uv = self._extract_accessor(gltf, blob, prim.attributes.TEXCOORD_0).astype(np.float32)

            indices = None
            if prim.indices is not None:
                indices = self._extract_accessor(gltf, blob, prim.indices).flatten().astype(np.uint32)

            tex_id = None
            base_color = (1.0, 1.0, 1.0, 1.0)

            if prim.material is not None:
                mat = gltf.materials[prim.material]
                if hasattr(mat, 'pbrMetallicRoughness') and mat.pbrMetallicRoughness:
                    pbr = mat.pbrMetallicRoughness
                    if hasattr(pbr, 'baseColorTexture') and pbr.baseColorTexture:
                        tex_idx = pbr.baseColorTexture.index
                        if tex_idx < len(gltf.textures):
                            src = gltf.textures[tex_idx].source
                            tex_id = self.textures.get(src)

                    if hasattr(pbr, 'baseColorFactor') and pbr.baseColorFactor:
                        base_color = tuple(pbr.baseColorFactor)

            return {
                'positions': pos,
                'normals': norm,
                'uvs': uv,
                'indices': indices,
                'texture': tex_id,
                'base_color': base_color
            }

        except Exception as e:
            print(f"Błąd przetwarzania prymitywu: {e}")
            return None

    """
    Generate a VAO along with its VBOs and IBO from the provided mesh_data,
    and return the handles/info to the renderer.
    """
    def create_vao(self, mesh_data):
        vao = glGenVertexArrays(1)
        glBindVertexArray(vao)

        vbos = []

        pos_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, pos_vbo)
        glBufferData(GL_ARRAY_BUFFER, mesh_data['positions'].nbytes,
                     mesh_data['positions'], GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        vbos.append(pos_vbo)

        if mesh_data['normals'] is not None:
            norm_vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, norm_vbo)
            glBufferData(GL_ARRAY_BUFFER, mesh_data['normals'].nbytes,
                         mesh_data['normals'], GL_STATIC_DRAW)
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)
            vbos.append(norm_vbo)

        if mesh_data['uvs'] is not None:
            uv_vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, uv_vbo)
            glBufferData(GL_ARRAY_BUFFER, mesh_data['uvs'].nbytes,
                         mesh_data['uvs'], GL_STATIC_DRAW)
            glEnableVertexAttribArray(2)
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, None)
            vbos.append(uv_vbo)

        ibo = None
        if mesh_data['indices'] is not None:
            ibo = glGenBuffers(1)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ibo)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, mesh_data['indices'].nbytes,
                         mesh_data['indices'], GL_STATIC_DRAW)

        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        if ibo:
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

        return {
            'vao': vao,
            'vbos': vbos,
            'ibo': ibo,
            'count': len(mesh_data['indices']) if mesh_data['indices'] is not None else len(mesh_data['positions']),
            'texture': mesh_data['texture'],
            'base_color': mesh_data['base_color'],
            'has_indices': mesh_data['indices'] is not None
        }
    """
    Create VAOs for all loaded meshes and store them in vao_list.
    """
    def prepare_for_rendering(self):
        self.vao_list = []
        for mesh_data in self.meshes:
            vao_data = self.create_vao(mesh_data)
            self.vao_list.append(vao_data)
    """
    Delete textures, VAOs, and buffers when shutting down the application.
    """
    def cleanup(self):
        for tex in self.textures.values():
            glDeleteTextures(1, [tex])

        for vao_data in self.vao_list:
            glDeleteVertexArrays(1, [vao_data['vao']])
            glDeleteBuffers(len(vao_data['vbos']), vao_data['vbos'])
            if vao_data['ibo']:
                glDeleteBuffers(1, [vao_data['ibo']])