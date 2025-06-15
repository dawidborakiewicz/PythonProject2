import pygame
from pygame.locals import DOUBLEBUF, OPENGL, K_ESCAPE, K_TAB, K_r, K_h, K_f, K_l
from glm import perspective, radians, rotate, mat4, vec3
from context import init_context
from shaders import create_shader
from textures import load_atlas
from particles_with_heightmap import ParticleSystemWithHeightMap
from renderer import Renderer
from camera import Camera
from config import FLIGHT_FRAME_T, X_MIN, X_MAX, Y_MIN, Y_MAX

from scene_loader import GLTFScene
from scene_shaders import create_scene_shader
from scene_renderer import SceneRenderer
from height_map import HeightMap

from OpenGL.GL import *
from skybox_renderer import SkyboxRenderer
import os


def main():
    # 1) Init window + GL context
    init_context(800, 600, "Deszcz Point-Sprite z Kolizjami")

    # 2) Load rain resources
    rain_shader = create_shader()
    atlas_tex = load_atlas("atlas40.png")
    psys = ParticleSystemWithHeightMap()  # Używamy nowego systemu
    rain_renderer = Renderer(rain_shader, psys, atlas_tex)
    skybox = SkyboxRenderer("sky/skymap.png", 0.4)

    # 3) Load scene
    scene = GLTFScene()
    height_map = None
    try:
        print("Ładowanie sceny...")
        scene.load('scene/scene2.gltf')
        scene.prepare_for_rendering()
        scene_shader = create_scene_shader()
        scene_renderer = SceneRenderer(scene_shader, scene)
        scene_renderer.set_lighting(
            light_pos=vec3(2.0, 4.0, 3.0),  # niższe, bardziej rozproszone
            light_color=vec3(0.5, 0.5, 0.6),  # zimniejsze, lekko niebieskawe
            ambient_color=vec3(0.2, 0.2, 0.25)  # ciemniejsze, pochmurne niebo
        )
        scene_loaded = True
        print(f"Załadowano scenę: {len(scene.vao_list)} obiektów")

        # 4) Generuj mapę wysokości z lepszymi ustawieniami
        model_matrix = rotate(mat4(1.0), radians(90), vec3(1, 0, 0))

        # ZMNIEJSZ ROZDZIELCZOŚĆ dla szybszego generowania
        resolution = 0.8  # Było 0.3, teraz 0.8 - mniej punktów
        height_map = HeightMap(X_MIN, X_MAX, Y_MIN, Y_MAX, resolution=resolution)

        # Sprawdź czy istnieje zapisana mapa wysokości
        heightmap_cache = f"heightmap_cache_{resolution}.npy"
        if os.path.exists(heightmap_cache):
            print("Wczytywanie mapy wysokości z cache...")
            height_map.load_from_file(heightmap_cache)
        else:
            print("Generowanie nowej mapy wysokości...")
            print("UWAGA: To może potrwać kilka minut przy pierwszym uruchomieniu!")
            print("Możesz przerwać (Ctrl+C) i uruchomić ponownie z większą rozdzielczością później.")

            try:
                height_map.generate_from_scene(scene, model_matrix)
                height_map.save_to_file(heightmap_cache)
                print("Mapa wysokości zapisana do cache!")
            except KeyboardInterrupt:
                print("\nGenerowanie przerwane przez użytkownika!")
                print("Używam płaskiej mapy wysokości...")
                height_map = None

        # Przekaż mapę wysokości do systemu cząstek
        psys.set_height_map(height_map)

        if height_map:
            print("Mapa wysokości gotowa!")
            print("Informacje o mapie:")
            for key, value in height_map.get_debug_info().items():
                print(f"  {key}: {value}")
        else:
            print("Używam domyślnej płaskiej powierzchni (Z=1.0)")

    except Exception as e:
        print(f"Błąd ładowania sceny: {e}")
        scene_loaded = False

    # 5) Setup camera control
    camera = Camera()
    camera_enabled = True
    rain_enabled = True
    show_stats = False

    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    pygame.mouse.get_rel()  # flush motion

    # 6) Projection
    proj = perspective(radians(45.0), 800 / 600, 0.1, 200.0)

    # 7) Main loop
    clock = pygame.time.Clock()
    running = True
    frame_count = 0
    stats_timer = 0.0

    print("\nSterowanie:")
    print("ESC - wyjście")
    print("TAB - włącz/wyłącz kontrolę kamery")
    print("R - włącz/wyłącz deszcz")
    print("H - regeneruj mapę wysokości (UWAGA: długa operacja!)")
    print("F - pokaż/ukryj statystyki")
    print("L - zapisz mapę wysokości")
    print("WSAD - ruch kamery")
    print("Spacja - w górę, Shift - w dół")

    while running:
        dt = clock.tick(60) / 1000.0
        frame_count += 1
        stats_timer += dt

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == K_ESCAPE:
                    running = False
                elif e.key == K_TAB:
                    camera_enabled = not camera_enabled
                    pygame.mouse.set_visible(not camera_enabled)
                    pygame.event.set_grab(camera_enabled)
                    pygame.mouse.get_rel()  # flush motion
                    print(f"Kontrola kamery: {'włączona' if camera_enabled else 'wyłączona'}")
                elif e.key == K_r:
                    rain_enabled = not rain_enabled
                    print(f"Deszcz: {'włączony' if rain_enabled else 'wyłączony'}")
                elif e.key == K_h and height_map and scene_loaded:
                    print("UWAGA: Regenerowanie mapy wysokości może zająć kilka minut!")
                    response = input("Czy kontynuować? (y/N): ")
                    if response.lower() == 'y':
                        print("Regenerowanie mapy wysokości...")
                        model_matrix = rotate(mat4(1.0), radians(90), vec3(1, 0, 0))
                        height_map.generate_from_scene(scene, model_matrix)
                        psys.set_height_map(height_map)
                        print("Mapa wysokości zregenerowana!")
                elif e.key == K_f:
                    show_stats = not show_stats
                    print(f"Statystyki: {'włączone' if show_stats else 'wyłączone'}")
                elif e.key == K_l and height_map:
                    height_map.save_to_file("heightmap_manual.npy")

        # Camera input
        if camera_enabled:
            dx, dy = pygame.mouse.get_rel()
            camera.process_mouse_delta(dx, dy)

        keys = pygame.key.get_pressed()
        if camera_enabled:
            camera.process_keyboard(keys, dt)

        # Update systems
        if rain_enabled:
            psys.update(dt)

        # Pokaż statystyki co sekundę
        if show_stats and stats_timer >= 1.0:
            stats = psys.get_stats()
            print(
                f"FPS: {frame_count / stats_timer:.1f} | Cząstki: {stats['flying_particles']} lecące, {stats['splashing_particles']} splash | Wysokości: {stats['height_range']}")
            stats_timer = 0.0
            frame_count = 0

        flightFrame = int((pygame.time.get_ticks() / 1000.0 / FLIGHT_FRAME_T) % 2)

        # Render
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.1, 0.1, 0.1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        view = camera.get_view_matrix()

        skybox.render(proj, view)

        # Render scene
        if scene_loaded:
            model_matrix = rotate(mat4(1.0), radians(90), vec3(1, 0, 0))
            scene_renderer.set_model_matrix(model_matrix)
            scene_renderer.render(proj, view, camera.position)

        # Render rain
        if rain_enabled:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            rain_renderer.render(proj, view, flightFrame)
            glDisable(GL_BLEND)

        pygame.display.flip()

    # Cleanup
    skybox.cleanup()
    if scene_loaded:
        scene.cleanup()

    pygame.quit()


if __name__ == '__main__':
    main()