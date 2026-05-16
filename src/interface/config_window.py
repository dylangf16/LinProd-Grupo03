"""
config_window.py  -  Interfaz visual de configuracion para la linea de produccion.

Flujo:
    ventana = ConfigWindow()
    linea = ventana.run()  # retorna LineaProduccion lista o None si se cancela
"""

from __future__ import annotations

import atexit
import json
import random
from pathlib import Path

import pygame
import pygame.gfxdraw

from src.logic.clase_linea_produccion import LineaProduccion
from src.logic.clase_proceso import Proceso
from src.logic.clase_tarea import Tarea


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def _boost(color: tuple[int, int, int], amount: int = 12) -> tuple[int, int, int]:
    return tuple(min(255, c + amount) for c in color)


def _draw_smooth_rounded_rect(
    surf: pygame.Surface,
    rect: pygame.Rect,
    color: tuple[int, int, int] | tuple[int, int, int, int],
    radius: int,
    border_color: tuple[int, int, int] | tuple[int, int, int, int] | None = None,
    border_width: int = 0,
):
    if rect.w <= 0 or rect.h <= 0:
        return

    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border_color is not None and border_width > 0:
        pygame.draw.rect(surf, border_color, rect, border_width, border_radius=radius)


def _draw_smooth_circle(
    surf: pygame.Surface,
    center: tuple[int, int],
    radius: int,
    color: tuple[int, int, int] | tuple[int, int, int, int],
    border_color: tuple[int, int, int] | tuple[int, int, int, int] | None = None,
    border_width: int = 0,
):
    if radius <= 0:
        return

    cx, cy = int(center[0]), int(center[1])
    r = int(radius)

    pygame.gfxdraw.filled_circle(surf, cx, cy, r, color)
    pygame.gfxdraw.aacircle(surf, cx, cy, r, color)

    if border_color is not None and border_width > 0:
        pygame.draw.circle(surf, border_color, (cx, cy), r, border_width)
        pygame.gfxdraw.aacircle(surf, cx, cy, r, border_color)


PAGE_BG = _hex_to_rgb("F5F5F7")
WHITE = (255, 255, 255)
TEXT_DARK = _hex_to_rgb("2C2C2C")
TEXT_MID = _hex_to_rgb("3B3B3B")
TEXT_SOFT = _hex_to_rgb("565656")
TEXT_HINT = _hex_to_rgb("979797")
INPUT_BORDER = _hex_to_rgb("D9D9D9")
INPUT_BG = _hex_to_rgb("F6F6F6")

BLUE_PRIMARY = _hex_to_rgb("11309F")
BLUE_ACTION = _hex_to_rgb("2952E1")
BLUE_PILL = _hex_to_rgb("1F3FAF")
BLUE_SOFT = _hex_to_rgb("D0DEF5")
BLUE_CARD = _hex_to_rgb("B7CDF2")
BLUE_GLOW = _hex_to_rgb("2F56DF")

CARD_BG = _hex_to_rgb("FAFBFF")
CARD_BORDER = _hex_to_rgb("E0E8F7")
CARD_BORDER_HOVER = _hex_to_rgb("BFD0F1")
CARD_IMAGE_BG = _hex_to_rgb("D9D9D9")

WIN_W = 1360
WIN_H = 820


class PillButton:
    def __init__(
        self,
        rect: tuple[int, int, int, int],
        label: str,
        fill: tuple[int, int, int],
        text_color: tuple[int, int, int],
        border: tuple[int, int, int] | None = None,
        radius: int = 999,
    ):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.fill = fill
        self.text_color = text_color
        self.border = border
        self.radius = radius
        self.hover = False

    def set_rect(self, rect: pygame.Rect):
        self.rect = pygame.Rect(rect)

    def update_hover(self, pos: tuple[int, int]):
        self.hover = self.rect.collidepoint(pos)

    def clicked(self, event: pygame.event.Event) -> bool:
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )

    def draw(self, surf: pygame.Surface, font: pygame.font.Font):
        color = _boost(self.fill, 10) if self.hover else self.fill
        _draw_smooth_rounded_rect(
            surf,
            self.rect,
            color,
            self.radius,
            border_color=self.border,
            border_width=1 if self.border is not None else 0,
        )
        txt = font.render(self.label, True, self.text_color)
        surf.blit(txt, txt.get_rect(center=self.rect.center))


class TextInput:
    def __init__(
        self,
        rect: tuple[int, int, int, int],
        placeholder: str = "",
        numeric: bool = False,
        max_len: int = 40,
    ):
        self.rect = pygame.Rect(rect)
        self.placeholder = placeholder
        self.numeric = numeric
        self.max_len = max_len
        self.text = ""
        self.active = False

        self._cursor_timer = 0
        self._cursor_visible = True

    def set_rect(self, rect: pygame.Rect):
        self.rect = pygame.Rect(rect)

    def update(self, dt_ms: int):
        self._cursor_timer += dt_ms
        if self._cursor_timer >= 520:
            self._cursor_visible = not self._cursor_visible
            self._cursor_timer = 0

    def handle(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return
            if event.key in (pygame.K_TAB, pygame.K_ESCAPE):
                self.active = False
                return
            if event.key == pygame.K_RETURN:
                return

            if len(self.text) >= self.max_len:
                return

            char = event.unicode
            if not char:
                return
            if self.numeric and not char.isdigit():
                return
            self.text += char

    def draw(self, surf: pygame.Surface, font: pygame.font.Font):
        border = BLUE_ACTION if self.active else INPUT_BORDER
        _draw_smooth_rounded_rect(
            surf,
            self.rect,
            INPUT_BG,
            9,
            border_color=border,
            border_width=1,
        )

        render_text = self.text if self.text else self.placeholder
        color = TEXT_MID if self.text else TEXT_HINT
        text_surf = font.render(render_text, True, color)
        text_pos = (
            self.rect.x + 18,
            self.rect.y + (self.rect.h - text_surf.get_height()) // 2,
        )
        surf.blit(text_surf, text_pos)

        if self.active and self._cursor_visible:
            cx = self.rect.x + 18 + font.size(self.text)[0]
            y1 = self.rect.y + 10
            y2 = self.rect.bottom - 10
            pygame.draw.line(surf, TEXT_MID, (cx, y1), (cx, y2), 2)


class CircleToggle:
    def __init__(self, x: int, y: int, label: str):
        self.circle = pygame.Rect(x, y, 28, 28)
        self.label = label
        self.checked = False

    def set_pos(self, x: int, y: int):
        self.circle.topleft = (x, y)

    def handle(self, event: pygame.event.Event) -> bool:
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.circle.collidepoint(event.pos)
        ):
            self.checked = not self.checked
            return True
        return False

    def draw(self, surf: pygame.Surface, font: pygame.font.Font):
        _draw_smooth_circle(
            surf, self.circle.center, 14, WHITE, border_color=TEXT_HINT, border_width=3
        )
        if self.checked:
            _draw_smooth_circle(surf, self.circle.center, 7, BLUE_ACTION)
        text = font.render(self.label, True, TEXT_MID)
        surf.blit(text, (self.circle.right + 14, self.circle.y + 1))


class HorizontalScrollBar:
    def __init__(self, rect: pygame.Rect):
        self.rect = pygame.Rect(rect)
        self.content_len = 1
        self.viewport_len = 1
        self.offset = 0.0

        self.dragging = False
        self.drag_mouse_origin = 0
        self.drag_offset_origin = 0.0

    @property
    def max_offset(self) -> float:
        return max(0.0, float(self.content_len - self.viewport_len))

    def set_rect(self, rect: pygame.Rect):
        self.rect = pygame.Rect(rect)

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
        track_len = self.rect.w
        ratio = (
            1.0
            if self.content_len <= self.viewport_len
            else self.viewport_len / self.content_len
        )

        thumb_len = max(34, int(track_len * ratio))
        travel = track_len - thumb_len

        if self.max_offset <= 0 or travel <= 0:
            thumb_pos = 0
        else:
            thumb_pos = int((self.offset / self.max_offset) * travel)

        return pygame.Rect(self.rect.x + thumb_pos, self.rect.y, thumb_len, self.rect.h)

    def handle(self, event: pygame.event.Event) -> bool:
        thumb = self._thumb_rect()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if thumb.collidepoint(event.pos):
                self.dragging = True
                self.drag_mouse_origin = event.pos[0]
                self.drag_offset_origin = self.offset
                return True
            if self.rect.collidepoint(event.pos):
                ratio = (event.pos[0] - self.rect.x) / max(1, self.rect.w)
                self.offset = max(0.0, min(self.max_offset, ratio * self.max_offset))
                return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            return True

        if event.type == pygame.MOUSEMOTION and self.dragging:
            delta = event.pos[0] - self.drag_mouse_origin
            travel = max(1, self.rect.w - thumb.w)
            if self.max_offset > 0:
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
        _draw_smooth_rounded_rect(surf, self.rect, _hex_to_rgb("D9E1F3"), 5)
        thumb = self._thumb_rect()
        _draw_smooth_rounded_rect(surf, thumb, _hex_to_rgb("9FB3E2"), 6)


