"""
simulation.py  -  Ventana de simulacion animada para la linea de produccion.

Uso recomendado:
    simulador = SimulationWindow(linea, cantidad_productos)
    simulador.run()
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pygame


# Si se ejecuta este archivo directamente, asegura imports del proyecto.
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src" / "logic") not in sys.path:
    sys.path.insert(0, str(ROOT / "src" / "logic"))

from src.logic.clase_linea_produccion import LineaProduccion


# ------------------------------ Estilos y layout ------------------------------

WIN_W = 1360
WIN_H = 820

TOP_H = 72
FOOT_H = 64
PAD = 14
SCROLL_SZ = 14

PROC_W = 250
PROC_H = 90
PROC_GAP = 74

TASK_W = 210
TASK_H = 90
TASK_GAP = 28

PROD_SZ = 36

BG = (20, 22, 30)
BG_2 = (26, 29, 39)
PANEL = (34, 38, 49)
PANEL_2 = (42, 47, 60)
BORDER = (92, 98, 118)
TEXT = (228, 231, 239)
TEXT_DIM = (166, 173, 188)
ACCENT = (255, 202, 70)
GOOD = (80, 183, 95)
BAD = (199, 74, 74)
BTN = (77, 85, 108)
BTN_H = (98, 109, 136)
SCROLL_TRACK = (44, 48, 60)
SCROLL_THUMB = (97, 106, 130)


# --------------------------------- Widgets ---------------------------------


class Button:
    def __init__(self, rect, label, color=BTN):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.color = color
        self.hover = False

    def draw(self, surf, font):
        color = BTN_H if self.hover else self.color
        pygame.draw.rect(surf, color, self.rect, border_radius=6)
        pygame.draw.rect(surf, BORDER, self.rect, 1, border_radius=6)
        text = font.render(self.label, True, TEXT)
        surf.blit(text, text.get_rect(center=self.rect.center))

    def update_hover(self, pos):
        self.hover = self.rect.collidepoint(pos)

    def clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


class ScrollBar:
    def __init__(self, rect: pygame.Rect, vertical: bool):
        self.rect = rect
        self.vertical = vertical
        self.content_len = 1
        self.viewport_len = 1
        self.offset = 0.0

        self.dragging = False
        self.drag_mouse_origin = 0
        self.drag_offset_origin = 0.0

    @property
    def max_offset(self):
        return max(0.0, float(self.content_len - self.viewport_len))

    def set_lengths(self, content_len: int, viewport_len: int):
        self.content_len = max(1, int(content_len))
        self.viewport_len = max(1, int(viewport_len))
        self.offset = max(0.0, min(self.offset, self.max_offset))

    def scroll_pixels(self, delta: float):
        if self.max_offset <= 0:
            self.offset = 0.0
            return
        self.offset = max(0.0, min(self.max_offset, self.offset + delta))

    def _thumb_rect(self):
        if self.vertical:
            track_len = self.rect.h
        else:
            track_len = self.rect.w

        if self.content_len <= self.viewport_len:
            ratio = 1.0
        else:
            ratio = self.viewport_len / self.content_len

        thumb_len = max(28, int(track_len * ratio))
        travel = track_len - thumb_len

        if self.max_offset <= 0 or travel <= 0:
            thumb_pos = 0
        else:
            thumb_pos = int((self.offset / self.max_offset) * travel)

        if self.vertical:
            return pygame.Rect(self.rect.x, self.rect.y + thumb_pos, self.rect.w, thumb_len)
        return pygame.Rect(self.rect.x + thumb_pos, self.rect.y, thumb_len, self.rect.h)

    def handle(self, event):
        thumb = self._thumb_rect()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if thumb.collidepoint(event.pos):
                self.dragging = True
                self.drag_mouse_origin = event.pos[1] if self.vertical else event.pos[0]
                self.drag_offset_origin = self.offset
                return True
            if self.rect.collidepoint(event.pos):
                pos = event.pos[1] if self.vertical else event.pos[0]
                start = self.rect.y if self.vertical else self.rect.x
                ratio = (pos - start) / (self.rect.h if self.vertical else self.rect.w)
                self.offset = max(0.0, min(self.max_offset, ratio * self.max_offset))
                return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                return True

        if event.type == pygame.MOUSEMOTION and self.dragging:
            mouse_now = event.pos[1] if self.vertical else event.pos[0]
            delta = mouse_now - self.drag_mouse_origin
            thumb_now = self._thumb_rect()
            travel = (self.rect.h - thumb_now.h) if self.vertical else (self.rect.w - thumb_now.w)
            if travel > 0 and self.max_offset > 0:
                self.offset = max(
                    0.0,
                    min(self.max_offset, self.drag_offset_origin + delta * self.max_offset / travel),
                )
            return True

        return False

    def draw(self, surf):
        pygame.draw.rect(surf, SCROLL_TRACK, self.rect, border_radius=6)
        pygame.draw.rect(surf, BORDER, self.rect, 1, border_radius=6)
        thumb = self._thumb_rect()
        pygame.draw.rect(surf, SCROLL_THUMB, thumb, border_radius=6)


@dataclass
class ProductSprite:
    pid: int
    pos: pygame.Vector2
    start: pygame.Vector2
    target: pygame.Vector2
    elapsed_ms: float = 0.0
    duration_ms: float = 250.0
    visible: bool = True
    hide_on_arrival: bool = False

    def set_target(self, target_xy, duration_ms: float):
        self.start = self.pos.copy()
        self.target = pygame.Vector2(target_xy)
        self.elapsed_ms = 0.0
        self.duration_ms = max(1.0, float(duration_ms))

    def update(self, dt_ms: float):
        hidden_now = False
        if self.elapsed_ms < self.duration_ms:
            self.elapsed_ms = min(self.duration_ms, self.elapsed_ms + dt_ms)
            t = self.elapsed_ms / self.duration_ms
            eased = 1.0 - (1.0 - t) ** 3
            self.pos = self.start.lerp(self.target, eased)

        if self.hide_on_arrival and self.elapsed_ms >= self.duration_ms:
            self.visible = False
            self.hide_on_arrival = False
            hidden_now = True

        return hidden_now


# ------------------------------- Simulador UI -------------------------------


class SimulationWindow:
    def __init__(self, linea: LineaProduccion, cantidad_productos: int | None = None):
        pygame.init()

        self.screen = pygame.display.set_mode((WIN_W, WIN_H), pygame.RESIZABLE)
        pygame.display.set_caption("LinProd - Simulacion de la Linea")
        self.clock = pygame.time.Clock()

        self.screen_w, self.screen_h = self.screen.get_size()

        self.font_h = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.font = pygame.font.SysFont("Segoe UI", 17)
        self.font_sm = pygame.font.SysFont("Segoe UI", 14)

        self.linea = linea
        base_count = cantidad_productos if cantidad_productos is not None else linea.cantidad_ingreso
        self.cantidad_productos = max(1, int(base_count or 1))

        self.running = True
        self.next_action = "exit"
        self.playing = False
        self.cycle_ms = 460
        self.accumulator_ms = 0.0

        self.first_finished_id: int | None = None
        self.hidden_finished_count = 0
        self.completion_order: dict[int, int] = {}

        self.product_locations: dict[int, tuple] = {}
        self.product_sprites: dict[int, ProductSprite] = {}

        self.process_rects: list[pygame.Rect] = []
        self.task_rects: dict[tuple[int, int], pygame.Rect] = {}
        self.finish_rect = pygame.Rect(0, 0, 1, 1)

        self.view_rect = pygame.Rect(0, 0, 1, 1)

        self.world_w = 1
        self.world_h = 1
        self.world = pygame.Surface((self.world_w, self.world_h)).convert_alpha()

        self.hbar = ScrollBar(
            pygame.Rect(0, 0, 1, 1),
            vertical=False,
        )
        self.vbar = ScrollBar(
            pygame.Rect(0, 0, 1, 1),
            vertical=True,
        )

        self._refresh_viewport()

        self._load_assets()
        self._build_controls()
        self._rebuild_layout()
        self._reset_simulation()

    def _refresh_viewport(self):
        view_w = max(320, self.screen_w - PAD * 2 - SCROLL_SZ - 4)
        view_h = max(220, self.screen_h - (TOP_H + PAD * 2 + FOOT_H) - SCROLL_SZ)
        self.view_rect = pygame.Rect(PAD, TOP_H + PAD, view_w, view_h)

        self.hbar.rect = pygame.Rect(self.view_rect.x, self.view_rect.bottom + 4, self.view_rect.w, SCROLL_SZ)
        self.vbar.rect = pygame.Rect(self.view_rect.right + 4, self.view_rect.y, SCROLL_SZ, self.view_rect.h)

        self.hbar.set_lengths(self.world_w, self.view_rect.w)
        self.vbar.set_lengths(self.world_h, self.view_rect.h)

    def _maximize_to_monitor(self):
        info = pygame.display.Info()
        self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.RESIZABLE)
        self.screen_w, self.screen_h = self.screen.get_size()
        self._refresh_viewport()

    # ----------------------------- Inicializacion ----------------------------

    def _load_assets(self):
        assets_dir = Path(__file__).resolve().parent / "assets"

        def load_or_placeholder(path: Path, size: tuple[int, int], color: tuple[int, int, int]):
            try:
                image = pygame.image.load(str(path))
                image = image.convert_alpha() if image.get_alpha() is not None else image.convert()
            except Exception:
                image = pygame.Surface(size)
                image.fill(color)
            return pygame.transform.smoothscale(image, size)

        self.asset_proc = load_or_placeholder(assets_dir / "proceso.png", (PROC_W, PROC_H), (66, 85, 140))
        self.asset_task = load_or_placeholder(assets_dir / "tarea.png", (TASK_W, TASK_H), (90, 120, 160))
        self.asset_prod = load_or_placeholder(assets_dir / "producto.jpg", (PROD_SZ, PROD_SZ), (213, 171, 82))

    def _build_controls(self):
        y = 16
        x = 16
        self.btn_toggle = Button((x, y, 130, 40), "Iniciar", GOOD)
        x += 140
        self.btn_reset = Button((x, y, 118, 40), "Reiniciar", BTN)
        x += 128
        self.btn_reconfigure = Button((x, y, 140, 40), "Reconfigurar", BTN)
        x += 150
        self.btn_maximize = Button((x, y, 120, 40), "Maximizar", BTN)
        x += 130
        self.btn_exit = Button((x, y, 94, 40), "Salir", BAD)

        self.buttons = [
            self.btn_toggle,
            self.btn_reset,
            self.btn_reconfigure,
            self.btn_maximize,
            self.btn_exit,
        ]

    def _rebuild_layout(self):
        procesos = self.linea.procesos
        max_tareas = max((len(p.tareas) for p in procesos), default=1)

        start_x = 60
        header_y = 54
        tasks_y = header_y + PROC_H + 34

        width_line = len(procesos) * PROC_W + max(0, len(procesos) - 1) * PROC_GAP
        finish_w = 250
        world_w = start_x + width_line + PROC_GAP + finish_w + 80
        world_h = tasks_y + max_tareas * (TASK_H + TASK_GAP) + 90

        self.world_w = max(world_w, self.view_rect.w)
        self.world_h = max(world_h, self.view_rect.h)
        self.world = pygame.Surface((self.world_w, self.world_h)).convert_alpha()

        self.process_rects = []
        self.task_rects = {}

        for i, proceso in enumerate(procesos):
            px = start_x + i * (PROC_W + PROC_GAP)
            pr = pygame.Rect(px, header_y, PROC_W, PROC_H)
            self.process_rects.append(pr)

            for j, _ in enumerate(proceso.tareas):
                tx = px + (PROC_W - TASK_W) // 2
                ty = tasks_y + j * (TASK_H + TASK_GAP)
                self.task_rects[(i, j)] = pygame.Rect(tx, ty, TASK_W, TASK_H)

        fx = start_x + width_line + PROC_GAP
        fh = max(TASK_H * 2, max_tareas * (TASK_H + TASK_GAP) - TASK_GAP)
        self.finish_rect = pygame.Rect(fx, tasks_y, finish_w, fh)

        self.hbar.set_lengths(self.world_w, self.view_rect.w)
        self.vbar.set_lengths(self.world_h, self.view_rect.h)

    def _reset_simulation(self):
        self.linea.reiniciar(self.cantidad_productos)
        self.linea.pausar()

        self.playing = False
        self.accumulator_ms = 0.0

        self.first_finished_id = None
        self.hidden_finished_count = 0
        self.completion_order.clear()

        self.product_locations = self._capture_locations()
        self.product_sprites.clear()

        for producto in self.linea.productos:
            pid = producto.id
            loc = self.product_locations.get(pid)
            pos = pygame.Vector2(self._location_to_point(pid, loc))
            self.product_sprites[pid] = ProductSprite(pid, pos, pos.copy(), pos.copy())

        self.hbar.offset = 0.0
        self.vbar.offset = 0.0

    # ---------------------------- Estado y animacion --------------------------

    def _capture_locations(self):
        mapping: dict[int, tuple] = {}

        for pi, proceso in enumerate(self.linea.procesos):
            for ti, tarea in enumerate(proceso.tareas):
                if tarea.producto_actual is not None:
                    mapping[tarea.producto_actual.id] = ("task", pi, ti, 0)
                for qi, prod in enumerate(tarea.contenido_esperando):
                    mapping[prod.id] = ("queue", pi, ti, qi)

        for prod in self.linea.productos:
            if prod.estado == "finalizado":
                mapping[prod.id] = ("final", -1, -1, -1)

        return mapping

    def _task_center(self, pi: int, ti: int):
        rect = self.task_rects[(pi, ti)]
        return rect.centerx, rect.centery

    def _queue_slot(self, pi: int, ti: int, qi: int):
        rect = self.task_rects[(pi, ti)]
        x = rect.left - 30 - qi * 28
        y = rect.centery
        x = max(20, x)
        return x, y

    def _finish_slot(self, pid: int):
        order = self.completion_order.get(pid, 0)
        # El primer producto queda visible al lado del ultimo proceso.
        if order == 0:
            return self.finish_rect.left + 64, self.finish_rect.top + 54

        idx = order - 1
        row = idx % 8
        col = idx // 8
        x = self.finish_rect.left + 150 + col * 26
        y = self.finish_rect.top + 40 + row * 26
        return x, y

    def _location_to_point(self, pid: int, loc: tuple | None):
        if not loc:
            if self.process_rects:
                first_proc = self.process_rects[0]
                return first_proc.left - 30, first_proc.top + PROC_H // 2
            return 50, 50

        kind, pi, ti, extra = loc
        if kind == "task":
            return self._task_center(pi, ti)
        if kind == "queue":
            return self._queue_slot(pi, ti, extra)
        if kind == "final":
            return self._finish_slot(pid)

        return 50, 50

    def _register_finished(self, newly_finished: list[int]):
        for pid in newly_finished:
            if pid in self.completion_order:
                continue

            self.completion_order[pid] = len(self.completion_order)
            sprite = self.product_sprites.get(pid)
            if sprite is None:
                continue

            if self.first_finished_id is None:
                self.first_finished_id = pid
                sprite.visible = True
                sprite.hide_on_arrival = False
            else:
                sprite.visible = True
                sprite.hide_on_arrival = True

    def _advance_tick(self):
        old_locs = self.product_locations

        self.linea.reanudar()
        self.linea.tick()
        self.linea.pausar()

        new_locs = self._capture_locations()

        newly_finished = [
            pid
            for pid, loc in new_locs.items()
            if loc[0] == "final" and (pid not in old_locs or old_locs[pid][0] != "final")
        ]
        if newly_finished:
            self._register_finished(sorted(newly_finished))

        anim_ms = max(150, min(500, int(self.cycle_ms * 0.88)))

        for pid, sprite in self.product_sprites.items():
            loc = new_locs.get(pid)
            old = old_locs.get(pid)
            target = self._location_to_point(pid, loc)

            if old != loc:
                sprite.set_target(target, anim_ms)
            elif sprite.elapsed_ms >= sprite.duration_ms:
                sprite.pos = pygame.Vector2(target)
                sprite.start = sprite.pos.copy()
                sprite.target = sprite.pos.copy()

        self.product_locations = new_locs

        if self.linea.todos_finalizados():
            self.playing = False

    # -------------------------------- Eventos --------------------------------

    def _toggle_play(self):
        if self.linea.todos_finalizados():
            return
        self.playing = not self.playing
        if not self.playing:
            self.linea.pausar()
            self.linea.imprimir_estado()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.VIDEORESIZE:
                self.screen_w = event.w
                self.screen_h = event.h
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                self._refresh_viewport()
                continue

            if event.type == pygame.MOUSEMOTION:
                for button in self.buttons:
                    button.update_hover(event.pos)

            # Scrollbars primero para capturar drag.
            used_scroll = self.hbar.handle(event) or self.vbar.handle(event)
            if used_scroll:
                continue

            if event.type == pygame.MOUSEWHEEL:
                mouse = pygame.mouse.get_pos()
                if self.view_rect.collidepoint(mouse):
                    mods = pygame.key.get_mods()
                    if mods & pygame.KMOD_SHIFT:
                        self.hbar.scroll_pixels(-event.y * 70)
                    else:
                        self.vbar.scroll_pixels(-event.y * 70)

            if self.btn_toggle.clicked(event):
                self._toggle_play()
            elif self.btn_reset.clicked(event):
                self._reset_simulation()
            elif self.btn_reconfigure.clicked(event):
                self.next_action = "reconfigure"
                self.running = False
            elif self.btn_maximize.clicked(event):
                self._maximize_to_monitor()
            elif self.btn_exit.clicked(event):
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self._toggle_play()
                elif event.key == pygame.K_r:
                    self._reset_simulation()
                elif event.key == pygame.K_F11:
                    self._maximize_to_monitor()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False

    # -------------------------------- Dibujo ---------------------------------

    def _draw_top(self):
        pygame.draw.rect(self.screen, BG_2, (0, 0, self.screen_w, TOP_H))
        pygame.draw.line(self.screen, BORDER, (0, TOP_H - 1), (self.screen_w, TOP_H - 1), 1)

        if self.playing:
            self.btn_toggle.label = "Pausar"
            self.btn_toggle.color = BAD
        else:
            if self.linea.tiempo_actual == 0:
                self.btn_toggle.label = "Iniciar"
            elif self.linea.todos_finalizados():
                self.btn_toggle.label = "Finalizado"
            else:
                self.btn_toggle.label = "Reanudar"
            self.btn_toggle.color = GOOD

        for button in self.buttons:
            button.draw(self.screen, self.font)

        estado = "RUN" if self.playing else "PAUSA"
        txt = self.font.render(
            f"T={self.linea.tiempo_actual}   Estado={estado}",
            True,
            ACCENT,
        )
        self.screen.blit(txt, (max(16, self.screen_w - 320), 26))

    def _draw_world(self):
        self.world.fill(PANEL)

        # separadores sutiles de fondo
        for y in range(0, self.world_h, 48):
            pygame.draw.line(self.world, (39, 43, 55), (0, y), (self.world_w, y), 1)

        # lineas entre procesos
        for i in range(len(self.process_rects) - 1):
            a = self.process_rects[i]
            b = self.process_rects[i + 1]
            y = a.centery
            pygame.draw.line(self.world, ACCENT, (a.right + 10, y), (b.left - 10, y), 3)
            pygame.draw.polygon(
                self.world,
                ACCENT,
                [(b.left - 10, y), (b.left - 20, y - 6), (b.left - 20, y + 6)],
            )

        for pi, proceso in enumerate(self.linea.procesos):
            pr = self.process_rects[pi]
            self.world.blit(self.asset_proc, pr.topleft)
            pygame.draw.rect(self.world, BORDER, pr, 2, border_radius=12)

            flags = []
            if proceso.es_inicial:
                flags.append("INICIAL")
            if proceso.es_final:
                flags.append("FINAL")
            mark = f" ({', '.join(flags)})" if flags else ""

            title = self.font.render(proceso.nombre + mark, True, TEXT)
            self.world.blit(title, (pr.x + 12, pr.y + 10))

            subt = self.font_sm.render(f"Tareas: {len(proceso.tareas)}", True, TEXT_DIM)
            self.world.blit(subt, (pr.x + 12, pr.y + 44))

            for ti, tarea in enumerate(proceso.tareas):
                tr = self.task_rects[(pi, ti)]
                self.world.blit(self.asset_task, tr.topleft)
                pygame.draw.rect(self.world, BORDER, tr, 2, border_radius=10)

                if tarea.esta_procesando:
                    overlay = pygame.Surface((tr.w, tr.h), pygame.SRCALPHA)
                    overlay.fill((56, 145, 69, 70))
                    self.world.blit(overlay, tr.topleft)

                t1 = self.font_sm.render(tarea.nombre, True, TEXT)
                t2 = self.font_sm.render(
                    f"TP={tarea.tiempo_proceso}  EP={'S' if tarea.esta_procesando else 'N'}  CE={tarea.cantidad_en_espera()}",
                    True,
                    TEXT_DIM,
                )
                self.world.blit(t1, (tr.x + 10, tr.y + 10))
                self.world.blit(t2, (tr.x + 10, tr.y + 38))

        # panel de finalizados
        pygame.draw.rect(self.world, PANEL_2, self.finish_rect, border_radius=12)
        pygame.draw.rect(self.world, BORDER, self.finish_rect, 2, border_radius=12)
        fin_title = self.font.render("Finalizados", True, ACCENT)
        self.world.blit(fin_title, (self.finish_rect.x + 16, self.finish_rect.y + 14))

        fin_total = sum(1 for p in self.linea.productos if p.estado == "finalizado")
        fin_txt = self.font_sm.render(f"Total: {fin_total}/{len(self.linea.productos)}", True, TEXT)
        self.world.blit(fin_txt, (self.finish_rect.x + 16, self.finish_rect.y + 44))

        if self.first_finished_id is not None:
            ptxt = self.font_sm.render(f"Visible: Producto {self.first_finished_id}", True, TEXT_DIM)
            self.world.blit(ptxt, (self.finish_rect.x + 16, self.finish_rect.y + 68))

        if self.hidden_finished_count > 0:
            htxt = self.font_sm.render(f"Ocultos: {self.hidden_finished_count}", True, TEXT_DIM)
            self.world.blit(htxt, (self.finish_rect.x + 16, self.finish_rect.y + 90))

        # productos animados
        for sprite in self.product_sprites.values():
            if not sprite.visible:
                continue
            rect = self.asset_prod.get_rect(center=(int(sprite.pos.x), int(sprite.pos.y)))
            self.world.blit(self.asset_prod, rect.topleft)
            id_txt = self.font_sm.render(str(sprite.pid), True, (25, 25, 25))
            self.world.blit(id_txt, id_txt.get_rect(center=rect.center))

    def _draw_footer(self):
        y = self.screen_h - FOOT_H
        pygame.draw.rect(self.screen, BG_2, (0, y, self.screen_w, FOOT_H))
        pygame.draw.line(self.screen, BORDER, (0, y), (self.screen_w, y), 1)

        total = len(self.linea.productos)
        fin = sum(1 for p in self.linea.productos if p.estado == "finalizado")
        ocupadas = sum(
            1
            for proceso in self.linea.procesos
            for tarea in proceso.tareas
            if tarea.esta_procesando
        )

        txt = self.font.render(
            f"Productos finalizados: {fin}/{total}    Tareas ocupadas: {ocupadas}    Scroll X={int(self.hbar.offset)} Y={int(self.vbar.offset)}",
            True,
            TEXT,
        )
        self.screen.blit(txt, (16, y + 20))

    def draw(self):
        self.screen.fill(BG)

        self._draw_top()
        self._draw_world()

        src = pygame.Rect(int(self.hbar.offset), int(self.vbar.offset), self.view_rect.w, self.view_rect.h)
        self.screen.blit(self.world, self.view_rect.topleft, src)

        pygame.draw.rect(self.screen, BORDER, self.view_rect, 2)
        self.hbar.draw(self.screen)
        self.vbar.draw(self.screen)

        self._draw_footer()
        pygame.display.flip()

    # --------------------------------- Loop ----------------------------------

    def run(self):
        while self.running:
            dt = self.clock.tick(60)
            self._handle_events()

            if self.playing and not self.linea.todos_finalizados():
                self.accumulator_ms += dt
                while self.accumulator_ms >= self.cycle_ms:
                    self._advance_tick()
                    self.accumulator_ms -= self.cycle_ms
            else:
                self.accumulator_ms = min(self.accumulator_ms, self.cycle_ms)

            for sprite in self.product_sprites.values():
                hidden_now = sprite.update(dt)
                if hidden_now:
                    self.hidden_finished_count += 1

            self.draw()

        pygame.quit()
        return self.next_action


# ------------------------------- Ejecucion local -----------------------------


def main():
    from src.interface.config_window import ConfigWindow

    while True:
        config = ConfigWindow()
        linea = config.run()
        if linea is None:
            print("Configuracion cancelada.")
            return None

        sim = SimulationWindow(linea, cantidad_productos=max(1, linea.cantidad_ingreso or 1))
        action = sim.run()
        if action == "reconfigure":
            continue
        return linea


if __name__ == "__main__":
    main()
