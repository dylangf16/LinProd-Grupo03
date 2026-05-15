"""
final_report.py  -  Ventana emergente de reporte final para la simulacion.

Muestra, como minimo, las metricas solicitadas en el enunciado del proyecto.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pygame

# Soporte de ejecucion directa y desde el resto del proyecto.
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src" / "logic") not in sys.path:
    sys.path.insert(0, str(ROOT / "src" / "logic"))

from src.logic.clase_estadistica import Estadisticas
from src.logic.clase_linea_produccion import LineaProduccion


WIN_W = 980
WIN_H = 640

PAGE_BG = (210, 210, 210)
PANEL_BG = (245, 246, 250)
PANEL_BORDER = (204, 210, 223)

CARD_BG = (236, 241, 251)
CARD_BORDER = (211, 220, 239)
PROC_CARD_BG = (238, 242, 249)

TEXT_DARK = (38, 42, 52)
TEXT_MID = (77, 84, 98)
TEXT_SOFT = (118, 126, 141)
ACCENT = (41, 82, 225)
GOOD = (57, 140, 84)
WARN = (170, 110, 28)

BTN_FILL = (208, 222, 245)
BTN_FILL_H = (195, 212, 241)
BTN_TEXT = (41, 82, 225)
BTN_BORDER = (166, 188, 230)


def _draw_rounded_rect(
    surf: pygame.Surface,
    rect: pygame.Rect,
    color: tuple[int, int, int] | None,
    radius: int,
    border_color: tuple[int, int, int] | None = None,
    border_width: int = 0,
):
    if rect.w <= 0 or rect.h <= 0:
        return
    if color is not None:
        pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border_color is not None and border_width > 0:
        pygame.draw.rect(surf, border_color, rect, border_width, border_radius=radius)


class ReportButton:
    def __init__(self, label: str):
        self.label = label
        self.rect = pygame.Rect(0, 0, 1, 1)
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
        fill = BTN_FILL_H if self.hover else BTN_FILL
        _draw_rounded_rect(
            surf,
            self.rect,
            fill,
            radius=10,
            border_color=BTN_BORDER,
            border_width=1,
        )
        txt = font.render(self.label, True, BTN_TEXT)
        surf.blit(txt, txt.get_rect(center=self.rect.center))


class FinalReportWindow:
    def __init__(self, linea: LineaProduccion, finish_reason: str = "manual"):
        if not pygame.get_init():
            pygame.init()

        self.linea = linea
        self.finish_reason = finish_reason
        self.stats = Estadisticas(linea)

        self.screen = pygame.display.set_mode((WIN_W, WIN_H), pygame.RESIZABLE)
        pygame.display.set_caption("LinProd - Reporte Final")
        self.clock = pygame.time.Clock()

        self.font_title = pygame.font.SysFont("Segoe UI", 44, bold=True)
        self.font_h = pygame.font.SysFont("Segoe UI", 30, bold=True)
        self.font = pygame.font.SysFont("Segoe UI", 18)
        self.font_b = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.font_sm = pygame.font.SysFont("Segoe UI", 14)

        self.running = True
        self.btn_close = ReportButton("Cerrar reporte")

    # ------------------------------- Datos ---------------------------------

    @staticmethod
    def _fmt_t(value: int | None) -> str:
        if value is None:
            return "No disponible"
        return f"T{int(value)}"

    @staticmethod
    def _fmt_cycles(value: float | int) -> str:
        return f"{float(value):.2f} ciclos"

    def _report_rows(self) -> list[tuple[str, str]]:
        return [
            ("Primer producto finalizo en", self._fmt_t(self.stats.tiempo_primer_producto())),
            ("Ultimo producto finalizo en", self._fmt_t(self.stats.tiempo_ultimo_producto())),
            (
                "Tiempo promedio de finalizacion",
                self._fmt_cycles(self.stats.tiempo_promedio_finalizacion()),
            ),
            (
                "Proceso con mayor congestionamiento",
                self.stats.proceso_mayor_congestion(),
            ),
            (
                "Tiempo promedio para iniciar tarea",
                self._fmt_cycles(self.stats.promedio_espera_tareas()),
            ),
            (
                "Proceso y tarea con mayor espera",
                self.stats.proceso_y_tarea_mayor_espera(),
            ),
            (
                "Tiempo total de procesamiento",
                self._fmt_cycles(self.stats.tiempo_total_procesamiento()),
            ),
        ]

    def _extra_stat(self) -> tuple[str, str]:
        """Estadistica adicional propuesta por el grupo."""
        pct = self.stats.utilizacion_promedio_tareas() * 100
        return (
            "Utilizacion promedio de tareas",
            f"{pct:.1f}%",
        )

    # ------------------------------- Dibujo --------------------------------

    def _draw_metric_cards(
        self,
        panel: pygame.Rect,
        left_rect: pygame.Rect,
        close_button_rect: pygame.Rect,
    ):
        rows = self._report_rows()

        title = self.font_h.render("Tiempo total", True, ACCENT)
        total_txt = self.font.render(
            f"{self.stats.tiempo_total_simulacion()} ciclos", True, TEXT_MID
        )
        self.screen.blit(title, (left_rect.x, left_rect.y))
        self.screen.blit(total_txt, (left_rect.x, left_rect.y + title.get_height() + 2))

        grid_top = left_rect.y + 68
        col_gap = 10
        row_gap = 8
        col_w = (left_rect.w - col_gap) // 2

        card_h = 66
        rows_count = (len(rows) + 1) // 2
        for idx, (label, value) in enumerate(rows):
            col = idx % 2
            row = idx // 2
            card = pygame.Rect(
                left_rect.x + col * (col_w + col_gap),
                grid_top + row * (card_h + row_gap),
                col_w,
                card_h,
            )
            _draw_rounded_rect(
                self.screen,
                card,
                CARD_BG,
                radius=10,
                border_color=CARD_BORDER,
                border_width=1,
            )
            lbl = self.font_sm.render(label, True, TEXT_SOFT)
            val = self.font_b.render(value, True, TEXT_DARK)
            self.screen.blit(lbl, (card.x + 10, card.y + 8))
            self.screen.blit(val, (card.x + 10, card.y + 30))

        # Estadistica adicional propuesta por el grupo: ocupa todo el ancho y
        # se destaca con la paleta acento para diferenciarla de las metricas
        # solicitadas por el enunciado.
        extra_label, extra_value = self._extra_stat()
        extra_top = grid_top + rows_count * (card_h + row_gap)
        extra_card = pygame.Rect(left_rect.x, extra_top, left_rect.w, card_h)
        _draw_rounded_rect(
            self.screen,
            extra_card,
            BTN_FILL,
            radius=10,
            border_color=BTN_BORDER,
            border_width=1,
        )
        badge = self.font_sm.render("Estadistica del grupo", True, BTN_TEXT)
        self.screen.blit(badge, (extra_card.x + 10, extra_card.y + 8))
        extra_lbl = self.font_sm.render(extra_label, True, TEXT_SOFT)
        extra_val = self.font_b.render(extra_value, True, ACCENT)
        self.screen.blit(
            extra_lbl,
            (extra_card.x + 10 + badge.get_width() + 10, extra_card.y + 8),
        )
        self.screen.blit(extra_val, (extra_card.x + 10, extra_card.y + 30))

        status_msg = "Fin por boton Finalizar"
        status_color = WARN
        if self.finish_reason == "finished_auto":
            status_msg = "Todos los productos finalizaron"
            status_color = GOOD

        status = self.font.render(status_msg, True, status_color)
        self.screen.blit(status, (left_rect.x, close_button_rect.y - 50))

        product_txt = self.font.render(
            f"Productos procesados: {self.stats.cantidad_productos_procesados()}"
            f" / {len(self.linea.productos)}",
            True,
            TEXT_MID,
        )
        self.screen.blit(product_txt, (left_rect.x, close_button_rect.y - 24))

    def _draw_process_stats(self, right_rect: pygame.Rect):
        title = self.font_h.render("Estadisticas", True, TEXT_DARK)
        product_count = self.font.render(
            f"Cantidad de productos: {len(self.linea.productos)}", True, ACCENT
        )
        sim_time = self.font.render(
            f"Tiempo total de simulacion: {self.stats.tiempo_total_simulacion()} ciclos",
            True,
            TEXT_MID,
        )

        self.screen.blit(title, (right_rect.x, right_rect.y))
        self.screen.blit(product_count, (right_rect.x, right_rect.y + title.get_height() + 2))
        self.screen.blit(sim_time, (right_rect.x, right_rect.y + title.get_height() + 28))

        cards_top = right_rect.y + 98
        card_h = 78
        gap = 10
        available_h = right_rect.bottom - cards_top
        max_cards = max(1, available_h // (card_h + gap))

        per_process = sorted(
            self.stats.estadisticas_por_proceso(),
            key=lambda proc: proc["espera_total"],
            reverse=True,
        )
        visible = per_process[:max_cards]

        for idx, proc in enumerate(visible):
            rect = pygame.Rect(
                right_rect.x,
                cards_top + idx * (card_h + gap),
                right_rect.w,
                card_h,
            )
            _draw_rounded_rect(
                self.screen,
                rect,
                PROC_CARD_BG,
                radius=12,
                border_color=CARD_BORDER,
                border_width=1,
            )

            name = self.font_b.render(str(proc["proceso"]), True, TEXT_DARK)
            tcount = self.font.render(f"Tareas: {proc['num_tareas']}", True, TEXT_MID)
            wait = self.font.render(f"Espera: {proc['espera_total']} ciclos", True, TEXT_MID)

            self.screen.blit(name, (rect.x + 14, rect.y + 12))
            self.screen.blit(tcount, (rect.x + 14, rect.y + 40))
            self.screen.blit(wait, (rect.x + 130, rect.y + 40))

        missing = len(per_process) - len(visible)
        if missing > 0:
            more = self.font_sm.render(f"+{missing} procesos adicionales", True, TEXT_SOFT)
            self.screen.blit(more, (right_rect.x + 4, right_rect.bottom - 18))

    def _draw(self):
        self.screen.fill(PAGE_BG)
        w, h = self.screen.get_size()

        panel_w = min(1160, max(780, w - 72))
        panel_h = min(760, max(520, h - 56))
        panel = pygame.Rect((w - panel_w) // 2, (h - panel_h) // 2, panel_w, panel_h)

        _draw_rounded_rect(
            self.screen,
            panel,
            PANEL_BG,
            radius=24,
            border_color=PANEL_BORDER,
            border_width=1,
        )

        title = self.font_title.render("Reporte General", True, TEXT_DARK)
        self.screen.blit(title, (panel.x + 30, panel.y + 26))

        cols_top = panel.y + 98
        cols_bottom = panel.bottom - 130
        cols_h = max(220, cols_bottom - cols_top)
        cols_gap = 34

        left_w = int((panel.w - cols_gap - 60) * 0.55)
        right_w = panel.w - left_w - cols_gap - 60

        left_rect = pygame.Rect(panel.x + 30, cols_top, left_w, cols_h)
        right_rect = pygame.Rect(left_rect.right + cols_gap, cols_top, right_w, cols_h)

        close_button_rect = pygame.Rect(panel.x + 30, panel.bottom - 72, 188, 40)

        self._draw_metric_cards(panel, left_rect, close_button_rect)
        self._draw_process_stats(right_rect)

        self.btn_close.set_rect(close_button_rect)
        self.btn_close.draw(self.screen, self.font_b)

        hint = self.font_sm.render("ESC o Enter para cerrar", True, TEXT_SOFT)
        self.screen.blit(hint, (panel.right - 172, panel.bottom - 56))

        pygame.display.flip()

    # -------------------------------- Loop ---------------------------------

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(
                    (event.w, event.h), pygame.RESIZABLE
                )
                continue

            if event.type == pygame.MOUSEMOTION:
                self.btn_close.update_hover(event.pos)

            if self.btn_close.clicked(event):
                self.running = False
                return

            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE,
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
            ):
                self.running = False
                return

    def run(self):
        while self.running:
            self.clock.tick(60)
            self._handle_events()
            self._draw()


if __name__ == "__main__":
    from src.interface.config_window import ConfigWindow
    from src.interface.simulation import SimulationWindow

    cfg = ConfigWindow()
    ln = cfg.run()
    if ln is not None:
        sim = SimulationWindow(ln, cantidad_productos=max(1, ln.cantidad_ingreso or 1))
        sim.run()
        FinalReportWindow(ln, finish_reason="manual").run()
        pygame.quit()