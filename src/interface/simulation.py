"""
simulation.py  -  Ventana de simulacion animada para la linea de produccion.

Uso recomendado:
    simulador = SimulationWindow(linea, cantidad_productos)
    simulador.run()
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pygame

# Si se ejecuta este archivo directamente, asegura imports del proyecto.
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src" / "logic") not in sys.path:
    sys.path.insert(0, str(ROOT / "src" / "logic"))

from src.interface.final_report import FinalReportWindow
from src.logic.clase_linea_produccion import LineaProduccion

# ------------------------------ Estilos y layout ------------------------------

WIN_W = 1360
WIN_H = 820

OUTER_PAD = 14
INNER_PAD = 16
SIDEBAR_W = 336
SCROLL_SZ = 14

PROC_W = 250
PROC_H = 90
PROC_GAP = 74

TASK_W = 210
TASK_H = 90
TASK_GAP = 28

PROD_SZ = 30

PROC_FILL = (3, 1, 76)  # #03014C
PROC_TEXT = (242, 246, 255)
PROC_META = (197, 206, 244)

TASK_IDLE_FILL = (83, 79, 252)  # #534FFC
TASK_IDLE_TEXT = (244, 246, 255)
TASK_IDLE_META = (212, 219, 255)

TASK_ACTIVE_FILL = (243, 248, 255)  # #F3F8FF
TASK_ACTIVE_BORDER = (174, 173, 254)  # #AEADFE
TASK_ACTIVE_TEXT = (50, 57, 78)
TASK_ACTIVE_META = (139, 148, 170)

PAGE_BG = (210, 210, 210)
SIDEBAR_BG = (246, 247, 250)
PANEL_BG = (244, 246, 250)
CARD_BG = (233, 238, 248)
CARD_SOFT = (239, 242, 249)
PANEL_BORDER = (208, 214, 225)

TEXT_DARK = (34, 38, 49)
TEXT_MID = (74, 82, 96)
TEXT_SOFT = (130, 138, 152)
TEXT_LIGHT = (245, 248, 252)

ACCENT = (44, 84, 209)
ACCENT_H = (56, 96, 222)
GOOD = (56, 153, 82)
GOOD_H = (68, 166, 94)
BAD = (189, 70, 70)
BAD_H = (203, 84, 84)

BTN_NEUTRAL = (223, 229, 241)
BTN_NEUTRAL_H = (211, 220, 238)
BTN_BORDER = (186, 197, 220)

BTN_DEEP_BLUE = (17, 48, 159)  # #11309F
BTN_DEEP_BLUE_H = (27, 60, 173)
BTN_DEEP_BLUE_B = (14, 39, 126)

BTN_SOFT_BLUE = (208, 222, 245)  # #D0DEF5
BTN_SOFT_BLUE_H = (197, 213, 240)
BTN_SOFT_BLUE_B = (167, 188, 228)
BTN_SOFT_BLUE_TXT = (41, 82, 225)  # #2952E1

BTN_LIGHT = (246, 246, 246)  # #F6F6F6
BTN_LIGHT_H = (237, 237, 237)
BTN_LIGHT_B = (214, 214, 214)
BTN_LIGHT_TXT = (44, 44, 44)  # #2C2C2C

BTN_DARK = (44, 44, 44)  # #2C2C2C
BTN_DARK_H = (58, 58, 58)
BTN_DARK_B = (30, 30, 30)

SCROLL_TRACK = (211, 220, 236)
SCROLL_THUMB = (150, 167, 204)


def _draw_rounded_rect(
    surf: pygame.Surface,
    rect: pygame.Rect,
    color: tuple[int, int, int] | tuple[int, int, int, int] | None,
    radius: int,
    border_color: tuple[int, int, int] | tuple[int, int, int, int] | None = None,
    border_width: int = 0,
):
    if rect.w <= 0 or rect.h <= 0:
        return
    if color is not None:
        pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border_color is not None and border_width > 0:
        pygame.draw.rect(surf, border_color, rect, border_width, border_radius=radius)


# --------------------------------- Widgets ---------------------------------


class ActionButton:
    def __init__(
        self,
        label: str,
        fill: tuple[int, int, int],
        text_color: tuple[int, int, int],
        hover_fill: tuple[int, int, int] | None = None,
        border: tuple[int, int, int] | None = None,
    ):
        self.label = label
        self.fill = fill
        self.hover_fill = hover_fill if hover_fill is not None else fill
        self.border = border if border is not None else fill
        self.text_color = text_color

        self.disabled_fill = (227, 231, 239)
        self.disabled_border = (199, 205, 218)
        self.disabled_text = (141, 149, 165)

        self.rect = pygame.Rect(0, 0, 1, 1)
        self.hover = False
        self.enabled = True

    def set_rect(self, rect: pygame.Rect):
        self.rect = pygame.Rect(rect)

    def update_hover(self, pos: tuple[int, int]):
        self.hover = self.enabled and self.rect.collidepoint(pos)

    def clicked(self, event: pygame.event.Event) -> bool:
        return (
            self.enabled
            and event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )

    def _palette(self):
        if not self.enabled:
            return self.disabled_fill, self.disabled_border, self.disabled_text

        color = self.hover_fill if self.hover else self.fill
        return color, self.border, self.text_color

    def draw(self, surf: pygame.Surface, font: pygame.font.Font):
        fill, border, txt_color = self._palette()
        _draw_rounded_rect(
            surf,
            self.rect,
            fill,
            radius=10,
            border_color=border,
            border_width=1,
        )
        text = font.render(self.label, True, txt_color)
        surf.blit(text, text.get_rect(center=self.rect.center))


class ScrollBar:
    def __init__(self, rect: pygame.Rect, vertical: bool):
        self.rect = pygame.Rect(rect)
        self.vertical = vertical

        self.content_len = 1
        self.viewport_len = 1
        self.offset = 0.0

        self.dragging = False
        self.drag_mouse_origin = 0
        self.drag_offset_origin = 0.0

    @property
    def max_offset(self) -> float:
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

    def _thumb_rect(self) -> pygame.Rect:
        track_len = self.rect.h if self.vertical else self.rect.w
        ratio = (
            1.0
            if self.content_len <= self.viewport_len
            else self.viewport_len / self.content_len
        )
        thumb_len = max(28, int(track_len * ratio))
        travel = track_len - thumb_len

        if self.max_offset <= 0 or travel <= 0:
            thumb_pos = 0
        else:
            thumb_pos = int((self.offset / self.max_offset) * travel)

        if self.vertical:
            return pygame.Rect(
                self.rect.x,
                self.rect.y + thumb_pos,
                self.rect.w,
                thumb_len,
            )
        return pygame.Rect(
            self.rect.x + thumb_pos,
            self.rect.y,
            thumb_len,
            self.rect.h,
        )

    def handle(self, event: pygame.event.Event) -> bool:
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
                ratio = (pos - start) / (
                    self.rect.h if self.vertical else max(1, self.rect.w)
                )
                self.offset = max(0.0, min(self.max_offset, ratio * self.max_offset))
                return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            return True

        if event.type == pygame.MOUSEMOTION and self.dragging:
            mouse_now = event.pos[1] if self.vertical else event.pos[0]
            delta = mouse_now - self.drag_mouse_origin

            thumb_now = self._thumb_rect()
            travel = (
                self.rect.h - thumb_now.h
                if self.vertical
                else self.rect.w - thumb_now.w
            )

            if travel > 0 and self.max_offset > 0:
                self.offset = max(
                    0.0,
                    min(
                        self.max_offset,
                        self.drag_offset_origin + delta * self.max_offset / travel,
                    ),
                )
            return True

        return False

    def draw(self, surf: pygame.Surface):
        _draw_rounded_rect(
            surf,
            self.rect,
            SCROLL_TRACK,
            radius=6,
            border_color=PANEL_BORDER,
            border_width=1,
        )
        thumb = self._thumb_rect()
        _draw_rounded_rect(surf, thumb, SCROLL_THUMB, radius=6)


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

    def set_target(self, target_xy: tuple[int, int], duration_ms: float):
        self.start = self.pos.copy()
        self.target = pygame.Vector2(target_xy)
        self.elapsed_ms = 0.0
        self.duration_ms = max(1.0, float(duration_ms))

    def update(self, dt_ms: float) -> bool:
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

        self.font_title = pygame.font.SysFont("Segoe UI", 46, bold=True)
        self.font_h = pygame.font.SysFont("Segoe UI", 27, bold=True)
        self.font = pygame.font.SysFont("Segoe UI", 18)
        self.font_b = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.font_sm = pygame.font.SysFont("Segoe UI", 14)
        self.font_proc_name = pygame.font.SysFont("Segoe UI", 19, bold=True)
        self.font_proc_meta = pygame.font.SysFont("Segoe UI", 8)
        self.font_task_name = pygame.font.SysFont("Segoe UI", 16)
        self.font_task_meta = pygame.font.SysFont("Segoe UI", 8)

        self.linea = linea
        base_count = (
            cantidad_productos
            if cantidad_productos is not None
            else linea.cantidad_ingreso
        )
        self.cantidad_productos = max(1, int(base_count or 1))

        self.running = True
        self.next_action = "exit"
        self.finish_reason: str | None = None
        self.playing = False
        self.cycle_ms = 460
        self.accumulator_ms = 0.0

        self.first_finished_id: int | None = None
        self.hidden_finished_count = 0
        self.completion_order: dict[int, int] = {}

        self.product_locations: dict[int, tuple] = {}
        self.product_sprites: dict[int, ProductSprite] = {}

        self.sidebar_rect = pygame.Rect(0, 0, 1, 1)
        self.sim_panel_rect = pygame.Rect(0, 0, 1, 1)
        self.summary_rect = pygame.Rect(0, 0, 1, 1)
        self.metadata_rect = pygame.Rect(0, 0, 1, 1)
        self.legend_rect = pygame.Rect(0, 0, 1, 1)

        self.process_rects: list[pygame.Rect] = []
        self.task_rects: dict[tuple[int, int], pygame.Rect] = {}
        self.finish_rect = pygame.Rect(0, 0, 1, 1)

        self.view_rect = pygame.Rect(0, 0, 1, 1)

        self.world_w = 1
        self.world_h = 1
        self.world = pygame.Surface((self.world_w, self.world_h)).convert_alpha()
        self._view_bg_cache_size = (-1, -1)
        self._view_bg_cache: pygame.Surface | None = None

        self.hbar = ScrollBar(pygame.Rect(0, 0, 1, 1), vertical=False)
        self.vbar = ScrollBar(pygame.Rect(0, 0, 1, 1), vertical=True)

        self.toast_message = ""
        self.toast_deadline_ms = 0

        self._load_assets()
        self._build_controls()
        self._refresh_layout()
        self._rebuild_layout()
        self._reset_simulation()

    # ----------------------------- Inicializacion ----------------------------

    def _load_image(self, path: Path) -> pygame.Surface | None:
        try:
            image = pygame.image.load(str(path))
            return (
                image.convert_alpha()
                if image.get_alpha() is not None
                else image.convert()
            )
        except Exception:
            return None

    def _set_window_icon(self):
        icon = self._load_image(self.assets_dir / "Iconos" / "Icon Logo.png")
        if icon is None:
            return
        pygame.display.set_icon(pygame.transform.smoothscale(icon, (32, 32)))

    def _load_assets(self):
        self.assets_dir = Path(__file__).resolve().parent / "assets"
        self._set_window_icon()

        def load_or_placeholder(
            path: Path,
            size: tuple[int, int],
            color: tuple[int, int, int],
        ) -> pygame.Surface:
            image = self._load_image(path)
            if image is None:
                placeholder = pygame.Surface(size, pygame.SRCALPHA)
                pygame.draw.circle(
                    placeholder,
                    color,
                    (size[0] // 2, size[1] // 2),
                    max(6, min(size) // 3),
                )
                image = placeholder
            return pygame.transform.smoothscale(image, size)

        self.asset_queue_icon = load_or_placeholder(
            self.assets_dir / "Iconos" / "Icon En cola.png",
            (PROD_SZ, PROD_SZ),
            (14, 14, 106),
        )
        self.asset_process_icon = load_or_placeholder(
            self.assets_dir / "Iconos" / "Icon Proceso.png",
            (PROD_SZ, PROD_SZ),
            (113, 195, 45),
        )

    @staticmethod
    def _cover_surface(
        image: pygame.Surface, width: int, height: int
    ) -> pygame.Surface:
        iw, ih = image.get_size()
        if iw <= 0 or ih <= 0 or width <= 0 or height <= 0:
            return pygame.Surface((max(1, width), max(1, height)))

        scale = max(width / iw, height / ih)
        scaled_w = max(1, int(iw * scale))
        scaled_h = max(1, int(ih * scale))
        scaled = pygame.transform.smoothscale(image, (scaled_w, scaled_h))

        crop_x = max(0, (scaled_w - width) // 2)
        crop_y = max(0, (scaled_h - height) // 2)
        return scaled.subsurface(pygame.Rect(crop_x, crop_y, width, height)).copy()

    def _get_view_background(self) -> pygame.Surface:
        size = (self.view_rect.w, self.view_rect.h)
        if self._view_bg_cache is None or self._view_bg_cache_size != size:
            self._view_bg_cache = pygame.Surface(size)
            self._view_bg_cache.fill(BTN_SOFT_BLUE)
            self._view_bg_cache_size = size
        return self._view_bg_cache

    def _build_controls(self):
        self.btn_start = ActionButton(
            "Iniciar",
            fill=BTN_SOFT_BLUE,
            text_color=BTN_SOFT_BLUE_TXT,
            hover_fill=BTN_SOFT_BLUE_H,
            border=BTN_SOFT_BLUE_B,
        )
        self.btn_pause = ActionButton(
            "Pausar",
            fill=BTN_DEEP_BLUE,
            text_color=TEXT_LIGHT,
            hover_fill=BTN_DEEP_BLUE_H,
            border=BTN_DEEP_BLUE_B,
        )
        self.btn_reconfigure = ActionButton(
            "ReConfigurar",
            fill=BTN_SOFT_BLUE,
            text_color=BTN_SOFT_BLUE_TXT,
            hover_fill=BTN_SOFT_BLUE_H,
            border=BTN_SOFT_BLUE_B,
        )
        self.btn_snapshot = ActionButton(
            "Tomar Foto",
            fill=BTN_DEEP_BLUE,
            text_color=TEXT_LIGHT,
            hover_fill=BTN_DEEP_BLUE_H,
            border=BTN_DEEP_BLUE_B,
        )
        self.btn_finish = ActionButton(
            "Finalizar",
            fill=BTN_DARK,
            text_color=BTN_LIGHT,
            hover_fill=BTN_DARK_H,
            border=BTN_DARK_B,
        )

        self.buttons = [
            self.btn_start,
            self.btn_pause,
            self.btn_reconfigure,
            self.btn_snapshot,
            self.btn_finish,
        ]

    def _refresh_layout(self):
        self.screen_w, self.screen_h = self.screen.get_size()

        sidebar_w = min(370, max(290, SIDEBAR_W))
        content_h = self.screen_h - OUTER_PAD * 2

        self.sidebar_rect = pygame.Rect(OUTER_PAD, OUTER_PAD, sidebar_w, content_h)

        right_x = self.sidebar_rect.right + OUTER_PAD
        right_w = max(280, self.screen_w - right_x - OUTER_PAD)
        self.sim_panel_rect = pygame.Rect(right_x, OUTER_PAD, right_w, content_h)

        self.summary_rect = pygame.Rect(
            self.sidebar_rect.x + INNER_PAD,
            self.sidebar_rect.y + 92,
            self.sidebar_rect.w - INNER_PAD * 2,
            86,
        )

        self.metadata_rect = pygame.Rect(
            self.summary_rect.x,
            self.summary_rect.bottom + 12,
            self.summary_rect.w,
            176,
        )

        btn_area_h = 5 * 45 + 4 * 10
        btn_base_y = self.sidebar_rect.bottom - INNER_PAD - btn_area_h
        btn_w = self.sidebar_rect.w - INNER_PAD * 2

        legend_top = self.metadata_rect.bottom + 12
        legend_bottom = btn_base_y - 12
        legend_h = max(0, legend_bottom - legend_top)
        self.legend_rect = pygame.Rect(
            self.summary_rect.x,
            legend_top,
            self.summary_rect.w,
            legend_h,
        )

        for idx, button in enumerate(self.buttons):
            y = btn_base_y + idx * (45 + 10)
            button.set_rect(pygame.Rect(self.sidebar_rect.x + INNER_PAD, y, btn_w, 45))

        panel_header_h = 70
        available_w = max(
            120,
            self.sim_panel_rect.w - INNER_PAD * 2 - SCROLL_SZ - 4,
        )
        available_h = max(
            120,
            self.sim_panel_rect.h - panel_header_h - INNER_PAD * 2 - SCROLL_SZ,
        )

        self.view_rect = pygame.Rect(
            self.sim_panel_rect.x + INNER_PAD,
            self.sim_panel_rect.y + panel_header_h,
            available_w,
            available_h,
        )

        self.hbar.rect = pygame.Rect(
            self.view_rect.x,
            self.view_rect.bottom + 4,
            self.view_rect.w,
            SCROLL_SZ,
        )
        self.vbar.rect = pygame.Rect(
            self.view_rect.right + 4,
            self.view_rect.y,
            SCROLL_SZ,
            self.view_rect.h,
        )

        self.hbar.set_lengths(self.world_w, self.view_rect.w)
        self.vbar.set_lengths(self.world_h, self.view_rect.h)

    def _rebuild_layout(self):
        procesos = self.linea.procesos
        max_tareas = max((len(p.tareas) for p in procesos), default=1)

        start_x = 76
        header_y = 82
        tasks_y = header_y + PROC_H + 40

        width_line = len(procesos) * PROC_W + max(0, len(procesos) - 1) * PROC_GAP
        finish_w = 260
        finish_h = 164
        world_w = start_x + width_line + PROC_GAP + finish_w + 110
        tasks_h = tasks_y + max_tareas * (TASK_H + TASK_GAP) + 110
        finish_h_total = tasks_y + finish_h + 110
        world_h = max(tasks_h, finish_h_total)

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
        self.finish_rect = pygame.Rect(fx, tasks_y, finish_w, finish_h)

        self.hbar.set_lengths(self.world_w, self.view_rect.w)
        self.vbar.set_lengths(self.world_h, self.view_rect.h)

    def _snap_sprites_to_locations(self):
        for pid, sprite in self.product_sprites.items():
            loc = self.product_locations.get(pid)
            target = self._location_to_point(pid, loc)
            sprite.pos = pygame.Vector2(target)
            sprite.start = sprite.pos.copy()
            sprite.target = sprite.pos.copy()
            sprite.elapsed_ms = sprite.duration_ms

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

    def _capture_locations(self) -> dict[int, tuple]:
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

    def _task_center(self, pi: int, ti: int) -> tuple[int, int]:
        rect = self.task_rects[(pi, ti)]
        return rect.right - 34, rect.centery

    def _queue_slot(self, pi: int, ti: int, qi: int) -> tuple[int, int]:
        rect = self.task_rects[(pi, ti)]
        x = max(24, rect.left - 20 - qi * (PROD_SZ + 8))
        y = rect.centery
        return x, y

    def _finish_slot(self, pid: int) -> tuple[int, int]:
        _ = pid
        return self.finish_rect.centerx, self.finish_rect.top + 84

    def _location_to_point(self, pid: int, loc: tuple | None) -> tuple[int, int]:
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

    def _status_counts(self) -> tuple[int, int, int, int]:
        total = len(self.linea.productos)
        por_procesar = sum(1 for p in self.linea.productos if p.estado == "en_espera")
        procesando = sum(1 for p in self.linea.productos if p.estado == "en_proceso")
        procesados = sum(1 for p in self.linea.productos if p.estado == "finalizado")
        return total, por_procesar, procesando, procesados

    def _advance_tick(self):
        old_locs = self.product_locations

        self.linea.reanudar()
        self.linea.tick()
        self.linea.pausar()

        new_locs = self._capture_locations()

        newly_finished = [
            pid
            for pid, loc in new_locs.items()
            if loc[0] == "final"
            and (pid not in old_locs or old_locs[pid][0] != "final")
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
            if self.finish_reason is None:
                self.finish_reason = "finished_auto"
            self.running = False

    def _start_play(self):
        if self.linea.todos_finalizados():
            return
        self.playing = True

    def _pause_play(self):
        if not self.playing:
            return
        self.playing = False
        self.linea.pausar()

    def _toggle_play(self):
        if self.playing:
            self._pause_play()
        else:
            self._start_play()

    def _show_toast(self, message: str, ms: int = 2400):
        self.toast_message = message
        self.toast_deadline_ms = pygame.time.get_ticks() + ms

    def _estimated_finish_cycles(self) -> int:
        total_tareas = sum(len(proceso.tareas) for proceso in self.linea.procesos)
        max_tp = max(
            (
                tarea.tiempo_proceso
                for proceso in self.linea.procesos
                for tarea in proceso.tareas
            ),
            default=1,
        )
        total_productos = max(1, len(self.linea.productos))

        # Cota superior conservadora para completar el lote al acelerar.
        return max(10000, total_tareas * max_tp * total_productos * 4)

    def _finish_to_end(self):
        if self.linea.todos_finalizados():
            self.finish_reason = "finished_button"
            self.running = False
            return

        self.playing = False
        self.accumulator_ms = 0.0

        self.linea.reanudar()
        budget = self._estimated_finish_cycles()
        self.linea.correr(max_ciclos=budget)

        if not self.linea.todos_finalizados():
            self.linea.correr(max_ciclos=budget * 4)

        self.linea.pausar()
        self.finish_reason = "finished_button"
        self.running = False

    def _take_snapshot(self):
        captures_dir = self.assets_dir / "capturas"
        captures_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = captures_dir / f"sim_{timestamp}.png"

        try:
            region = self.screen.subsurface(self.sim_panel_rect).copy()
            pygame.image.save(region, str(output))
            self._show_toast(f"Foto guardada: {output.name}")
        except Exception:
            self._show_toast("No se pudo guardar la foto")

    # -------------------------------- Eventos --------------------------------

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(
                    (event.w, event.h), pygame.RESIZABLE
                )
                self._set_window_icon()
                self._refresh_layout()
                self._rebuild_layout()
                self._snap_sprites_to_locations()
                continue

            if event.type == pygame.MOUSEMOTION:
                for button in self.buttons:
                    button.update_hover(event.pos)

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

            if self.btn_start.clicked(event):
                self._start_play()
            elif self.btn_pause.clicked(event):
                self._pause_play()
            elif self.btn_reconfigure.clicked(event):
                self.next_action = "reconfigure"
                self.running = False
            elif self.btn_snapshot.clicked(event):
                self._take_snapshot()
            elif self.btn_finish.clicked(event):
                self._finish_to_end()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self._toggle_play()
                elif event.key == pygame.K_p:
                    self._pause_play()
                elif event.key == pygame.K_s:
                    self._take_snapshot()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False

    # -------------------------------- Dibujo ---------------------------------

    def _draw_sidebar(self):
        _draw_rounded_rect(
            self.screen,
            self.sidebar_rect,
            SIDEBAR_BG,
            radius=20,
            border_color=PANEL_BORDER,
            border_width=1,
        )

        title = self.font_title.render("Simulacion", True, TEXT_DARK)
        self.screen.blit(
            title, (self.sidebar_rect.x + INNER_PAD, self.sidebar_rect.y + 24)
        )

        total, por_procesar, procesando, procesados = self._status_counts()

        _draw_rounded_rect(
            self.screen,
            self.summary_rect,
            CARD_BG,
            radius=12,
            border_color=PANEL_BORDER,
            border_width=1,
        )
        summary_main = self.font_h.render(f"{total} Productos", True, TEXT_DARK)
        summary_sub = self.font_sm.render("Lote cargado", True, TEXT_SOFT)
        self.screen.blit(
            summary_main, (self.summary_rect.x + 14, self.summary_rect.y + 16)
        )
        self.screen.blit(
            summary_sub, (self.summary_rect.x + 14, self.summary_rect.y + 52)
        )

        _draw_rounded_rect(
            self.screen,
            self.metadata_rect,
            CARD_SOFT,
            radius=12,
            border_color=PANEL_BORDER,
            border_width=1,
        )

        metadata_rows = [
            ("Tiempo", str(self.linea.tiempo_actual)),
            ("Productos por Procesar", str(por_procesar)),
            ("Procesando", str(procesando)),
            ("Procesados", str(procesados)),
        ]

        row_h = 40
        y = self.metadata_rect.y + 10
        for idx, (label, value) in enumerate(metadata_rows):
            if idx > 0:
                pygame.draw.line(
                    self.screen,
                    (219, 224, 234),
                    (self.metadata_rect.x + 12, y - 6),
                    (self.metadata_rect.right - 12, y - 6),
                    1,
                )
            lab_txt = self.font_sm.render(label, True, TEXT_MID)
            val_txt = self.font_b.render(value, True, ACCENT)
            self.screen.blit(lab_txt, (self.metadata_rect.x + 14, y + 4))
            self.screen.blit(
                val_txt,
                (self.metadata_rect.right - 16 - val_txt.get_width(), y + 2),
            )
            y += row_h

        if self.legend_rect.h >= 68:
            _draw_rounded_rect(
                self.screen,
                self.legend_rect,
                CARD_SOFT,
                radius=12,
                border_color=PANEL_BORDER,
                border_width=1,
            )

            icon_size = 20
            icon_proc = pygame.transform.smoothscale(
                self.asset_process_icon, (icon_size, icon_size)
            )
            icon_queue = pygame.transform.smoothscale(
                self.asset_queue_icon, (icon_size, icon_size)
            )

            row1_y = self.legend_rect.y + 12
            row2_y = row1_y + 30
            icon_x = self.legend_rect.x + 14
            text_x = icon_x + icon_size + 10

            self.screen.blit(icon_proc, (icon_x, row1_y))
            txt_proc = self.font_sm.render("Flecha verde: en proceso", True, TEXT_MID)
            self.screen.blit(txt_proc, (text_x, row1_y + 1))

            self.screen.blit(icon_queue, (icon_x, row2_y))
            txt_queue = self.font_sm.render("Flecha azul: en cola", True, TEXT_MID)
            self.screen.blit(txt_queue, (text_x, row2_y + 1))

        self.btn_start.enabled = (not self.playing) and (
            not self.linea.todos_finalizados()
        )
        self.btn_pause.enabled = self.playing
        self.btn_reconfigure.enabled = True
        self.btn_snapshot.enabled = True
        self.btn_finish.enabled = True

        for button in self.buttons:
            button.draw(self.screen, self.font)

        now_ms = pygame.time.get_ticks()
        if self.toast_message and now_ms < self.toast_deadline_ms:
            toast_rect = pygame.Rect(
                self.sidebar_rect.x + INNER_PAD,
                self.sidebar_rect.bottom - INNER_PAD - 34,
                self.sidebar_rect.w - INNER_PAD * 2,
                30,
            )
            _draw_rounded_rect(
                self.screen,
                toast_rect,
                (223, 233, 255),
                radius=8,
                border_color=(171, 189, 227),
                border_width=1,
            )
            toast_txt = self.font_sm.render(self.toast_message, True, (45, 70, 129))
            self.screen.blit(
                toast_txt,
                (
                    toast_rect.x + 10,
                    toast_rect.y + (toast_rect.h - toast_txt.get_height()) // 2,
                ),
            )

    def _draw_world(self):
        self.world.fill((0, 0, 0, 0))

        for i in range(len(self.process_rects) - 1):
            a = self.process_rects[i]
            b = self.process_rects[i + 1]
            y = a.centery
            pygame.draw.line(self.world, ACCENT, (a.right + 12, y), (b.left - 12, y), 3)
            pygame.draw.polygon(
                self.world,
                ACCENT,
                [(b.left - 12, y), (b.left - 22, y - 6), (b.left - 22, y + 6)],
            )

        for pi, proceso in enumerate(self.linea.procesos):
            pr = self.process_rects[pi]
            _draw_rounded_rect(
                self.world,
                pr,
                PROC_FILL,
                radius=12,
                border_color=PROC_FILL,
                border_width=1,
            )

            title = self.font_proc_name.render(proceso.nombre, True, PROC_TEXT)
            subt = self.font_proc_meta.render(
                f"Tareas: {len(proceso.tareas)}", True, PROC_META
            )

            self.world.blit(title, (pr.x + 14, pr.y + 16))
            self.world.blit(subt, (pr.x + 14, pr.y + 52))

            for ti, tarea in enumerate(proceso.tareas):
                tr = self.task_rects[(pi, ti)]
                active = tarea.esta_procesando
                fill = TASK_ACTIVE_FILL if active else TASK_IDLE_FILL
                border = TASK_ACTIVE_BORDER if active else TASK_IDLE_FILL
                text_main = TASK_ACTIVE_TEXT if active else TASK_IDLE_TEXT
                text_meta = TASK_ACTIVE_META if active else TASK_IDLE_META

                _draw_rounded_rect(
                    self.world,
                    tr,
                    fill,
                    radius=10,
                    border_color=border,
                    border_width=2,
                )

                t1 = self.font_task_name.render(tarea.nombre, True, text_main)
                t2 = self.font_task_meta.render(
                    f"TP={tarea.tiempo_proceso} EP={tarea.cantidad_en_espera()}",
                    True,
                    text_meta,
                )
                self.world.blit(t1, (tr.x + 14, tr.y + 14))
                self.world.blit(t2, (tr.x + 14, tr.y + 44))

        _draw_rounded_rect(
            self.world,
            self.finish_rect,
            (223, 232, 248),
            radius=12,
            border_color=(133, 154, 198),
            border_width=2,
        )
        fin_title = self.font_b.render("Procesados", True, ACCENT)
        self.world.blit(fin_title, (self.finish_rect.x + 16, self.finish_rect.y + 14))

        fin_total = sum(1 for p in self.linea.productos if p.estado == "finalizado")

        if fin_total == 0:
            slot_x, slot_y = self._finish_slot(0)
            placeholder_icon = self.asset_process_icon.copy()
            placeholder_icon.set_alpha(95)
            p_rect = placeholder_icon.get_rect(center=(slot_x, slot_y))
            self.world.blit(placeholder_icon, p_rect.topleft)

        fin_txt = self.font_sm.render(f"Terminados: {fin_total}", True, TEXT_DARK)
        fin_txt_rect = fin_txt.get_rect(
            center=(self.finish_rect.centerx, self.finish_rect.bottom - 26)
        )
        self.world.blit(fin_txt, fin_txt_rect.topleft)

        for sprite in self.product_sprites.values():
            if not sprite.visible:
                continue
            loc = self.product_locations.get(sprite.pid)
            kind = loc[0] if loc else ""
            icon = self.asset_queue_icon if kind == "queue" else self.asset_process_icon
            rect = icon.get_rect(center=(int(sprite.pos.x), int(sprite.pos.y)))
            self.world.blit(icon, rect.topleft)

    def _draw_simulation_panel(self):
        _draw_rounded_rect(
            self.screen,
            self.sim_panel_rect,
            PANEL_BG,
            radius=20,
            border_color=PANEL_BORDER,
            border_width=1,
        )

        title = self.font_h.render("Simulacion", True, TEXT_DARK)
        state = "En ejecucion" if self.playing else "Pausada"
        state_color = GOOD if self.playing else TEXT_MID
        subtitle = self.font_sm.render(f"Estado: {state}", True, state_color)

        self.screen.blit(
            title, (self.sim_panel_rect.x + INNER_PAD, self.sim_panel_rect.y + 20)
        )
        self.screen.blit(
            subtitle,
            (
                self.sim_panel_rect.x + INNER_PAD + title.get_width() + 14,
                self.sim_panel_rect.y + 30,
            ),
        )

        self.screen.blit(self._get_view_background(), self.view_rect.topleft)

        self._draw_world()

        src = pygame.Rect(
            int(self.hbar.offset),
            int(self.vbar.offset),
            self.view_rect.w,
            self.view_rect.h,
        )
        self.screen.blit(self.world, self.view_rect.topleft, src)

        _draw_rounded_rect(
            self.screen,
            self.view_rect,
            None,
            radius=8,
            border_color=(170, 182, 207),
            border_width=2,
        )

        self.hbar.draw(self.screen)
        self.vbar.draw(self.screen)

    def draw(self):
        self.screen.fill(PAGE_BG)
        self._draw_sidebar()
        self._draw_simulation_panel()
        pygame.display.flip()

    # --------------------------------- Loop ----------------------------------

    def run(self):
        while self.running:
            dt = self.clock.tick(60)
            self._handle_events()

            if not self.running:
                break

            if self.playing and not self.linea.todos_finalizados():
                self.accumulator_ms += dt
                while self.accumulator_ms >= self.cycle_ms and self.running:
                    self._advance_tick()
                    self.accumulator_ms -= self.cycle_ms
            else:
                self.accumulator_ms = min(self.accumulator_ms, self.cycle_ms)

            if not self.running:
                break

            for sprite in self.product_sprites.values():
                hidden_now = sprite.update(dt)
                if hidden_now:
                    self.hidden_finished_count += 1

            self.draw()

        if self.finish_reason in {"finished_button", "finished_auto"}:
            report = FinalReportWindow(self.linea, finish_reason=self.finish_reason)
            report.run()

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

        sim = SimulationWindow(
            linea,
            cantidad_productos=max(1, linea.cantidad_ingreso or 1),
        )
        action = sim.run()
        if action == "reconfigure":
            continue
        return linea


if __name__ == "__main__":
    main()
