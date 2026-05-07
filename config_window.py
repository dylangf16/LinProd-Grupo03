"""
config_window.py  —  Interfaz gráfica de configuración de la línea de producción.

Flujo:
    ventana = ConfigWindow()
    linea   = ventana.run()   # retorna LineaProduccion lista o None si se canceló
"""

import json
import os

import pygame

from clase_linea_produccion import LineaProduccion
from clase_proceso import Proceso
from clase_tarea import Tarea

# ── Paleta ────────────────────────────────────────────────────────────────────
BG       = (28,  28,  35)
PANEL    = (40,  40,  50)
PANEL2   = (50,  50,  62)
BORDER   = (75,  75,  90)
SEP_COL  = (60,  60,  75)
TEXT     = (220, 220, 220)
TEXT_DIM = (130, 130, 145)
SEL_BG   = (70,  100, 200)
BTN_G    = (55,  150,  70)
BTN_R    = (190,  55,  55)
BTN_B    = (45,  120, 195)
BTN_GR   = (85,   85,  98)
ACCENT   = (255, 200,  50)
INP_BG   = (35,  35,  45)
INP_ACT  = (48,  55,  78)

# ── Dimensiones ───────────────────────────────────────────────────────────────
W, H    = 1200, 760
HDR_H   = 52
C1_W    = 285
C2_W    = 345
C3_W    = W - C1_W - C2_W   # 570
CONT_H  = H - HDR_H          # 708

C1_X = 0
C2_X = C1_W
C3_X = C1_W + C2_W

ROW_H = 36
BTN_H = 30
PAD   = 12

# Posiciones fijas de la columna 3
_PX    = C3_X + PAD           # x base: 632
_PY    = HDR_H + PAD * 2      # y inicio props: 76  (más holgura bajo el header)
_SIM_Y = 330                   # y inicio sección parámetros de simulación


# ── Primitivos UI ─────────────────────────────────────────────────────────────

class Button:
    def __init__(self, rect, label, color=BTN_GR):
        self.rect   = pygame.Rect(rect)
        self.label  = label
        self.color  = color
        self._hover = False

    def draw(self, surf, font):
        c = tuple(min(255, v + 28) for v in self.color) if self._hover else self.color
        pygame.draw.rect(surf, c, self.rect, border_radius=5)
        pygame.draw.rect(surf, BORDER, self.rect, 1, border_radius=5)
        t = font.render(self.label, True, TEXT)
        surf.blit(t, t.get_rect(center=self.rect.center))

    def update_hover(self, pos):
        self._hover = self.rect.collidepoint(pos)

    def clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))