class ConfigWindow:
    SETUP_DIR = Path(__file__).resolve().parent.parent / "prod_line_setup"
    CONFIG_FILE = SETUP_DIR / "configuracion_linea.json"
    CURRENT_FILE = SETUP_DIR / "current_lin_prod.json"

    TEAM_MEMBERS = [
        "Nahomi Cordero - 2021052766",
        "Melany Cordero - 2021527387",
        "Dylan Garbanzo - 2021057775",
        "Enrique Moraga - 2020195501",
        "Gabriela Salazar - 2020048408",
    ]

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H), pygame.RESIZABLE)
        pygame.display.set_caption("LinProd - Configuracion de Linea de Produccion")
        self.clock = pygame.time.Clock()

        self.assets_dir = Path(__file__).resolve().parent / "assets"
        self._set_window_icon()
        self.header_bg = self._load_image(
            "Pantalla Configuración/Header de Pantalla Configuración.png"
        )
        self.icons_raw: dict[str, pygame.Surface | None] = {
            "edit": self._load_image("Iconos/Icon editar.png"),
            "delete": self._load_image("Iconos/Icon eliminar.png"),
            "task": self._load_image("Iconos/Icon imagen.png"),
            "inicio": self._load_image("Iconos/Icon Inicio.png"),
            "intermedio": self._load_image("Iconos/Icon intermedio.png"),
            "final": self._load_image("Iconos/Icon final.png"),
        }
        self.icons_scaled: dict[tuple[str, int], pygame.Surface] = {}

        self._font_key: float | None = None
        self.ui_scale = 1.0
        self.font_title = pygame.font.SysFont("Segoe UI", 32, bold=True)
        self.font_subtitle = pygame.font.SysFont("Segoe UI", 20)
        self.font_h1 = pygame.font.SysFont("Segoe UI", 30, bold=True)
        self.font_h2 = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.font_body = pygame.font.SysFont("Segoe UI", 18)
        self.font_small = pygame.font.SysFont("Segoe UI", 15)
        self.font_tiny = pygame.font.SysFont("Segoe UI", 13)
        self._refresh_fonts()

        self.procesos_cfg: list[dict] = []
        self.cards_scroll = 0.0
        self.cards_scrollbar = HorizontalScrollBar(pygame.Rect(0, 0, 1, 1))
        self.card_hitboxes: list[dict] = []
        self.hover_card_index: int | None = None

        self.inp_cantidad = TextInput(
            (0, 0, 140, 48), placeholder="# productos", numeric=True, max_len=4
        )

        self.btn_add_proc = PillButton(
            (0, 0, 300, 52), "+ Añadir proceso", BLUE_PILL, WHITE
        )
        self.btn_start = PillButton(
            (0, 0, 300, 52), "Iniciar simulación", BLUE_PILL, WHITE
        )
        self.btn_save = PillButton(
            (0, 0, 130, 44), "Guardar JSON", BLUE_SOFT, BLUE_ACTION, border=BLUE_SOFT
        )
        self.btn_load = PillButton(
            (0, 0, 130, 44), "Cargar JSON", BLUE_SOFT, BLUE_ACTION, border=BLUE_SOFT
        )

        self.start_modal_open = False
        self.start_modal_error = ""
        self.start_modal_input = TextInput(
            (0, 0, 100, 56), placeholder="# de productos", numeric=True, max_len=4
        )
        self.btn_start_modal_cancel = PillButton(
            (0, 0, 180, 50), "Cancelar", BLUE_SOFT, BLUE_ACTION, border=BLUE_SOFT
        )
        self.btn_start_modal_confirm = PillButton(
            (0, 0, 180, 50), "Iniciar", BLUE_ACTION, WHITE
        )

        self.modal_open = False
        self.modal_edit_index: int | None = None
        self.modal_tasks: list[dict] = []
        self.modal_error = ""
        self.modal_task_scroll = 0.0
        self.modal_task_delete_hitboxes: list[tuple[int, pygame.Rect]] = []
        self.modal_task_item_hitboxes: list[tuple[int, pygame.Rect]] = []
        self.modal_task_move_left_hitboxes: list[tuple[int, pygame.Rect]] = []
        self.modal_task_move_right_hitboxes: list[tuple[int, pygame.Rect]] = []
        self.modal_task_edit_index: int | None = None
        self.modal_predecessor_name: str | None = None
        self.modal_predecessor_left_hitbox = pygame.Rect(0, 0, 0, 0)
        self.modal_predecessor_right_hitbox = pygame.Rect(0, 0, 0, 0)
        self.modal_predecessor_at_open: str | None = None
        self.modal_initial_at_open: bool = False
        self.modal_final_at_open: bool = False

        self.modal_proc_name = TextInput(
            (0, 0, 100, 56), placeholder="Placeholder text here...", max_len=40
        )
        self.modal_task_name = TextInput(
            (0, 0, 100, 56), placeholder="Placeholder text here...", max_len=40
        )
        self.modal_task_time = TextInput(
            (0, 0, 100, 56),
            placeholder="Placeholder text here...",
            numeric=True,
            max_len=5,
        )

        self.modal_chk_initial = CircleToggle(0, 0, "Proceso inicial")
        self.modal_chk_final = CircleToggle(0, 0, "Proceso final")

        self.btn_modal_add_task = PillButton(
            (0, 0, 208, 47), "Añadir tarea", BLUE_SOFT, BLUE_ACTION, border=BLUE_SOFT
        )
        self.btn_modal_apply = PillButton(
            (0, 0, 134, 47), "Aplicar", BLUE_ACTION, WHITE
        )

        self.linea_resultado: LineaProduccion | None = None

        self._bootstrap_config_files()

        print("[INFO] Sistema iniciado. Configura tu linea de produccion.")

    def _load_image(self, relative_path: str) -> pygame.Surface | None:
        full = self.assets_dir / relative_path
        if not full.exists():
            return None
        try:
            return pygame.image.load(str(full)).convert_alpha()
        except pygame.error:
            return None

    def _set_window_icon(self):
        icon = self._load_image("Iconos/Icon Logo.png")
        if icon is None:
            return
        pygame.display.set_icon(pygame.transform.smoothscale(icon, (32, 32)))

    def _get_icon(self, name: str, size: int) -> pygame.Surface | None:
        key = (name, size)
        cached = self.icons_scaled.get(key)
        if cached is not None:
            return cached

        base = self.icons_raw.get(name)
        if base is None:
            return None

        scaled = pygame.transform.smoothscale(base, (size, size))
        self.icons_scaled[key] = scaled
        return scaled

    def _refresh_fonts(self):
        w, h = self.screen.get_size()
        self.ui_scale = max(0.72, min(1.35, min(w / WIN_W, h / WIN_H)))
        key = round(self.ui_scale, 3)
        if self._font_key == key:
            return
        self._font_key = key

        def fs(base: int, min_size: int = 12) -> int:
            return max(min_size, int(base * self.ui_scale))

        self.font_title = pygame.font.SysFont("Segoe UI", fs(44, 26), bold=True)
        self.font_subtitle = pygame.font.SysFont("Segoe UI", fs(30, 20), bold=False)
        self.font_h1 = pygame.font.SysFont("Segoe UI", fs(23, 17), bold=True)
        self.font_h2 = pygame.font.SysFont("Segoe UI", fs(18, 14), bold=True)
        self.font_body = pygame.font.SysFont("Segoe UI", fs(15, 12), bold=False)
        self.font_small = pygame.font.SysFont("Segoe UI", fs(13, 10), bold=False)
        self.font_tiny = pygame.font.SysFont("Segoe UI", fs(11, 9), bold=False)

        self.icons_scaled.clear()

    def _layout(self) -> dict[str, pygame.Rect | tuple[int, int]]:
        w, h = self.screen.get_size()

        margin_x = max(28, int(w * 0.03))
        top_margin = max(10, int(h * 0.02))

        header_h = max(132, int(h * 0.27))
        header_rect = pygame.Rect(
            margin_x, top_margin, max(560, w - 2 * margin_x), header_h
        )

        content_top = header_rect.bottom + max(18, int(h * 0.02))

        btn_h = max(44, int(50 * self.ui_scale))
        bottom_pad = max(18, int(0.025 * h))
        btn_gap = max(12, int(16 * self.ui_scale))

        start_w = max(200, int(282 * self.ui_scale))
        add_w = max(220, int(282 * self.ui_scale))

        start_rect = pygame.Rect(
            w - margin_x - start_w, h - bottom_pad - btn_h, start_w, btn_h
        )
        add_rect = pygame.Rect(
            start_rect.x - btn_gap - add_w, start_rect.y, add_w, btn_h
        )

        save_rect = pygame.Rect(
            margin_x, start_rect.y, max(124, int(136 * self.ui_scale)), btn_h
        )
        load_rect = pygame.Rect(
            save_rect.right + 10,
            start_rect.y,
            max(124, int(136 * self.ui_scale)),
            btn_h,
        )

        cards_top = content_top + max(26, int(18 * self.ui_scale))
        cards_bottom = start_rect.y - max(22, int(24 * self.ui_scale))

        cards_view = pygame.Rect(
            margin_x,
            cards_top,
            max(640, w - 2 * margin_x),
            max(130, cards_bottom - cards_top),
        )
        cards_clip = pygame.Rect(
            cards_view.x, cards_view.y, cards_view.w, max(90, cards_view.h - 20)
        )
        scroll_rect = pygame.Rect(cards_view.x, cards_view.bottom - 8, cards_view.w, 8)

        modal_margin_x = max(20, int(w * 0.03))
        modal_margin_y = max(22, int(h * 0.035))
        modal_rect = pygame.Rect(
            modal_margin_x,
            modal_margin_y,
            max(760, w - 2 * modal_margin_x),
            max(520, h - 2 * modal_margin_y),
        )

        return {
            "header": header_rect,
            "count_pos": (margin_x, content_top),
            "cards_clip": cards_clip,
            "cards_scroll": scroll_rect,
            "add_btn": add_rect,
            "start_btn": start_rect,
            "save_btn": save_rect,
            "load_btn": load_rect,
            "modal": modal_rect,
        }

    def _start_modal_layout(self) -> dict[str, pygame.Rect | int]:
        w, h = self.screen.get_size()

        panel_w = min(700, max(430, int(w * 0.52)), w - 48)
        panel_h = min(320, max(250, int(h * 0.34)), h - 56)
        panel = pygame.Rect((w - panel_w) // 2, (h - panel_h) // 2, panel_w, panel_h)

        side_pad = max(24, int(30 * self.ui_scale))
        top_pad = max(18, int(22 * self.ui_scale))

        title_h = self.font_h1.get_height()
        subtitle_h = self.font_body.get_height()
        section_h = self.font_h2.get_height()
        input_h = max(42, int(50 * self.ui_scale))
        hint_h = self.font_small.get_height()

        gap_title = max(4, int(6 * self.ui_scale))
        gap_sub = max(8, int(10 * self.ui_scale))
        gap_input = max(10, int(12 * self.ui_scale))
        gap_hint = max(6, int(7 * self.ui_scale))

        btn_h = max(40, int(48 * self.ui_scale))
        btn_bottom_pad = max(20, int(24 * self.ui_scale))
        btn_y = panel.bottom - btn_bottom_pad - btn_h

        content_top = panel.y + top_pad
        content_bottom = btn_y - max(12, int(16 * self.ui_scale))
        available = max(0, content_bottom - content_top)
        required = title_h + subtitle_h + section_h + input_h + hint_h
        base_gaps = gap_title + gap_sub + gap_input + gap_hint

        extra = max(0, available - required - base_gaps)
        gap_sub += extra // 2
        gap_input += extra - (extra // 2)

        title_y = content_top
        subtitle_y = title_y + title_h + gap_title
        section_y = subtitle_y + subtitle_h + gap_sub
        input_top = section_y + section_h + gap_input
        hint_y = input_top + input_h + gap_hint

        input_rect = pygame.Rect(
            panel.x + side_pad,
            input_top,
            panel.w - side_pad * 2,
            input_h,
        )

        btn_gap = max(12, int(18 * self.ui_scale))
        btn_w = (panel.w - side_pad * 2 - btn_gap) // 2
        cancel_btn = pygame.Rect(panel.x + side_pad, btn_y, btn_w, btn_h)
        confirm_btn = pygame.Rect(cancel_btn.right + btn_gap, btn_y, btn_w, btn_h)

        return {
            "panel": panel,
            "input": input_rect,
            "cancel": cancel_btn,
            "confirm": confirm_btn,
            "title_y": title_y,
            "subtitle_y": subtitle_y,
            "section_y": section_y,
            "hint_y": hint_y,
        }

    def _modal_layout(
        self, panel: pygame.Rect
    ) -> dict[str, pygame.Rect | tuple[int, int]]:
        pad_x = max(34, int(66 * self.ui_scale))
        top = panel.y + max(26, int(46 * self.ui_scale))

        left_x = panel.x + pad_x
        left_w = int(panel.w * 0.43)

        right_x = left_x + left_w + max(24, int(40 * self.ui_scale))
        right_w = panel.right - right_x - max(30, int(44 * self.ui_scale))

        if right_w < 220:
            shrink = 220 - right_w
            left_w = max(320, left_w - shrink)
            right_x = left_x + left_w + max(20, int(26 * self.ui_scale))
            right_w = panel.right - right_x - max(24, int(34 * self.ui_scale))

        proc_input = pygame.Rect(
            left_x,
            top + max(48, int(58 * self.ui_scale)),
            left_w,
            max(44, int(56 * self.ui_scale)),
        )
        checks_y = proc_input.bottom + max(18, int(24 * self.ui_scale))

        pred_input = pygame.Rect(
            left_x,
            checks_y + max(46, int(56 * self.ui_scale)),
            left_w,
            max(42, int(50 * self.ui_scale)),
        )

        task_name = pygame.Rect(
            left_x,
            pred_input.bottom + max(42, int(50 * self.ui_scale)),
            left_w,
            max(44, int(56 * self.ui_scale)),
        )
        task_time = pygame.Rect(
            left_x,
            task_name.bottom + max(70, int(84 * self.ui_scale)),
            left_w,
            max(44, int(56 * self.ui_scale)),
        )

        add_task_btn = pygame.Rect(
            left_x + (left_w - max(180, int(208 * self.ui_scale))) // 2,
            task_time.bottom + max(52, int(66 * self.ui_scale)),
            max(180, int(208 * self.ui_scale)),
            max(40, int(47 * self.ui_scale)),
        )

        apply_btn = pygame.Rect(
            panel.right - max(138, int(172 * self.ui_scale)),
            panel.bottom - max(52, int(72 * self.ui_scale)),
            max(122, int(134 * self.ui_scale)),
            max(40, int(47 * self.ui_scale)),
        )

        tasks_title = (right_x, top + max(2, int(8 * self.ui_scale)))
        list_clip = pygame.Rect(
            right_x,
            top + max(46, int(66 * self.ui_scale)),
            right_w,
            max(120, panel.bottom - top - max(120, int(190 * self.ui_scale))),
        )

        return {
            "proc_input": proc_input,
            "checks_y": checks_y,
            "pred_input": pred_input,
            "task_name": task_name,
            "task_time": task_time,
            "add_task_btn": add_task_btn,
            "apply_btn": apply_btn,
            "tasks_title": tasks_title,
            "list_clip": list_clip,
        }

    def _trim_text(self, text: str, font: pygame.font.Font, max_width: int) -> str:
        if font.size(text)[0] <= max_width:
            return text
        while text and font.size(text + "...")[0] > max_width:
            text = text[:-1]
        return (text + "...") if text else ""

    def _process_type_label(self, proc_cfg: dict) -> str:
        ini = bool(proc_cfg.get("es_inicial"))
        fin = bool(proc_cfg.get("es_final"))
        if ini and fin:
            return "Proceso inicial / final"
        if ini:
            return "Proceso inicial"
        if fin:
            return "Proceso final"
        return "Proceso intermedio"

    def _process_icon_name(self, proc_cfg: dict) -> str:
        if proc_cfg.get("es_inicial"):
            return "inicio"
        if proc_cfg.get("es_final"):
            return "final"
        return "intermedio"

    def _sum_task_time(self, proc_cfg: dict) -> int:
        return sum(int(t.get("tiempo", 0)) for t in proc_cfg.get("tareas", []))

    def _normalize_unique_flags(self):
        seen_initial = False
        seen_final = False
        for proc in self.procesos_cfg:
            if proc.get("es_inicial"):
                if seen_initial:
                    proc["es_inicial"] = False
                else:
                    seen_initial = True

            if proc.get("es_final"):
                if seen_final:
                    proc["es_final"] = False
                else:
                    seen_final = True

    def _normalize_predecessor_refs(self):
        valid_names = {
            str(proc.get("nombre", "")).strip()
            for proc in self.procesos_cfg
            if str(proc.get("nombre", "")).strip()
        }

        for proc in self.procesos_cfg:
            proc.setdefault("predecesor", None)
            if proc.get("es_inicial"):
                proc["predecesor"] = None
                continue

            pred = proc.get("predecesor")
            pred_name = str(pred).strip() if pred is not None else ""
            own_name = str(proc.get("nombre", "")).strip()

            if not pred_name or pred_name == own_name or pred_name not in valid_names:
                proc["predecesor"] = None
                continue

            pred_cfg = next(
                (
                    p
                    for p in self.procesos_cfg
                    if str(p.get("nombre", "")).strip() == pred_name
                ),
                None,
            )
            if pred_cfg is not None and pred_cfg.get("es_final"):
                proc["predecesor"] = None
            else:
                proc["predecesor"] = pred_name

    def _ordered_cfg_for_build(self) -> list[dict]:
        initial = next((p for p in self.procesos_cfg if p.get("es_inicial")), None)
        final = next((p for p in self.procesos_cfg if p.get("es_final")), None)

        if initial is None or final is None:
            return list(self.procesos_cfg)

        ordered: list[dict] = [initial]
        for proc in self.procesos_cfg:
            if proc is initial or proc is final:
                continue
            ordered.append(proc)

        if final is not initial:
            ordered.append(final)

        return ordered

    def _visual_process_order_indices(self) -> list[int]:
        initial_idx = next(
            (i for i, p in enumerate(self.procesos_cfg) if p.get("es_inicial")),
            None,
        )
        final_idx = next(
            (i for i, p in enumerate(self.procesos_cfg) if p.get("es_final")),
            None,
        )

        ordered: list[int] = []
        if initial_idx is not None:
            ordered.append(initial_idx)

        for i in range(len(self.procesos_cfg)):
            if i == initial_idx or i == final_idx:
                continue
            ordered.append(i)

        if final_idx is not None and final_idx != initial_idx:
            ordered.append(final_idx)

        return ordered

    def _next_process_default_name(self) -> str:
        used_names = {str(p.get("nombre", "")).strip() for p in self.procesos_cfg}
        num = 1
        while f"Proceso_{num}" in used_names:
            num += 1
        return f"Proceso_{num}"

    def _modal_predecessor_candidates(self) -> list[str]:
        candidates: list[str] = []
        for idx, proc in enumerate(self.procesos_cfg):
            if self.modal_edit_index is not None and idx == self.modal_edit_index:
                continue
            if proc.get("es_final"):
                continue
            nombre = str(proc.get("nombre", "")).strip()
            if nombre:
                candidates.append(nombre)
        return candidates

    def _infer_predecessor_from_index(self, index: int) -> str | None:
        if not (0 <= index < len(self.procesos_cfg)):
            return None

        proceso = self.procesos_cfg[index]
        if proceso.get("es_inicial"):
            return None

        visual_indices = self._visual_process_order_indices()
        if index not in visual_indices:
            return None

        visual_pos = visual_indices.index(index)
        for prev_pos in range(visual_pos - 1, -1, -1):
            prev = self.procesos_cfg[visual_indices[prev_pos]]
            if prev.get("es_final"):
                continue
            nombre = str(prev.get("nombre", "")).strip()
            if nombre:
                return nombre

        return None

    def _default_modal_predecessor(
        self,
        stored_name: str | None = None,
        fallback_to_last: bool = True,
    ) -> str | None:
        candidates = self._modal_predecessor_candidates()
        if self.modal_chk_initial.checked or not candidates:
            return None
        if stored_name in candidates:
            return stored_name
        if not fallback_to_last:
            return None
        return candidates[-1]

    def _cycle_modal_predecessor(self, step: int):
        candidates = self._modal_predecessor_candidates()
        if self.modal_chk_initial.checked or not candidates:
            self.modal_predecessor_name = None
            return

        options: list[str | None] = [None] + candidates
        current = (
            self.modal_predecessor_name
            if self.modal_predecessor_name in options
            else None
        )
        idx = options.index(current)
        self.modal_predecessor_name = options[(idx + step) % len(options)]

    def _set_modal_predecessor_hitboxes(self, pred_rect: pygame.Rect):
        arrow_r = max(12, int(14 * self.ui_scale))
        gap = max(8, int(10 * self.ui_scale))

        right_rect = pygame.Rect(0, 0, arrow_r * 2, arrow_r * 2)
        left_rect = pygame.Rect(0, 0, arrow_r * 2, arrow_r * 2)

        right_rect.center = (
            pred_rect.right - max(24, int(30 * self.ui_scale)),
            pred_rect.centery,
        )
        left_rect.center = (
            right_rect.centerx - (arrow_r * 2 + gap),
            pred_rect.centery,
        )

        self.modal_predecessor_left_hitbox = left_rect
        self.modal_predecessor_right_hitbox = right_rect

    def _reposition_process_by_predecessor(self, process_index: int):
        if not (0 <= process_index < len(self.procesos_cfg)):
            return

        proc = self.procesos_cfg.pop(process_index)

        if proc.get("es_inicial"):
            proc["predecesor"] = None
            self.procesos_cfg.insert(0, proc)
            return

        if proc.get("es_final") and self.procesos_cfg:
            self.procesos_cfg.append(proc)
            return

        pred_raw = proc.get("predecesor")
        pred_name = pred_raw.strip() if isinstance(pred_raw, str) else ""
        if not pred_name:
            initial_idx = next(
                (i for i, p in enumerate(self.procesos_cfg) if p.get("es_inicial")),
                None,
            )
            insert_idx = initial_idx + 1 if initial_idx is not None else len(self.procesos_cfg)
            self.procesos_cfg.insert(insert_idx, proc)
            return

        pred_idx = next(
            (
                i
                for i, p in enumerate(self.procesos_cfg)
                if str(p.get("nombre", "")).strip() == pred_name
            ),
            None,
        )
        if pred_idx is None:
            proc["predecesor"] = None
            initial_idx = next(
                (i for i, p in enumerate(self.procesos_cfg) if p.get("es_inicial")),
                None,
            )
            insert_idx = initial_idx + 1 if initial_idx is not None else len(self.procesos_cfg)
            self.procesos_cfg.insert(insert_idx, proc)
            return

        self.procesos_cfg.insert(pred_idx + 1, proc)

    def _swap_modal_tasks(self, idx_a: int, idx_b: int):
        if not (0 <= idx_a < len(self.modal_tasks) and 0 <= idx_b < len(self.modal_tasks)):
            return

        self.modal_tasks[idx_a], self.modal_tasks[idx_b] = (
            self.modal_tasks[idx_b],
            self.modal_tasks[idx_a],
        )

        if self.modal_task_edit_index == idx_a:
            self.modal_task_edit_index = idx_b
        elif self.modal_task_edit_index == idx_b:
            self.modal_task_edit_index = idx_a

    def _next_task_default_name(self) -> str:
        used_names = {str(t.get("nombre", "")).strip() for t in self.modal_tasks}
        num = 1
        while f"Tarea_{num}" in used_names:
            num += 1
        return f"Tarea_{num}"

    def _seed_modal_task_defaults(self):
        self.modal_task_name.text = self._next_task_default_name()
        self.modal_task_time.text = str(random.randint(1, 15))

    @classmethod
    def _cleanup_current_file(cls):
        try:
            if cls.CURRENT_FILE.exists():
                cls.CURRENT_FILE.unlink()
                print(
                    f"[INFO] Archivo temporal eliminado: '{cls.CURRENT_FILE.as_posix()}'."
                )
        except Exception as exc:
            print(f"[WARN] No se pudo eliminar '{cls.CURRENT_FILE.as_posix()}': {exc}")

    def _set_task_add_mode(self, reseed: bool):
        self.modal_task_edit_index = None
        self.btn_modal_add_task.label = "Añadir tarea"
        if reseed:
            self._seed_modal_task_defaults()

    def _toggle_task_edit_mode(self, task_index: int):
        if not (0 <= task_index < len(self.modal_tasks)):
            return

        if self.modal_task_edit_index == task_index:
            self._set_task_add_mode(reseed=True)
            return

        task = self.modal_tasks[task_index]
        self.modal_task_edit_index = task_index
        self.btn_modal_add_task.label = "Editar tarea"
        self.modal_task_name.text = str(task.get("nombre", "")).strip()
        self.modal_task_time.text = str(int(task.get("tiempo", 1)))

    def _current_data_payload(self) -> dict:
        return {
            "procesos": self.procesos_cfg,
            "cantidad_ingreso": int(self.inp_cantidad.text or 0),
        }

    def _write_config_file(self, path: Path, data: dict, label: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[INFO] {label} guardada en '{path.as_posix()}'.")

    def _load_data_into_ui(self, data: dict):
        self.procesos_cfg = data.get("procesos", [])
        for proc in self.procesos_cfg:
            proc.setdefault("predecesor", None)
        self._normalize_unique_flags()
        self._normalize_predecessor_refs()
        cantidad = data.get("cantidad_ingreso", 0)
        self.inp_cantidad.text = str(cantidad) if cantidad else ""
        self.cards_scroll = 0.0
        self.cards_scrollbar.offset = 0.0

    def _read_config_file(self, path: Path, label: str) -> dict | None:
        if not path.exists():
            return None
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                print(f"[ERROR] {label} invalida: se esperaba un objeto JSON.")
                return None
            if "procesos" not in data:
                data["procesos"] = []
            if "cantidad_ingreso" not in data:
                data["cantidad_ingreso"] = 0
            return data
        except Exception as exc:
            print(f"[ERROR] No se pudo leer {label} '{path.as_posix()}': {exc}")
            return None

    def _bootstrap_config_files(self):
        self.SETUP_DIR.mkdir(parents=True, exist_ok=True)

        data = self._read_config_file(self.CURRENT_FILE, "configuracion actual")
        if data is not None:
            self._load_data_into_ui(data)
            return

        empty_data = {"procesos": [], "cantidad_ingreso": 0}
        self._load_data_into_ui(empty_data)
        self._write_config_file(self.CURRENT_FILE, empty_data, "Configuracion actual")

    def _guardar_json(self):
        data = self._current_data_payload()
        self._write_config_file(self.CONFIG_FILE, data, "Configuracion")
        self._write_config_file(self.CURRENT_FILE, data, "Configuracion actual")

    def _cargar_json(self):
        data = self._read_config_file(self.CONFIG_FILE, "configuracion guardada")
        if data is None:
            print(
                f"[ERROR] Archivo '{self.CONFIG_FILE.as_posix()}' no encontrado o invalido."
            )
            return

        self._load_data_into_ui(data)
        self._write_config_file(
            self.CURRENT_FILE, self._current_data_payload(), "Configuracion actual"
        )
        cantidad = data.get("cantidad_ingreso", 0)
        print(
            f"[INFO] Cargados {len(self.procesos_cfg)} proceso(s), cantidad={cantidad}."
        )

    def _construir_linea(self) -> LineaProduccion | None:
        if not self.procesos_cfg:
            print("[ERROR] No hay procesos definidos.")
            return None

        iniciales = [p for p in self.procesos_cfg if p.get("es_inicial")]
        finales = [p for p in self.procesos_cfg if p.get("es_final")]

        if len(iniciales) != 1:
            print(
                f"[ERROR] Se requiere exactamente 1 proceso inicial (hay {len(iniciales)})."
            )
            return None
        if len(finales) != 1:
            print(
                f"[ERROR] Se requiere exactamente 1 proceso final (hay {len(finales)})."
            )
            return None

        if len(self.procesos_cfg) > 1 and iniciales[0] is finales[0]:
            print(
                "[ERROR] Inicial y final deben ser procesos distintos si hay más de un proceso."
            )
            return None

        for pc in self.procesos_cfg:
            if not pc.get("tareas"):
                print(f"[ERROR] El proceso '{pc['nombre']}' no tiene tareas.")
                return None

        cant_s = self.inp_cantidad.text.strip()
        if not cant_s:
            cantidad = 1
        else:
            if int(cant_s) < 1:
                print("[ERROR] La cantidad de productos debe ser un entero >= 1.")
                return None
            cantidad = int(cant_s)

        linea = LineaProduccion("Linea Configurada")
        cfg_ordenada = self._ordered_cfg_for_build()
        for pc in cfg_ordenada:
            tareas = [Tarea(t["nombre"], int(t["tiempo"])) for t in pc["tareas"]]
            proceso = Proceso(
                pc["nombre"],
                tareas,
                es_inicial=bool(pc.get("es_inicial")),
                es_final=bool(pc.get("es_final")),
            )
            linea.agregar_proceso(proceso)

        linea.cantidad_ingreso = cantidad
        self._write_config_file(
            self.CURRENT_FILE, self._current_data_payload(), "Configuracion actual"
        )
        self.linea_resultado = linea
        return linea

    def _open_process_modal(self, index: int | None):
        self.modal_open = True
        self.modal_error = ""
        self.modal_task_scroll = 0.0
        self.modal_edit_index = index

        if index is None:
            default_initial = len(self.procesos_cfg) == 0
            proc_cfg = {
                "nombre": self._next_process_default_name(),
                "es_inicial": default_initial,
                "es_final": False,
                "predecesor": None,
                "tareas": [],
            }
        else:
            proc = self.procesos_cfg[index]
            pred_raw = proc.get("predecesor")
            pred = (
                pred_raw.strip()
                if isinstance(pred_raw, str) and pred_raw.strip()
                else None
            )
            if pred is None:
                pred = self._infer_predecessor_from_index(index)
            proc_cfg = {
                "nombre": str(proc.get("nombre", "")),
                "es_inicial": bool(proc.get("es_inicial")),
                "es_final": bool(proc.get("es_final")),
                "predecesor": pred,
                "tareas": [
                    {
                        "nombre": str(t.get("nombre", "")),
                        "tiempo": int(t.get("tiempo", 1)),
                    }
                    for t in proc.get("tareas", [])
                ],
            }

        self.modal_proc_name.text = proc_cfg["nombre"]
        self.modal_chk_initial.checked = bool(proc_cfg["es_inicial"])
        self.modal_chk_final.checked = bool(proc_cfg["es_final"])
        self.modal_predecessor_name = self._default_modal_predecessor(
            proc_cfg.get("predecesor"),
            fallback_to_last=index is None,
        )
        self.modal_predecessor_at_open = self.modal_predecessor_name
        self.modal_initial_at_open = self.modal_chk_initial.checked
        self.modal_final_at_open = self.modal_chk_final.checked
        self.modal_tasks = proc_cfg["tareas"]
        self._set_task_add_mode(reseed=True)

        self.modal_proc_name.active = False
        self.modal_task_name.active = False
        self.modal_task_time.active = False

    def _close_modal(self):
        self.modal_open = False
        self.modal_error = ""
        self._set_task_add_mode(reseed=False)
        self.modal_predecessor_name = None
        self.modal_predecessor_left_hitbox = pygame.Rect(0, 0, 0, 0)
        self.modal_predecessor_right_hitbox = pygame.Rect(0, 0, 0, 0)
        self.modal_proc_name.active = False
        self.modal_task_name.active = False
        self.modal_task_time.active = False

    def _open_start_modal(self):
        self.start_modal_open = True
        self.start_modal_error = ""
        self.start_modal_input.text = self.inp_cantidad.text.strip() or "1"
        self.start_modal_input.active = True

    def _close_start_modal(self):
        self.start_modal_open = False
        self.start_modal_error = ""
        self.start_modal_input.active = False

    def _confirm_start_modal(self):
        qty_text = self.start_modal_input.text.strip() or "1"
        try:
            cantidad = int(qty_text)
        except ValueError:
            self.start_modal_error = "La cantidad de productos debe ser un entero >= 1."
            return

        if cantidad < 1:
            self.start_modal_error = "La cantidad de productos debe ser un entero >= 1."
            return

        self.inp_cantidad.text = str(cantidad)
        result = self._construir_linea()
        if result is None:
            self.start_modal_error = (
                "No se pudo iniciar. Revisa la configuración de procesos."
            )
            return

        self._close_start_modal()
        pygame.event.post(pygame.event.Event(pygame.USEREVENT, {"action": "finish"}))

    def _modal_add_task(self):
        name = self.modal_task_name.text.strip()
        time_s = self.modal_task_time.text.strip()

        if not name:
            self.modal_error = "El nombre de la tarea no puede estar vacio."
            return
        if not time_s:
            self.modal_error = "El tiempo de tarea debe ser un entero >= 1."
            return

        tiempo = int(time_s)
        if tiempo < 1:
            self.modal_error = "El tiempo de tarea debe ser un entero >= 1."
            return

        task_data = {"nombre": name, "tiempo": tiempo}

        if self.modal_task_edit_index is not None:
            idx = self.modal_task_edit_index
            if 0 <= idx < len(self.modal_tasks):
                self.modal_tasks[idx] = task_data
            else:
                self.modal_tasks.append(task_data)
            self._set_task_add_mode(reseed=True)
            self.modal_error = ""
            return

        self.modal_tasks.append(task_data)
        self._set_task_add_mode(reseed=True)
        self.modal_error = ""

    def _modal_validate_flags(self, data: dict) -> bool:
        # Mantiene unicidad en pantalla: si se marca este proceso como
        # inicial/final, se desmarca en los demás automáticamente.
        for idx, proc in enumerate(self.procesos_cfg):
            if self.modal_edit_index is not None and idx == self.modal_edit_index:
                continue
            if data["es_inicial"]:
                proc["es_inicial"] = False
            if data["es_final"]:
                proc["es_final"] = False
        return True

    def _modal_apply(self):
        name = self.modal_proc_name.text.strip()
        if not name:
            self.modal_error = "El nombre del proceso no puede estar vacio."
            return
        for idx, proc in enumerate(self.procesos_cfg):
            if self.modal_edit_index is not None and idx == self.modal_edit_index:
                continue
            if str(proc.get("nombre", "")).strip().lower() == name.lower():
                self.modal_error = "El nombre del proceso debe ser unico."
                return
        if not self.modal_tasks:
            self.modal_error = "Agrega al menos una tarea para guardar el proceso."
            return

        predecessor_name = None
        if not self.modal_chk_initial.checked:
            predecessor_name = self.modal_predecessor_name

        data = {
            "nombre": name,
            "es_inicial": self.modal_chk_initial.checked,
            "es_final": self.modal_chk_final.checked,
            "predecesor": predecessor_name,
            "tareas": [
                {"nombre": t["nombre"], "tiempo": int(t["tiempo"])}
                for t in self.modal_tasks
            ],
        }

        if not self._modal_validate_flags(data):
            return

        old_name = None
        if self.modal_edit_index is None:
            self.procesos_cfg.append(data)
            target_index = len(self.procesos_cfg) - 1
            self.cards_scroll = 0.0
            self.cards_scrollbar.offset = 0.0
        else:
            old_name = str(self.procesos_cfg[self.modal_edit_index].get("nombre", "")).strip()
            self.procesos_cfg[self.modal_edit_index] = data
            target_index = self.modal_edit_index

        if old_name and old_name != name:
            for idx, proc in enumerate(self.procesos_cfg):
                if idx == target_index:
                    continue
                pred_raw = proc.get("predecesor")
                pred_name = pred_raw.strip() if isinstance(pred_raw, str) else ""
                if pred_name == old_name:
                    proc["predecesor"] = name

        self._normalize_predecessor_refs()

        # Solo reposicionar si el usuario realmente cambio algo que afecta
        # la posicion. Asi editar nombre o reordenar tareas no mueve el
        # proceso aunque el predecesor guardado este desactualizado por
        # swaps previos hechos desde los chevrons de las cards.
        should_reposition = (
            self.modal_edit_index is None
            or self.modal_predecessor_name != self.modal_predecessor_at_open
            or self.modal_chk_initial.checked != self.modal_initial_at_open
            or self.modal_chk_final.checked != self.modal_final_at_open
        )
        if should_reposition:
            self._reposition_process_by_predecessor(target_index)

        self._close_modal()

    def _delete_process(self, index: int):
        if 0 <= index < len(self.procesos_cfg):
            removed = self.procesos_cfg.pop(index)
            removed_name = str(removed.get("nombre", "")).strip()
            for proc in self.procesos_cfg:
                if str(proc.get("predecesor", "")).strip() == removed_name:
                    proc["predecesor"] = None
            self._normalize_predecessor_refs()

    def _swap_visual_neighbors(self, visual_idx_a: int, visual_idx_b: int):
        """Intercambia, en procesos_cfg, los procesos que ocupan dos posiciones
        visuales contiguas. Se usa para reordenar procesos intermedios desde
        la GUI sin tocar el proceso inicial ni el final, que siempre quedan en
        los extremos por _ordered_cfg_for_build/_visual_process_order_indices.
        """
        visual = self._visual_process_order_indices()
        if not (0 <= visual_idx_a < len(visual) and 0 <= visual_idx_b < len(visual)):
            return
        cfg_idx_a = visual[visual_idx_a]
        cfg_idx_b = visual[visual_idx_b]
        proc_a = self.procesos_cfg[cfg_idx_a]
        proc_b = self.procesos_cfg[cfg_idx_b]
        if proc_a.get("es_inicial") or proc_a.get("es_final"):
            return
        if proc_b.get("es_inicial") or proc_b.get("es_final"):
            return
        self.procesos_cfg[cfg_idx_a], self.procesos_cfg[cfg_idx_b] = (
            self.procesos_cfg[cfg_idx_b],
            self.procesos_cfg[cfg_idx_a],
        )

    def _draw_header(self, layout: dict):
        rect = layout["header"]
        if self.header_bg is not None:
            scaled = pygame.transform.smoothscale(self.header_bg, (rect.w, rect.h))
            self.screen.blit(scaled, rect.topleft)
        else:
            _draw_smooth_rounded_rect(self.screen, rect, _hex_to_rgb("D9E4F7"), 8)
        title = self.font_title.render("Simulación", True, BLUE_PRIMARY)
        subtitle = self.font_subtitle.render("Línea de Producción", True, BLUE_PRIMARY)

        middle_pad_x = max(36, int(rect.w * 0.08))
        middle_rect = pygame.Rect(
            rect.x + middle_pad_x,
            rect.y + max(16, int(rect.h * 0.21)),
            max(180, rect.w - middle_pad_x * 2),
            max(56, int(rect.h * 0.56)),
        )

        title_x = middle_rect.x + max(10, int(18 * self.ui_scale))
        title_gap = max(2, int(4 * self.ui_scale))
        title_block_h = title.get_height() + title_gap + subtitle.get_height()
        title_y = middle_rect.y + (middle_rect.h - title_block_h) // 2

        self.screen.blit(title, (title_x, title_y))
        self.screen.blit(subtitle, (title_x, title_y + title.get_height() + title_gap))

        member_surfaces = [
            self.font_tiny.render(name, True, TEXT_SOFT) for name in self.TEAM_MEMBERS
        ]
        line_gap = max(3, int(4 * self.ui_scale))
        block_h = sum(s.get_height() for s in member_surfaces) + line_gap * max(
            0, len(member_surfaces) - 1
        )
        block_w = max((s.get_width() for s in member_surfaces), default=0)

        right_pad = max(12, int(18 * self.ui_scale))
        members_x = middle_rect.right - right_pad - block_w
        members_y = middle_rect.y + max(0, (middle_rect.h - block_h) // 2) + 4

        current_y = members_y
        for txt in member_surfaces:
            self.screen.blit(txt, (members_x, current_y))
            current_y += txt.get_height() + line_gap

    def _draw_process_card(
        self,
        proc_idx: int,
        proc_cfg: dict,
        rect: pygame.Rect,
        visual_idx: int,
        can_move_left: bool,
        can_move_right: bool,
    ):
        hovered = proc_idx == self.hover_card_index
        border_col = CARD_BORDER_HOVER if hovered else CARD_BORDER

        _draw_smooth_rounded_rect(
            self.screen,
            rect,
            CARD_BG,
            10,
            border_color=border_col,
            border_width=2 if hovered else 1,
        )

        icon_box = pygame.Rect(
            rect.x + 18,
            rect.y + 20,
            max(52, int(72 * self.ui_scale)),
            max(52, int(72 * self.ui_scale)),
        )
        _draw_smooth_rounded_rect(self.screen, icon_box, CARD_IMAGE_BG, 10)

        picon = self._get_icon(
            self._process_icon_name(proc_cfg), max(24, int(34 * self.ui_scale))
        )
        if picon is not None:
            p_rect = picon.get_rect(center=icon_box.center)
            self.screen.blit(picon, p_rect)

        info_x = icon_box.right + max(12, int(16 * self.ui_scale))
        name_max = rect.right - info_x - 16
        name = self._trim_text(str(proc_cfg.get("nombre", "")), self.font_h2, name_max)
        t_name = self.font_h2.render(name, True, TEXT_MID)
        self.screen.blit(t_name, (info_x, rect.y + 34))

        type_label = self._process_type_label(proc_cfg)
        t_type = self.font_body.render(type_label, True, TEXT_SOFT)
        self.screen.blit(t_type, (info_x, rect.y + 34 + t_name.get_height() + 5))

        bullet_y = rect.y + max(136, int(168 * self.ui_scale))
        c_tareas = len(proc_cfg.get("tareas", []))
        sum_t = self._sum_task_time(proc_cfg)
        line1 = self.font_body.render(
            f"• Cantidad de Tareas: {c_tareas}", True, TEXT_MID
        )
        line2 = self.font_body.render(f"• Tiempo de ejecución: {sum_t}", True, TEXT_MID)
        self.screen.blit(line1, (rect.x + 24, bullet_y))
        self.screen.blit(line2, (rect.x + 24, bullet_y + line1.get_height() + 10))

        radius = max(20, int(30 * self.ui_scale))
        del_center = (
            rect.right - max(40, int(52 * self.ui_scale)),
            rect.bottom - max(34, int(48 * self.ui_scale)),
        )
        edit_center = (
            del_center[0] - (radius * 2 + max(10, int(12 * self.ui_scale))),
            del_center[1],
        )

        _draw_smooth_circle(self.screen, edit_center, radius, BLUE_CARD)
        _draw_smooth_circle(self.screen, del_center, radius, BLUE_CARD)

        e_icon = self._get_icon("edit", max(16, int(22 * self.ui_scale)))
        d_icon = self._get_icon("delete", max(16, int(22 * self.ui_scale)))
        if e_icon is not None:
            self.screen.blit(e_icon, e_icon.get_rect(center=edit_center))
        if d_icon is not None:
            self.screen.blit(d_icon, d_icon.get_rect(center=del_center))

        edit_rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        del_rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        edit_rect.center = edit_center
        del_rect.center = del_center

        # Botones de reordenar (chevron izq/der) en la esquina inferior-izquierda.
        # Solo aparecen para procesos intermedios que tienen un vecino tambien
        # intermedio con el que intercambiarse. El proceso inicial siempre queda
        # primero y el final siempre al ultimo en _ordered_cfg_for_build, asi
        # que no tiene sentido reordenarlos aqui.
        arrow_radius = max(14, int(20 * self.ui_scale))
        left_center = (
            rect.x + max(28, int(40 * self.ui_scale)) + arrow_radius,
            del_center[1],
        )
        right_center = (
            left_center[0] + arrow_radius * 2 + max(8, int(10 * self.ui_scale)),
            del_center[1],
        )

        left_rect = pygame.Rect(0, 0, arrow_radius * 2, arrow_radius * 2)
        right_rect = pygame.Rect(0, 0, arrow_radius * 2, arrow_radius * 2)
        left_rect.center = left_center
        right_rect.center = right_center

        if can_move_left:
            _draw_smooth_circle(self.screen, left_center, arrow_radius, BLUE_SOFT)
            self._draw_chevron(
                self.screen, left_center, arrow_radius, BLUE_ACTION, "left"
            )
        if can_move_right:
            _draw_smooth_circle(self.screen, right_center, arrow_radius, BLUE_SOFT)
            self._draw_chevron(
                self.screen, right_center, arrow_radius, BLUE_ACTION, "right"
            )

        self.card_hitboxes.append(
            {
                "index": proc_idx,
                "visual_idx": visual_idx,
                "rect": rect,
                "edit": edit_rect,
                "delete": del_rect,
                "move_left": left_rect if can_move_left else None,
                "move_right": right_rect if can_move_right else None,
            }
        )

    def _draw_chevron(
        self,
        surf: pygame.Surface,
        center: tuple[int, int],
        radius: int,
        color: tuple[int, int, int],
        direction: str,
    ):
        cx, cy = center
        size = max(5, radius // 2)
        if direction == "left":
            points = [
                (cx + size // 2, cy - size),
                (cx - size // 2 - 1, cy),
                (cx + size // 2, cy + size),
            ]
        else:
            points = [
                (cx - size // 2, cy - size),
                (cx + size // 2 + 1, cy),
                (cx - size // 2, cy + size),
            ]
        pygame.draw.polygon(surf, color, points)

    def _draw_processes(self, layout: dict):
        cards_clip: pygame.Rect = layout["cards_clip"]
        scroll_rect: pygame.Rect = layout["cards_scroll"]

        card_h = min(max(260, int(430 * self.ui_scale)), cards_clip.h - 8)
        card_w = max(260, int(card_h * 0.78))
        gap = max(14, int(24 * self.ui_scale))

        visual_indices = self._visual_process_order_indices()

        total = 0
        if visual_indices:
            total = len(visual_indices) * (card_w + gap) - gap

        self.cards_scrollbar.set_rect(scroll_rect)
        self.cards_scrollbar.set_lengths(max(1, total), max(1, cards_clip.w))
        self.cards_scrollbar.offset = max(
            0.0, min(self.cards_scrollbar.max_offset, self.cards_scroll)
        )
        self.cards_scroll = self.cards_scrollbar.offset

        self.card_hitboxes = []
        prev_clip = self.screen.get_clip()
        self.screen.set_clip(cards_clip)

        def _is_swappable(cfg: dict) -> bool:
            return not (cfg.get("es_inicial") or cfg.get("es_final"))

        for visual_idx, proc_idx in enumerate(visual_indices):
            proc_cfg = self.procesos_cfg[proc_idx]
            x_in_content = visual_idx * (card_w + gap)
            draw_x = cards_clip.x + int(x_in_content - self.cards_scroll)
            draw_rect = pygame.Rect(draw_x, cards_clip.y + 4, card_w, card_h)

            if (
                draw_rect.right < cards_clip.left - 10
                or draw_rect.left > cards_clip.right + 10
            ):
                continue

            can_left = False
            can_right = False
            if _is_swappable(proc_cfg):
                if visual_idx > 0:
                    prev_cfg = self.procesos_cfg[visual_indices[visual_idx - 1]]
                    can_left = _is_swappable(prev_cfg)
                if visual_idx + 1 < len(visual_indices):
                    next_cfg = self.procesos_cfg[visual_indices[visual_idx + 1]]
                    can_right = _is_swappable(next_cfg)

            self._draw_process_card(
                proc_idx,
                proc_cfg,
                draw_rect,
                visual_idx=visual_idx,
                can_move_left=can_left,
                can_move_right=can_right,
            )

        self.screen.set_clip(prev_clip)

        if self.cards_scrollbar.max_offset > 0:
            self.cards_scrollbar.draw(self.screen)

    def _draw_bottom_controls(self, layout: dict):
        self.btn_add_proc.set_rect(layout["add_btn"])
        self.btn_start.set_rect(layout["start_btn"])
        self.btn_save.set_rect(layout["save_btn"])
        self.btn_load.set_rect(layout["load_btn"])

        self.btn_save.draw(self.screen, self.font_small)
        self.btn_load.draw(self.screen, self.font_small)

        self.btn_add_proc.draw(self.screen, self.font_h2)
        self.btn_start.draw(self.screen, self.font_h2)

    def _draw_main(self, layout: dict):
        self.screen.fill(PAGE_BG)
        self._draw_header(layout)

        cp = layout["count_pos"]
        count_txt = self.font_h2.render(
            f"{len(self.procesos_cfg)} Procesos configurado", True, TEXT_DARK
        )
        self.screen.blit(count_txt, cp)

        self._draw_processes(layout)
        self._draw_bottom_controls(layout)

    def _draw_modal(self, panel: pygame.Rect, m: dict):
        if m is None:
            m = self._modal_layout(panel)

        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 72))
        self.screen.blit(overlay, (0, 0))

        glow_rect = panel.inflate(10, 10)
        glow = pygame.Surface((glow_rect.w, glow_rect.h), pygame.SRCALPHA)
        _draw_smooth_rounded_rect(glow, glow.get_rect(), (*BLUE_GLOW, 70), 26)
        self.screen.blit(glow, glow_rect.topleft)

        _draw_smooth_rounded_rect(self.screen, panel, WHITE, 24)

        self.modal_proc_name.set_rect(m["proc_input"])
        self.modal_task_name.set_rect(m["task_name"])
        self.modal_task_time.set_rect(m["task_time"])
        self._set_modal_predecessor_hitboxes(m["pred_input"])
        self.modal_chk_initial.set_pos(m["proc_input"].x, m["checks_y"])
        self.modal_chk_final.set_pos(
            m["proc_input"].x + m["proc_input"].w // 2 + 8, m["checks_y"]
        )
        self.btn_modal_add_task.set_rect(m["add_task_btn"])
        self.btn_modal_apply.set_rect(m["apply_btn"])

        title = self.font_h1.render("Nombre del Proceso", True, TEXT_DARK)
        self.screen.blit(
            title, (m["proc_input"].x, m["proc_input"].y - title.get_height() - 22)
        )

        self.modal_proc_name.draw(self.screen, self.font_body)
        self.modal_chk_initial.draw(self.screen, self.font_h2)
        self.modal_chk_final.draw(self.screen, self.font_h2)

        pred_lbl = self.font_h2.render("Proceso predecesor", True, TEXT_MID)
        pred_rect: pygame.Rect = m["pred_input"]
        self.screen.blit(
            pred_lbl,
            (pred_rect.x, pred_rect.y - pred_lbl.get_height() - 10),
        )

        _draw_smooth_rounded_rect(
            self.screen,
            pred_rect,
            INPUT_BG,
            9,
            border_color=INPUT_BORDER,
            border_width=1,
        )

        pred_candidates = self._modal_predecessor_candidates()
        can_cycle_pred = (not self.modal_chk_initial.checked) and bool(pred_candidates)
        pred_value = self.modal_predecessor_name or "Sin predecesor"
        if self.modal_chk_initial.checked:
            pred_value = "No aplica (proceso inicial)"

        pred_text = self._trim_text(
            pred_value,
            self.font_body,
            pred_rect.w - max(138, int(174 * self.ui_scale)),
        )
        pred_text_s = self.font_body.render(pred_text, True, TEXT_MID)
        self.screen.blit(
            pred_text_s,
            (
                pred_rect.x + 16,
                pred_rect.y + (pred_rect.h - pred_text_s.get_height()) // 2,
            ),
        )

        for direction, rect in (
            ("left", self.modal_predecessor_left_hitbox),
            ("right", self.modal_predecessor_right_hitbox),
        ):
            fill = BLUE_SOFT if can_cycle_pred else _hex_to_rgb("E3E6EF")
            chevron = BLUE_ACTION if can_cycle_pred else TEXT_HINT
            _draw_smooth_circle(self.screen, rect.center, rect.w // 2, fill)
            self._draw_chevron(self.screen, rect.center, rect.w // 2, chevron, direction)

        tname_lbl = self.font_h2.render("Nombre de la tarea", True, TEXT_MID)
        self.screen.blit(
            tname_lbl,
            (m["task_name"].x, m["task_name"].y - tname_lbl.get_height() - 12),
        )
        self.modal_task_name.draw(self.screen, self.font_body)

        ttime_lbl = self.font_h2.render("Tiempo de tarea", True, TEXT_MID)
        self.screen.blit(
            ttime_lbl,
            (m["task_time"].x, m["task_time"].y - ttime_lbl.get_height() - 12),
        )
        self.modal_task_time.draw(self.screen, self.font_body)
        ciclos = self.font_small.render("Ciclos", True, TEXT_HINT)
        self.screen.blit(ciclos, (m["task_time"].x, m["task_time"].bottom + 5))

        self.btn_modal_add_task.draw(self.screen, self.font_h2)
        self.btn_modal_apply.draw(self.screen, self.font_h2)

        list_title = self.font_h1.render("Lista de Tareas", True, TEXT_DARK)
        self.screen.blit(list_title, m["tasks_title"])

        list_clip: pygame.Rect = m["list_clip"]
        item_h = max(70, int(84 * self.ui_scale))
        item_gap = max(8, int(12 * self.ui_scale))

        content_h = 0
        if self.modal_tasks:
            content_h = len(self.modal_tasks) * (item_h + item_gap) - item_gap

        max_scroll = max(0.0, float(content_h - list_clip.h))
        self.modal_task_scroll = max(0.0, min(self.modal_task_scroll, max_scroll))

        self.modal_task_delete_hitboxes = []
        self.modal_task_item_hitboxes = []
        self.modal_task_move_left_hitboxes = []
        self.modal_task_move_right_hitboxes = []
        prev_clip = self.screen.get_clip()
        self.screen.set_clip(list_clip)

        for i, task in enumerate(self.modal_tasks):
            item_y = list_clip.y + i * (item_h + item_gap) - int(self.modal_task_scroll)
            item_rect = pygame.Rect(list_clip.x, item_y, list_clip.w, item_h)
            if (
                item_rect.bottom < list_clip.top - 2
                or item_rect.top > list_clip.bottom + 2
            ):
                continue

            selected = i == self.modal_task_edit_index
            _draw_smooth_rounded_rect(
                self.screen,
                item_rect,
                WHITE,
                12,
                border_color=BLUE_ACTION if selected else CARD_BORDER,
                border_width=2 if selected else 1,
            )

            ic_r = max(18, int(24 * self.ui_scale))
            ic_c = (item_rect.x + max(30, int(40 * self.ui_scale)), item_rect.centery)
            _draw_smooth_circle(self.screen, ic_c, ic_r, _hex_to_rgb("EEF2FA"))

            t_icon = self._get_icon("task", max(16, int(24 * self.ui_scale)))
            if t_icon is not None:
                self.screen.blit(t_icon, t_icon.get_rect(center=ic_c))

            tx = item_rect.x + max(64, int(84 * self.ui_scale))
            name_max = item_rect.w - max(260, int(300 * self.ui_scale))
            nm = self._trim_text(str(task["nombre"]), self.font_h2, name_max)

            nm_s = self.font_h2.render(nm, True, TEXT_MID)
            cy_s = self.font_body.render(f"#{task['tiempo']} ciclos", True, TEXT_SOFT)
            self.screen.blit(nm_s, (tx, item_rect.y + max(14, int(16 * self.ui_scale))))
            self.screen.blit(
                cy_s,
                (
                    tx,
                    item_rect.y + max(16, int(18 * self.ui_scale)) + nm_s.get_height(),
                ),
            )

            d_icon = self._get_icon("delete", max(16, int(22 * self.ui_scale)))
            d_rect = pygame.Rect(
                0, 0, max(26, int(30 * self.ui_scale)), max(26, int(30 * self.ui_scale))
            )
            d_rect.center = (
                item_rect.right - max(26, int(34 * self.ui_scale)),
                item_rect.centery,
            )

            move_radius = max(12, int(16 * self.ui_scale))
            move_right_rect = pygame.Rect(0, 0, move_radius * 2, move_radius * 2)
            move_left_rect = pygame.Rect(0, 0, move_radius * 2, move_radius * 2)
            move_right_rect.center = (
                d_rect.centerx - max(36, int(44 * self.ui_scale)),
                item_rect.centery,
            )
            move_left_rect.center = (
                move_right_rect.centerx - (move_radius * 2 + max(8, int(10 * self.ui_scale))),
                item_rect.centery,
            )

            can_move_left = i > 0
            can_move_right = i + 1 < len(self.modal_tasks)
            if can_move_left:
                _draw_smooth_circle(self.screen, move_left_rect.center, move_radius, BLUE_SOFT)
                self._draw_chevron(
                    self.screen,
                    move_left_rect.center,
                    move_radius,
                    BLUE_ACTION,
                    "left",
                )
                self.modal_task_move_left_hitboxes.append((i, move_left_rect.copy()))

            if can_move_right:
                _draw_smooth_circle(self.screen, move_right_rect.center, move_radius, BLUE_SOFT)
                self._draw_chevron(
                    self.screen,
                    move_right_rect.center,
                    move_radius,
                    BLUE_ACTION,
                    "right",
                )
                self.modal_task_move_right_hitboxes.append((i, move_right_rect.copy()))

            if d_icon is not None:
                self.screen.blit(d_icon, d_icon.get_rect(center=d_rect.center))

            self.modal_task_item_hitboxes.append((i, item_rect.copy()))
            self.modal_task_delete_hitboxes.append((i, d_rect))

        self.screen.set_clip(prev_clip)

        if max_scroll > 0:
            track_w = max(6, int(8 * self.ui_scale))
            track = pygame.Rect(
                list_clip.right - track_w, list_clip.y, track_w, list_clip.h
            )
            _draw_smooth_rounded_rect(self.screen, track, _hex_to_rgb("E7ECF9"), 4)
            thumb_h = max(26, int(list_clip.h * (list_clip.h / max(1.0, content_h))))
            travel = max(1, list_clip.h - thumb_h)
            thumb_y = int(track.y + (self.modal_task_scroll / max_scroll) * travel)
            thumb = pygame.Rect(track.x, thumb_y, track_w, thumb_h)
            _draw_smooth_rounded_rect(self.screen, thumb, _hex_to_rgb("A8BCE6"), 4)

        if not self.modal_tasks:
            empty = self.font_body.render(
                "Agrega tareas para este proceso.", True, TEXT_HINT
            )
            self.screen.blit(empty, (list_clip.x + 8, list_clip.y + 8))

        if self.modal_error:
            err = self.font_small.render(self.modal_error, True, _hex_to_rgb("B73232"))
            self.screen.blit(
                err,
                (m["proc_input"].x, panel.bottom - max(52, int(68 * self.ui_scale))),
            )

    def _draw_start_modal(self, sm: dict[str, pygame.Rect | int]):
        panel = sm["panel"]
        self.start_modal_input.set_rect(sm["input"])
        self.btn_start_modal_cancel.set_rect(sm["cancel"])
        self.btn_start_modal_confirm.set_rect(sm["confirm"])

        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))
        self.screen.blit(overlay, (0, 0))

        glow_rect = panel.inflate(10, 10)
        glow = pygame.Surface((glow_rect.w, glow_rect.h), pygame.SRCALPHA)
        _draw_smooth_rounded_rect(glow, glow.get_rect(), (*BLUE_GLOW, 62), 24)
        self.screen.blit(glow, glow_rect.topleft)

        _draw_smooth_rounded_rect(self.screen, panel, WHITE, 24)

        title = self.font_h1.render("Iniciar simulación", True, TEXT_DARK)
        subtitle = self.font_body.render("Línea de Producción", True, TEXT_HINT)
        section = self.font_h2.render("Parámetros de simulación", True, TEXT_DARK)

        top_x = self.start_modal_input.rect.x
        self.screen.blit(title, (top_x, int(sm["title_y"])))
        self.screen.blit(subtitle, (top_x, int(sm["subtitle_y"])))
        self.screen.blit(section, (top_x, int(sm["section_y"])))

        self.start_modal_input.draw(self.screen, self.font_body)
        hint = self.font_small.render(
            "Cantidad de productos a ingresar", True, TEXT_HINT
        )
        self.screen.blit(hint, (self.start_modal_input.rect.x, int(sm["hint_y"])))

        self.btn_start_modal_cancel.draw(self.screen, self.font_h2)
        self.btn_start_modal_confirm.draw(self.screen, self.font_h2)

        if self.start_modal_error:
            err = self.font_small.render(
                self.start_modal_error, True, _hex_to_rgb("B73232")
            )
            self.screen.blit(
                err, (top_x, self.btn_start_modal_cancel.rect.y - err.get_height() - 8)
            )

    def _handle_main_event(self, event: pygame.event.Event, layout: dict):
        if event.type == pygame.MOUSEMOTION:
            self.btn_add_proc.update_hover(event.pos)
            self.btn_start.update_hover(event.pos)
            self.btn_save.update_hover(event.pos)
            self.btn_load.update_hover(event.pos)

            self.hover_card_index = None
            for hb in self.card_hitboxes:
                if hb["rect"].collidepoint(event.pos):
                    self.hover_card_index = hb["index"]
                    break

        if self.cards_scrollbar.handle(event):
            self.cards_scroll = self.cards_scrollbar.offset
            return

        if event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            if layout["cards_clip"].collidepoint((mx, my)):
                self.cards_scrollbar.scroll_pixels(
                    -event.y * max(50, int(72 * self.ui_scale))
                )
                self.cards_scroll = self.cards_scrollbar.offset
                return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for hb in self.card_hitboxes:
                if hb["delete"].collidepoint(event.pos):
                    self._delete_process(hb["index"])
                    return
                if hb["edit"].collidepoint(event.pos):
                    self._open_process_modal(hb["index"])
                    return
                if hb.get("move_left") is not None and hb["move_left"].collidepoint(
                    event.pos
                ):
                    self._swap_visual_neighbors(hb["visual_idx"], hb["visual_idx"] - 1)
                    return
                if hb.get("move_right") is not None and hb["move_right"].collidepoint(
                    event.pos
                ):
                    self._swap_visual_neighbors(hb["visual_idx"], hb["visual_idx"] + 1)
                    return

        if self.btn_add_proc.clicked(event):
            self._open_process_modal(None)
            return
        if self.btn_start.clicked(event):
            self._open_start_modal()
            return
        if self.btn_save.clicked(event):
            self._guardar_json()
            return
        if self.btn_load.clicked(event):
            self._cargar_json()
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                info = pygame.display.Info()
                self.screen = pygame.display.set_mode(
                    (info.current_w, info.current_h), pygame.RESIZABLE
                )
                self._set_window_icon()
                return
            if event.key == pygame.K_s and (event.mod & pygame.KMOD_CTRL):
                self._guardar_json()
                return
            if event.key == pygame.K_l and (event.mod & pygame.KMOD_CTRL):
                self._cargar_json()
                return

    def _handle_start_modal_event(
        self, event: pygame.event.Event, sm: dict[str, pygame.Rect | int]
    ):
        self.start_modal_input.set_rect(sm["input"])
        self.btn_start_modal_cancel.set_rect(sm["cancel"])
        self.btn_start_modal_confirm.set_rect(sm["confirm"])

        if event.type == pygame.MOUSEMOTION:
            self.btn_start_modal_cancel.update_hover(event.pos)
            self.btn_start_modal_confirm.update_hover(event.pos)

        self.start_modal_input.handle(event)

        if self.btn_start_modal_cancel.clicked(event):
            self._close_start_modal()
            return
        if self.btn_start_modal_confirm.clicked(event):
            self._confirm_start_modal()
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._close_start_modal()
                return
            if event.key == pygame.K_RETURN:
                self._confirm_start_modal()
                return

    def _handle_modal_event(
        self, event: pygame.event.Event, panel: pygame.Rect, m: dict
    ):
        if m is None:
            m = self._modal_layout(panel)

        if event.type == pygame.MOUSEMOTION:
            self.btn_modal_add_task.update_hover(event.pos)
            self.btn_modal_apply.update_hover(event.pos)

        self.modal_proc_name.handle(event)
        self.modal_task_name.handle(event)
        self.modal_task_time.handle(event)

        if self.modal_chk_initial.handle(event):
            if self.modal_chk_initial.checked:
                self.modal_predecessor_name = None
            else:
                self.modal_predecessor_name = self._default_modal_predecessor(
                    self.modal_predecessor_name
                )
            self.modal_error = ""
            return
        if self.modal_chk_final.handle(event):
            self.modal_error = ""
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._set_modal_predecessor_hitboxes(m["pred_input"])

            if self.modal_predecessor_left_hitbox.collidepoint(event.pos):
                self._cycle_modal_predecessor(-1)
                self.modal_error = ""
                return

            if self.modal_predecessor_right_hitbox.collidepoint(event.pos):
                self._cycle_modal_predecessor(1)
                self.modal_error = ""
                return

            for idx, drect in self.modal_task_delete_hitboxes:
                if drect.collidepoint(event.pos):
                    self.modal_tasks.pop(idx)
                    if self.modal_task_edit_index is not None:
                        if self.modal_task_edit_index == idx:
                            self._set_task_add_mode(reseed=True)
                        elif self.modal_task_edit_index > idx:
                            self.modal_task_edit_index -= 1
                    self.modal_error = ""
                    return

            for idx, lrect in self.modal_task_move_left_hitboxes:
                if lrect.collidepoint(event.pos):
                    self._swap_modal_tasks(idx, idx - 1)
                    self.modal_error = ""
                    return

            for idx, rrect in self.modal_task_move_right_hitboxes:
                if rrect.collidepoint(event.pos):
                    self._swap_modal_tasks(idx, idx + 1)
                    self.modal_error = ""
                    return

            for idx, irect in self.modal_task_item_hitboxes:
                if irect.collidepoint(event.pos):
                    self._toggle_task_edit_mode(idx)
                    self.modal_error = ""
                    return

            if not panel.collidepoint(event.pos):
                return

        if self.btn_modal_add_task.clicked(event):
            self._modal_add_task()
            return
        if self.btn_modal_apply.clicked(event):
            self._modal_apply()
            return

        if event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            clip_rect: pygame.Rect = m["list_clip"]
            if clip_rect.collidepoint((mx, my)):
                item_h = max(70, int(84 * self.ui_scale))
                item_gap = max(8, int(12 * self.ui_scale))
                content_h = (
                    len(self.modal_tasks) * (item_h + item_gap) - item_gap
                    if self.modal_tasks
                    else 0
                )
                max_scroll = max(0.0, float(content_h - clip_rect.h))
                self.modal_task_scroll = max(
                    0.0, min(max_scroll, self.modal_task_scroll - event.y * 40.0)
                )
                return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._close_modal()
                return
            if event.key == pygame.K_RETURN and (
                self.modal_task_name.active or self.modal_task_time.active
            ):
                self._modal_add_task()
                return

    def run(self) -> LineaProduccion | None:
        running = True

        while running:
            dt = self.clock.tick(60)
            self._refresh_fonts()

            layout = self._layout()
            modal_layout = (
                self._modal_layout(layout["modal"]) if self.modal_open else None
            )
            start_modal_layout = (
                self._start_modal_layout() if self.start_modal_open else None
            )

            if self.modal_open:
                self.modal_proc_name.update(dt)
                self.modal_task_name.update(dt)
                self.modal_task_time.update(dt)
            if self.start_modal_open:
                self.start_modal_input.update(dt)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

                if event.type == pygame.VIDEORESIZE:
                    nw = max(940, event.w)
                    nh = max(620, event.h)
                    self.screen = pygame.display.set_mode((nw, nh), pygame.RESIZABLE)
                    self._set_window_icon()
                    self._refresh_fonts()
                    continue

                if (
                    event.type == pygame.USEREVENT
                    and event.dict.get("action") == "finish"
                ):
                    running = False
                    continue

                if self.modal_open:
                    if modal_layout is None:
                        modal_layout = self._modal_layout(layout["modal"])
                    self._handle_modal_event(event, layout["modal"], modal_layout)
                elif self.start_modal_open:
                    if start_modal_layout is None:
                        start_modal_layout = self._start_modal_layout()
                    self._handle_start_modal_event(event, start_modal_layout)
                else:
                    self._handle_main_event(event, layout)

            self._draw_main(layout)
            if self.modal_open:
                if modal_layout is None:
                    modal_layout = self._modal_layout(layout["modal"])
                self._draw_modal(layout["modal"], modal_layout)
            elif self.start_modal_open:
                if start_modal_layout is None:
                    start_modal_layout = self._start_modal_layout()
                self._draw_start_modal(start_modal_layout)

            pygame.display.flip()

        pygame.quit()
        return self.linea_resultado


atexit.register(ConfigWindow._cleanup_current_file)


def main():
    ventana = ConfigWindow()
    linea = ventana.run()
    print()
    if linea is not None:
        print("=" * 58)
        print("LINEA LISTA para el modulo de simulacion.")
        print("=" * 58)
        linea.imprimir_estado()
    else:
        print("Configuracion cancelada.")
    return linea


if __name__ == "__main__":
    main()