class TextInput:
    def __init__(self, rect, placeholder="", numeric=False, max_len=40):
        self.rect    = pygame.Rect(rect)
        self.ph      = placeholder
        self.numeric = numeric
        self.max_len = max_len
        self.text    = ""
        self.active  = False
        self._ct     = 0
        self._cv     = True

    def draw(self, surf, font):
        bg = INP_ACT if self.active else INP_BG
        bc = SEL_BG  if self.active else BORDER
        pygame.draw.rect(surf, bg, self.rect, border_radius=4)
        pygame.draw.rect(surf, bc, self.rect, 1, border_radius=4)
        disp  = self.text if self.text else self.ph
        color = TEXT if self.text else TEXT_DIM
        t = font.render(disp, True, color)
        surf.blit(t, (self.rect.x + 8, self.rect.y + (self.rect.h - t.get_height()) // 2))
        if self.active and self._cv:
            cx = self.rect.x + 8 + font.size(self.text)[0]
            pygame.draw.line(surf, TEXT, (cx, self.rect.y + 5), (cx, self.rect.bottom - 5), 2)

    def update(self, dt):
        self._ct += dt
        if self._ct >= 500:
            self._cv = not self._cv
            self._ct = 0

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_TAB, pygame.K_ESCAPE):
                self.active = False
            elif len(self.text) < self.max_len:
                ch = event.unicode
                if self.numeric and not ch.isdigit():
                    return
                self.text += ch


class Checkbox:
    def __init__(self, x, y, label):
        self.rect    = pygame.Rect(x, y, 20, 20)
        self.label   = label
        self.checked = False

    def draw(self, surf, font):
        pygame.draw.rect(surf, INP_BG, self.rect, border_radius=3)
        pygame.draw.rect(surf, BORDER, self.rect, 1, border_radius=3)
        if self.checked:
            pygame.draw.rect(surf, SEL_BG, self.rect.inflate(-5, -5), border_radius=2)
        t = font.render(self.label, True, TEXT)
        surf.blit(t, (self.rect.right + 7, self.rect.centery - t.get_height() // 2))

    def handle(self, event):
        if (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos)):
            self.checked = not self.checked
            return True
        return False


# ── Ventana de configuración ──────────────────────────────────────────────────

class ConfigWindow:
    CONFIG_FILE = "configuracion_linea.json"

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("LinProd — Configuración de Línea de Producción")
        self.clock  = pygame.time.Clock()

        self.font_h  = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.font    = pygame.font.SysFont("Segoe UI", 18)
        self.font_sm = pygame.font.SysFont("Segoe UI", 15)

        # Estado: lista de dicts {nombre, es_inicial, es_final, tareas:[{nombre,tiempo}]}
        self.procesos_cfg: list[dict] = []
        self.sel_proc:  int | None = None
        self.sel_tarea: int | None = None

        # ── Widgets col3: propiedades de proceso ──────────────────────────────
        # Offsets desde _PY: título(0) → label(+20) → input(+36) → checks(+82) → btn(+112)
        self.inp_proc_nombre = TextInput(
            (_PX, _PY + 58, C3_W - PAD * 2, 32), placeholder="Nombre del proceso")
        self.chk_inicial = Checkbox(_PX,       _PY + 110, "Proceso Inicial")
        self.chk_final   = Checkbox(_PX + 180, _PY + 110, "Proceso Final")
        self.btn_proc_ok = Button((_PX, _PY + 148, 130, BTN_H + 4), "Aplicar", BTN_B)

        # ── Widgets col3: propiedades de tarea ───────────────────────────────
        # Misma zona que proceso (se muestran de forma alternada)
        # Offsets desde _PY: título(0) → label(+20) → input(+36) → label(+82) → input(+98) → btn(+144)
        self.inp_tarea_nombre = TextInput(
            (_PX, _PY + 58, C3_W - PAD * 2, 32), placeholder="Nombre de la tarea")
        self.inp_tarea_tiempo = TextInput(
            (_PX, _PY + 130, 120, 32), placeholder="Ciclos", numeric=True, max_len=5)
        self.btn_tarea_ok = Button((_PX, _PY + 180, 130, BTN_H + 4), "Aplicar", BTN_B)

        # ── Widgets col3: parámetros de simulación (posición fija) ───────────
        # Offsets desde _SIM_Y: título(0) → label(+18) → input(+34) → acciones(+80) → construir(+118)
        half_w = (C3_W - PAD * 2 - 8) // 2
        self.inp_cantidad  = TextInput(
            (_PX, _SIM_Y + 52, 130, 32), placeholder="# productos", numeric=True, max_len=4)
        self.btn_guardar   = Button((_PX,              _SIM_Y + 104,         half_w, BTN_H + 4), "Guardar JSON",  BTN_GR)
        self.btn_cargar    = Button((_PX + half_w + 8, _SIM_Y + 104,         half_w, BTN_H + 4), "Cargar JSON",   BTN_GR)
        self.btn_construir = Button((_PX,              _SIM_Y + 104 + BTN_H + 12, C3_W - PAD * 2, 40),
                                    "  Construir Linea de Produccion  >", BTN_G)

        # ── Widgets col1 / col2: botones de lista ─────────────────────────────
        c_btn_y = HDR_H + CONT_H - BTN_H - PAD   # 718
        qw = (C1_W - PAD * 2 - 12) // 4
        self.btn_add_proc = Button((C1_X + PAD,              c_btn_y, qw, BTN_H), "+",       BTN_G)
        self.btn_del_proc = Button((C1_X + PAD + (qw + 4),   c_btn_y, qw, BTN_H), "-",       BTN_R)
        self.btn_up_proc  = Button((C1_X + PAD + (qw + 4)*2, c_btn_y, qw, BTN_H), "^",       BTN_GR)
        self.btn_dn_proc  = Button((C1_X + PAD + (qw + 4)*3, c_btn_y, qw, BTN_H), "v",       BTN_GR)

        hw = (C2_W - PAD * 2 - 8) // 2
        self.btn_add_tarea = Button((C2_X + PAD,           c_btn_y, hw, BTN_H), "+ Tarea", BTN_G)
        self.btn_del_tarea = Button((C2_X + PAD + hw + 8,  c_btn_y, hw, BTN_H), "- Tarea", BTN_R)

        self.linea_resultado: LineaProduccion | None = None

        print("[INFO] Sistema iniciado. Configura tu linea de produccion.")

    # ── Modo de la columna 3 ──────────────────────────────────────────────────

    def _props_mode(self):
        """'task' si hay tarea seleccionada, 'process' si solo proceso, 'none' si nada."""
        if self.sel_proc is not None and self.sel_tarea is not None:
            return "task"
        if self.sel_proc is not None:
            return "process"
        return "none"

    # ── Carga de formularios ──────────────────────────────────────────────────

    def _load_proc_to_form(self):
        if self.sel_proc is None:
            return
        p = self.procesos_cfg[self.sel_proc]
        self.inp_proc_nombre.text = p["nombre"]
        self.chk_inicial.checked  = p["es_inicial"]
        self.chk_final.checked    = p["es_final"]

    def _load_tarea_to_form(self):
        if self.sel_proc is None or self.sel_tarea is None:
            return
        t = self.procesos_cfg[self.sel_proc]["tareas"][self.sel_tarea]
        self.inp_tarea_nombre.text = t["nombre"]
        self.inp_tarea_tiempo.text = str(t["tiempo"])

    # ── Acciones: procesos ────────────────────────────────────────────────────

    def _add_proceso(self):
        n = len(self.procesos_cfg) + 1
        self.procesos_cfg.append({
            "nombre":     f"Proceso_{n}",
            "es_inicial": n == 1,
            "es_final":   False,
            "tareas":     [],
        })
        self.sel_proc  = len(self.procesos_cfg) - 1
        self.sel_tarea = None
        self._load_proc_to_form()
        print(f"[INFO] Proceso_{n} creado.")

    def _del_proceso(self):
        if self.sel_proc is None:
            return
        nombre = self.procesos_cfg[self.sel_proc]["nombre"]
        self.procesos_cfg.pop(self.sel_proc)
        self.sel_proc  = min(self.sel_proc, len(self.procesos_cfg) - 1) if self.procesos_cfg else None
        self.sel_tarea = None
        if self.sel_proc is not None:
            self._load_proc_to_form()
        else:
            self.inp_proc_nombre.text = ""
            self.chk_inicial.checked  = False
            self.chk_final.checked    = False
        print(f"[INFO] Proceso '{nombre}' eliminado.")

    def _move_proc(self, delta: int):
        if self.sel_proc is None:
            return
        j = self.sel_proc + delta
        if 0 <= j < len(self.procesos_cfg):
            cfg = self.procesos_cfg
            cfg[self.sel_proc], cfg[j] = cfg[j], cfg[self.sel_proc]
            self.sel_proc = j
            print(f"[INFO] Proceso movido a posicion {j + 1}.")

    def _apply_proc(self):
        if self.sel_proc is None:
            return
        nombre = self.inp_proc_nombre.text.strip()
        if not nombre:
            print("[ERROR] El nombre del proceso no puede estar vacio.")
            return
        self.procesos_cfg[self.sel_proc]["nombre"] = nombre
        print(f"[INFO] Nombre del proceso actualizado a '{nombre}'.")

    def _auto_save_flags(self):
        """Guarda inmediatamente el estado de los checkboxes al toggelearlos."""
        if self.sel_proc is None:
            return
        for i, p in enumerate(self.procesos_cfg):
            if i == self.sel_proc:
                continue
            if self.chk_inicial.checked and p["es_inicial"]:
                print(f"[ERROR] Ya existe un proceso INICIAL: '{p['nombre']}'.")
                self.chk_inicial.checked = False
                return
            if self.chk_final.checked and p["es_final"]:
                print(f"[ERROR] Ya existe un proceso FINAL: '{p['nombre']}'.")
                self.chk_final.checked = False
                return
        p = self.procesos_cfg[self.sel_proc]
        p["es_inicial"] = self.chk_inicial.checked
        p["es_final"]   = self.chk_final.checked
        print(f"[INFO] '{p['nombre']}': INICIAL={p['es_inicial']}, FINAL={p['es_final']}")

    # ── Acciones: tareas ──────────────────────────────────────────────────────

    def _add_tarea(self):
        if self.sel_proc is None:
            print("[WARN] Selecciona un proceso primero.")
            return
        tareas = self.procesos_cfg[self.sel_proc]["tareas"]
        n = len(tareas) + 1
        tareas.append({"nombre": f"Tarea_{n}", "tiempo": 1})
        self.sel_tarea = len(tareas) - 1
        self._load_tarea_to_form()
        print(f"[INFO] Tarea_{n} agregada a '{self.procesos_cfg[self.sel_proc]['nombre']}'.")

    def _del_tarea(self):
        if self.sel_proc is None or self.sel_tarea is None:
            return
        tareas = self.procesos_cfg[self.sel_proc]["tareas"]
        nombre = tareas[self.sel_tarea]["nombre"]
        tareas.pop(self.sel_tarea)
        self.sel_tarea = min(self.sel_tarea, len(tareas) - 1) if tareas else None
        if self.sel_tarea is not None:
            self._load_tarea_to_form()
        else:
            self.inp_tarea_nombre.text = ""
            self.inp_tarea_tiempo.text = ""
        print(f"[INFO] Tarea '{nombre}' eliminada.")

    def _apply_tarea(self):
        if self.sel_proc is None or self.sel_tarea is None:
            return
        nombre = self.inp_tarea_nombre.text.strip()
        t_str  = self.inp_tarea_tiempo.text.strip()
        if not nombre:
            print("[ERROR] El nombre de la tarea no puede estar vacio.")
            return
        if not t_str or int(t_str) < 1:
            print("[ERROR] El tiempo de proceso debe ser un entero >= 1.")
            return
        tarea = self.procesos_cfg[self.sel_proc]["tareas"][self.sel_tarea]
        tarea["nombre"] = nombre
        tarea["tiempo"] = int(t_str)
        proc = self.procesos_cfg[self.sel_proc]["nombre"]
        print(f"[INFO] Tarea '{nombre}' (TP={tarea['tiempo']}) guardada en '{proc}'.")

    # ── Acciones: JSON y construcción ─────────────────────────────────────────

    def _guardar_json(self):
        data = {
            "procesos":         self.procesos_cfg,
            "cantidad_ingreso": int(self.inp_cantidad.text or 0),
        }
        with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[INFO] Configuracion guardada en '{self.CONFIG_FILE}'.")

    def _cargar_json(self):
        if not os.path.exists(self.CONFIG_FILE):
            print(f"[ERROR] Archivo '{self.CONFIG_FILE}' no encontrado.")
            return
        with open(self.CONFIG_FILE, encoding="utf-8") as f:
            data = json.load(f)
        self.procesos_cfg = data.get("procesos", [])
        cantidad = data.get("cantidad_ingreso", 0)
        self.inp_cantidad.text = str(cantidad) if cantidad else ""
        self.sel_proc  = 0 if self.procesos_cfg else None
        self.sel_tarea = None
        if self.sel_proc is not None:
            self._load_proc_to_form()
        print(f"[INFO] Cargados {len(self.procesos_cfg)} proceso(s), cantidad={cantidad}.")

    def _construir_linea(self) -> LineaProduccion | None:
        if not self.procesos_cfg:
            print("[ERROR] No hay procesos definidos.")
            return None
        iniciales = [p for p in self.procesos_cfg if p["es_inicial"]]
        finales   = [p for p in self.procesos_cfg if p["es_final"]]
        if len(iniciales) != 1:
            print(f"[ERROR] Se requiere exactamente 1 proceso inicial (hay {len(iniciales)}).")
            return None
        if len(finales) != 1:
            print(f"[ERROR] Se requiere exactamente 1 proceso final (hay {len(finales)}).")
            return None
        for pc in self.procesos_cfg:
            if not pc["tareas"]:
                print(f"[ERROR] El proceso '{pc['nombre']}' no tiene tareas.")
                return None
        cant_s = self.inp_cantidad.text.strip()
        if not cant_s or int(cant_s) < 1:
            print("[ERROR] La cantidad de productos debe ser un entero >= 1.")
            return None
        cantidad = int(cant_s)

        linea = LineaProduccion("Linea Configurada")
        for pc in self.procesos_cfg:
            tareas  = [Tarea(t["nombre"], t["tiempo"]) for t in pc["tareas"]]
            proceso = Proceso(pc["nombre"], tareas,
                              es_inicial=pc["es_inicial"], es_final=pc["es_final"])
            linea.agregar_proceso(proceso)

        sep = "-" * 58
        print(sep)
        print(f"LineaProduccion '{linea.nombre}' construida exitosamente.")
        print(f"  Procesos ({len(linea.procesos)}) en orden:")
        for idx, p in enumerate(linea.procesos):
            flags = []
            if p.es_inicial: flags.append("INICIAL")
            if p.es_final:   flags.append("FINAL")
            flag_s = f"  [{', '.join(flags)}]" if flags else ""
            ant = linea.procesos[idx - 1].nombre if idx > 0 else "ninguno"
            sig = linea.procesos[idx + 1].nombre if idx + 1 < len(linea.procesos) else "ninguno"
            print(f"    [{idx + 1}] {p.nombre}{flag_s}  anterior={ant}  siguiente={sig}")
            for j, t in enumerate(p.tareas):
                print(f"        tarea[{j + 1}] {t.nombre}  TP={t.tiempo_proceso} ciclos")
        print(f"  Proceso inicial : {linea.get_proceso_inicial().nombre}")
        print(f"  Proceso final   : {linea.get_proceso_final().nombre}")
        print(f"  Productos a ingresar: {cantidad}")
        print(sep)
        linea.imprimir_estado()

        self.linea_resultado = linea
        return linea

    # ── Dibujo ────────────────────────────────────────────────────────────────

    def _draw_header(self):
        pygame.draw.rect(self.screen, (22, 22, 32), (0, 0, W, HDR_H))
        pygame.draw.line(self.screen, BORDER, (0, HDR_H - 1), (W, HDR_H - 1), 1)
        t = self.font_h.render(
            "LinProd  -  Configuracion de Linea de Produccion", True, TEXT)
        self.screen.blit(t, (PAD * 2, (HDR_H - t.get_height()) // 2))

    def _draw_col1(self):
        pygame.draw.rect(self.screen, PANEL, (C1_X, HDR_H, C1_W, CONT_H))
        pygame.draw.line(self.screen, BORDER, (C1_W, HDR_H), (C1_W, H), 1)

        self.screen.blit(self.font_sm.render("PROCESOS", True, ACCENT),
                         (C1_X + PAD, HDR_H + 6))

        list_top  = HDR_H + PAD + 18
        mouse_pos = pygame.mouse.get_pos()
        for i, pc in enumerate(self.procesos_cfg):
            row = pygame.Rect(C1_X + 4, list_top + i * (ROW_H + 2), C1_W - 8, ROW_H)
            if i == self.sel_proc:
                pygame.draw.rect(self.screen, SEL_BG, row, border_radius=4)
            elif row.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, PANEL2, row, border_radius=4)
            flags = (" [I]" if pc["es_inicial"] else "") + (" [F]" if pc["es_final"] else "")
            t = self.font_sm.render(f"{i + 1}. {pc['nombre']}{flags}", True, TEXT)
            self.screen.blit(t, (C1_X + PAD, row.y + (ROW_H - t.get_height()) // 2))

        for btn in (self.btn_add_proc, self.btn_del_proc,
                    self.btn_up_proc,  self.btn_dn_proc):
            btn.draw(self.screen, self.font_sm)

    def _draw_col2(self):
        pygame.draw.rect(self.screen, PANEL2, (C2_X, HDR_H, C2_W, CONT_H))
        pygame.draw.line(self.screen, BORDER, (C2_X + C2_W, HDR_H), (C2_X + C2_W, H), 1)

        proc_nombre = (self.procesos_cfg[self.sel_proc]["nombre"]
                       if self.sel_proc is not None else "(selecciona proceso)")
        self.screen.blit(self.font_sm.render(f"TAREAS  -  {proc_nombre}", True, ACCENT),
                         (C2_X + PAD, HDR_H + 6))

        list_top  = HDR_H + PAD + 18
        mouse_pos = pygame.mouse.get_pos()
        if self.sel_proc is not None:
            for i, tc in enumerate(self.procesos_cfg[self.sel_proc]["tareas"]):
                row = pygame.Rect(C2_X + 4, list_top + i * (ROW_H + 2), C2_W - 8, ROW_H)
                if i == self.sel_tarea:
                    pygame.draw.rect(self.screen, SEL_BG, row, border_radius=4)
                elif row.collidepoint(mouse_pos):
                    pygame.draw.rect(self.screen, PANEL, row, border_radius=4)
                t = self.font_sm.render(
                    f"{i + 1}. {tc['nombre']}  (TP={tc['tiempo']})", True, TEXT)
                self.screen.blit(t, (C2_X + PAD, row.y + (ROW_H - t.get_height()) // 2))

        for btn in (self.btn_add_tarea, self.btn_del_tarea):
            btn.draw(self.screen, self.font_sm)

    def _draw_col3(self):
        pygame.draw.rect(self.screen, PANEL, (C3_X, HDR_H, C3_W, CONT_H))

        def lbl(text, y, dim=False):
            t = self.font_sm.render(text, True, TEXT_DIM if dim else ACCENT)
            self.screen.blit(t, (_PX, y))

        def sep(y):
            pygame.draw.line(self.screen, SEP_COL, (_PX, y), (C3_X + C3_W - PAD, y), 1)

        mode = self._props_mode()

        # ── Sección condicional (proceso O tarea) ─────────────────────────────
        if mode == "process":
            lbl("PROPIEDADES DEL PROCESO", _PY)
            lbl("Nombre:", _PY + 36, dim=True)
            self.inp_proc_nombre.draw(self.screen, self.font)
            self.chk_inicial.draw(self.screen, self.font_sm)
            self.chk_final.draw(self.screen, self.font_sm)
            self.btn_proc_ok.draw(self.screen, self.font_sm)

        elif mode == "task":
            lbl("PROPIEDADES DE LA TAREA", _PY)
            lbl("Nombre:", _PY + 36, dim=True)
            self.inp_tarea_nombre.draw(self.screen, self.font)
            lbl("Tiempo de proceso (ciclos):", _PY + 108, dim=True)
            self.inp_tarea_tiempo.draw(self.screen, self.font)
            self.btn_tarea_ok.draw(self.screen, self.font_sm)

        else:
            hint = self.font_sm.render("Selecciona un proceso o tarea.", True, TEXT_DIM)
            self.screen.blit(hint, (_PX, _PY))

        # ── Sección fija: parámetros de simulación ────────────────────────────
        sep(_SIM_Y - 18)
        lbl("PARAMETROS DE SIMULACION", _SIM_Y)
        lbl("Cantidad de productos a ingresar:", _SIM_Y + 32, dim=True)
        self.inp_cantidad.draw(self.screen, self.font)
        self.btn_guardar.draw(self.screen, self.font_sm)
        self.btn_cargar.draw(self.screen, self.font_sm)
        self.btn_construir.draw(self.screen, self.font_sm)

    def draw(self):
        self.screen.fill(BG)
        self._draw_header()
        self._draw_col1()
        self._draw_col2()
        self._draw_col3()
        pygame.display.flip()

    # ── Clics en listas ───────────────────────────────────────────────────────

    def _handle_list_clicks(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        list_top = HDR_H + PAD + 18

        for i in range(len(self.procesos_cfg)):
            row = pygame.Rect(C1_X + 4, list_top + i * (ROW_H + 2), C1_W - 8, ROW_H)
            if row.collidepoint(event.pos):
                if self.sel_proc != i:
                    self.sel_proc  = i
                    self.sel_tarea = None
                    self._load_proc_to_form()
                    print(f"[INFO] Proceso '{self.procesos_cfg[i]['nombre']}' seleccionado.")
                return

        if self.sel_proc is not None:
            for i, tc in enumerate(self.procesos_cfg[self.sel_proc]["tareas"]):
                row = pygame.Rect(C2_X + 4, list_top + i * (ROW_H + 2), C2_W - 8, ROW_H)
                if row.collidepoint(event.pos):
                    if self.sel_tarea != i:
                        self.sel_tarea = i
                        self._load_tarea_to_form()
                        print(f"[INFO] Tarea '{tc['nombre']}' seleccionada.")
                    return

    # ── Loop principal ────────────────────────────────────────────────────────

    def _visible_inputs(self):
        """Inputs que reciben eventos según el modo actual."""
        mode = self._props_mode()
        if mode == "process":
            return (self.inp_proc_nombre, self.inp_cantidad)
        if mode == "task":
            return (self.inp_tarea_nombre, self.inp_tarea_tiempo, self.inp_cantidad)
        return (self.inp_cantidad,)

    def _all_inputs(self):
        return (self.inp_proc_nombre, self.inp_tarea_nombre,
                self.inp_tarea_tiempo, self.inp_cantidad)

    def _all_buttons(self):
        return (self.btn_add_proc,  self.btn_del_proc,
                self.btn_up_proc,   self.btn_dn_proc,
                self.btn_add_tarea, self.btn_del_tarea,
                self.btn_proc_ok,   self.btn_tarea_ok,
                self.btn_guardar,   self.btn_cargar,
                self.btn_construir)

    def run(self) -> LineaProduccion | None:
        running = True
        while running:
            dt = self.clock.tick(60)

            for inp in self._all_inputs():
                inp.update(dt)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

                if event.type == pygame.MOUSEMOTION:
                    for btn in self._all_buttons():
                        btn.update_hover(event.pos)

                # Solo los inputs visibles reciben eventos de teclado/clic
                for inp in self._visible_inputs():
                    inp.handle(event)

                # Checkboxes: guardan inmediatamente al toggelear
                if self.chk_inicial.handle(event):
                    self._auto_save_flags()
                if self.chk_final.handle(event):
                    self._auto_save_flags()

                self._handle_list_clicks(event)

                if self.btn_add_proc.clicked(event):
                    self._add_proceso()
                elif self.btn_del_proc.clicked(event):
                    self._del_proceso()
                elif self.btn_up_proc.clicked(event):
                    self._move_proc(-1)
                elif self.btn_dn_proc.clicked(event):
                    self._move_proc(1)
                elif self.btn_add_tarea.clicked(event):
                    self._add_tarea()
                elif self.btn_del_tarea.clicked(event):
                    self._del_tarea()
                elif self.btn_proc_ok.clicked(event):
                    self._apply_proc()
                elif self.btn_tarea_ok.clicked(event):
                    self._apply_tarea()
                elif self.btn_guardar.clicked(event):
                    self._guardar_json()
                elif self.btn_cargar.clicked(event):
                    self._cargar_json()
                elif self.btn_construir.clicked(event):
                    result = self._construir_linea()
                    if result is not None:
                        running = False

            self.draw()

        pygame.quit()
        return self.linea_resultado


# ── Punto de entrada ──────────────────────────────────────────────────────────

def main():
    ventana = ConfigWindow()
    linea   = ventana.run()
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
