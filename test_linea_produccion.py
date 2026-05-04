"""Pruebas funcionales de LineaProduccion.

Restricciones del PDF que se validan:
  * La linea debe tener uno o mas procesos.
  * Debe existir un proceso inicial unico.
  * Debe existir un proceso final unico.
  * Cada proceso tiene una o mas tareas.
  * Las tareas tienen orden de ejecucion respetado.
  * Cada tarea procesa un producto a la vez (cola FIFO para los demas).
  * Cuando termina, el producto pasa de inmediato al siguiente paso.
  * Se debe poder pausar / reanudar / reiniciar la simulacion.
"""

import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from clase_estadistica import Estadisticas
from clase_linea_produccion import LineaProduccion
from clase_proceso import Proceso
from clase_tarea import Tarea

# ----------------------------------------------------------------------
# Utilidades de verificacion
# ----------------------------------------------------------------------
resultados = []  # lista de (nombre_test, criterio, ok)


def verificar(test, criterio, condicion, detalle=""):
    estado = "OK  " if condicion else "FAIL"
    resultados.append((test, criterio, condicion))
    extra = f"  ({detalle})" if detalle else ""
    print(f"    [{estado}] {criterio}{extra}")
    return condicion


def construir_linea(nombre, configuracion):
    """configuracion: lista de dicts con keys nombre, tareas, inicial, final."""
    linea = LineaProduccion(nombre)
    for cfg in configuracion:
        tareas = [Tarea(n, tp) for (n, tp) in cfg["tareas"]]
        proc = Proceso(
            cfg["nombre"],
            tareas,
            es_inicial=cfg.get("inicial", False),
            es_final=cfg.get("final", False),
        )
        linea.agregar_proceso(proc)
    return linea


def correr_test(numero, descripcion, configuracion, cantidad_productos):
    print()
    print(f"=== Test {numero}: {descripcion} ===")
    linea = construir_linea(f"L{numero}", configuracion)
    test = f"T{numero}"

    # ---- Pre-condiciones de configuracion (segun PDF) ----
    verificar(
        test,
        "Existe al menos 1 proceso",
        len(linea.procesos) >= 1,
        f"{len(linea.procesos)} procesos",
    )
    verificar(
        test,
        "Existe proceso inicial unico",
        sum(p.es_inicial for p in linea.procesos) == 1,
    )
    verificar(
        test,
        "Existe proceso final unico",
        sum(p.es_final for p in linea.procesos) == 1,
    )
    verificar(
        test,
        "Cada proceso tiene >= 1 tarea",
        all(len(p.tareas) >= 1 for p in linea.procesos),
    )
    verificar(
        test,
        "Encadenamiento bidireccional Proceso<->Proceso",
        all(
            (p.siguiente_proceso is None or p.siguiente_proceso.proceso_anterior is p)
            for p in linea.procesos
        ),
    )
    verificar(
        test,
        "Cada tarea conoce a su proceso",
        all(t.proceso is p for p in linea.procesos for t in p.tareas),
    )
    verificar(
        test,
        "Tareas encadenadas en orden dentro de cada proceso",
        all(
            p.tareas[i].siguiente_tarea is p.tareas[i + 1]
            for p in linea.procesos
            for i in range(len(p.tareas) - 1)
        ),
    )

    # ---- Inyectar productos y correr ----
    linea.cargar_productos(cantidad_productos)
    linea.correr(max_ciclos=10000)
    # estadística
    from clase_estadistica import Estadisticas

    estadisticas = Estadisticas(linea)
    estadisticas.mostrar_resumen()

    # ---- Post-condiciones del corrido ----
    tareas_total = [t for p in linea.procesos for t in p.tareas]
    suma_tiempos = sum(t.tiempo_proceso for t in tareas_total)

    verificar(
        test,
        "Todos los productos finalizaron",
        linea.todos_finalizados(),
        f"{sum(1 for p in linea.productos if p.estado == 'finalizado')}/"
        f"{len(linea.productos)}",
    )
    verificar(
        test,
        "tiempo_salida >= tiempo_ingreso para todos",
        all(p.tiempo_salida >= p.tiempo_ingreso for p in linea.productos),
    )
    verificar(
        test,
        "tiempo_salida >= suma de tiempos (recorrido minimo)",
        all(p.tiempo_salida >= suma_tiempos for p in linea.productos),
        f"min esperado={suma_tiempos}",
    )
    verificar(
        test,
        "Salida en orden FIFO de ingreso",
        all(
            linea.productos[i].tiempo_salida <= linea.productos[i + 1].tiempo_salida
            for i in range(len(linea.productos) - 1)
        ),
    )
    verificar(
        test,
        "No quedan productos en cola al final",
        all(t.cantidad_en_espera() == 0 for t in tareas_total),
    )
    verificar(
        test,
        "Ninguna tarea quedo procesando al final",
        all(t.esta_libre() for t in tareas_total),
    )

    print(
        f"  Resumen: procesos={len(linea.procesos)}, "
        f"tareas_totales={len(tareas_total)}, "
        f"productos={len(linea.productos)}, "
        f"T_fin={linea.tiempo_actual}, "
        f"primero_salio=T{linea.productos[0].tiempo_salida}, "
        f"ultimo_salio=T{linea.productos[-1].tiempo_salida}"
    )
    return linea


# ----------------------------------------------------------------------
# 5 configuraciones distintas
# ----------------------------------------------------------------------
TESTS = [
    {
        "descripcion": "Linea minima: 1 proceso, 1 tarea, 3 productos",
        "config": [
            {
                "nombre": "Unico",
                "tareas": [("T1", 2)],
                "inicial": True,
                "final": True,
            },
        ],
        "productos": 3,
    },
    {
        "descripcion": "2 procesos con 1 y 3 tareas distintas; 5 productos",
        "config": [
            {
                "nombre": "Recepcion",
                "tareas": [("Inspeccion", 1)],
                "inicial": True,
            },
            {
                "nombre": "Manufactura",
                "tareas": [("Corte", 2), ("Pulido", 1), ("Pintado", 3)],
                "final": True,
            },
        ],
        "productos": 5,
    },
    {
        "descripcion": "3 procesos con 1, 3 y 2 tareas distintas; 4 productos",
        "config": [
            {
                "nombre": "Recepcion",
                "tareas": [("Inspeccion", 1)],
                "inicial": True,
            },
            {
                "nombre": "Ensamblaje",
                "tareas": [("CorteA", 2), ("CorteB", 1), ("Soldadura", 3)],
            },
            {
                "nombre": "Empaque",
                "tareas": [("Pintura", 2), ("Caja", 1)],
                "final": True,
            },
        ],
        "productos": 4,
    },
    {
        "descripcion": "5 procesos con 1, 2, 5, 3 y 4 tareas distintas; 6 productos",
        "config": [
            {
                "nombre": "Entrada",
                "tareas": [("Recepcion", 1)],
                "inicial": True,
            },
            {
                "nombre": "Preparacion",
                "tareas": [("Lavado", 1), ("Secado", 2)],
            },
            {
                "nombre": "Mecanizado",
                "tareas": [
                    ("Fresado", 1),
                    ("Torneado", 1),
                    ("Taladrado", 1),
                    ("Rectificado", 2),
                    ("Inspeccion", 1),
                ],
            },
            {
                "nombre": "Acabado",
                "tareas": [("Pulido", 2), ("Pintado", 1), ("Barnizado", 2)],
            },
            {
                "nombre": "Empaque",
                "tareas": [
                    ("Etiquetado", 1),
                    ("Sellado", 1),
                    ("Encajado", 2),
                    ("Despacho", 1),
                ],
                "final": True,
            },
        ],
        "productos": 6,
    },
    {
        "descripcion": "Cuello de botella: 3 procesos con 2, 3 y 1 tareas distintas; 8 productos",
        "config": [
            {
                "nombre": "Entrada",
                "tareas": [("Recibo", 1), ("Clasificacion", 1)],
                "inicial": True,
            },
            {
                "nombre": "Procesamiento",
                "tareas": [
                    ("Preparacion", 1),
                    ("OperacionLenta", 5),
                    ("Verificacion", 1),
                ],
            },
            {
                "nombre": "Salida",
                "tareas": [("Empaque", 1)],
                "final": True,
            },
        ],
        "productos": 8,
    },
]


for i, t in enumerate(TESTS, start=1):
    correr_test(i, t["descripcion"], t["config"], t["productos"])


# ----------------------------------------------------------------------
# Tests adicionales: validaciones
# ----------------------------------------------------------------------
print()
print("=== Test V: Validaciones de configuracion ===")

try:
    L = LineaProduccion("V1")
    L.agregar_proceso(Proceso("A", [Tarea("t", 1)], es_inicial=True))
    L.agregar_proceso(Proceso("B", [Tarea("t", 1)], es_inicial=True))
    verificar("V", "Rechaza un segundo proceso inicial", False, "no lanzo error")
except ValueError:
    verificar("V", "Rechaza un segundo proceso inicial", True)

try:
    L = LineaProduccion("V2")
    L.agregar_proceso(Proceso("A", [Tarea("t", 1)], es_final=True))
    L.agregar_proceso(Proceso("B", [Tarea("t", 1)], es_final=True))
    verificar("V", "Rechaza un segundo proceso final", False, "no lanzo error")
except ValueError:
    verificar("V", "Rechaza un segundo proceso final", True)

try:
    L = LineaProduccion("V3")
    L.cargar_productos(1)
    verificar("V", "Rechaza cargar productos sin procesos", False, "no lanzo error")
except ValueError:
    verificar("V", "Rechaza cargar productos sin procesos", True)

try:
    L = LineaProduccion("V4")
    L.agregar_proceso(Proceso("A", [Tarea("t", 1)]))  # sin inicial
    L.cargar_productos(1)
    verificar("V", "Rechaza cargar sin proceso inicial", False, "no lanzo error")
except ValueError:
    verificar("V", "Rechaza cargar sin proceso inicial", True)


# ----------------------------------------------------------------------
# Tests de pausa, reanudar y reinicio
# ----------------------------------------------------------------------
print()
print("=== Test P: Pausa, reanudar y reinicio ===")

linea = LineaProduccion("Pausable")
linea.agregar_proceso(Proceso("P1", [Tarea("T1", 2)], es_inicial=True))
linea.agregar_proceso(Proceso("P2", [Tarea("T2", 2)], es_final=True))
linea.cargar_productos(3)

linea.correr_hasta(3)
verificar("P", "Reloj llega a T=3", linea.tiempo_actual == 3)
verificar(
    "P",
    "En T=3 hay productos sin finalizar",
    any(p.estado != "finalizado" for p in linea.productos),
)

linea.pausar()
t_antes = linea.tiempo_actual
linea.tick()  # debe ser ignorado
verificar(
    "P",
    "Pausada: tick() no avanza el reloj",
    linea.tiempo_actual == t_antes,
)

linea.reanudar()
linea.correr()
verificar("P", "Reanudada: la linea termina", linea.todos_finalizados())

# Reinicio con distinta cantidad de productos
linea.reiniciar(2)
verificar("P", "Reinicio: tiempo vuelve a 0", linea.tiempo_actual == 0)
verificar("P", "Reinicio: cantidad nueva = 2", len(linea.productos) == 2)
# Tras reinicio + carga, solo la primera tarea del proceso inicial debe
# estar procesando; el resto debe estar libre y sin cola residual.
primera = linea.get_proceso_inicial().get_primera_tarea()
otras = [t for p in linea.procesos for t in p.tareas if t is not primera]
verificar(
    "P",
    "Reinicio: tareas distintas a la primera quedan libres y sin cola",
    all(t.esta_libre() and t.cantidad_en_espera() == 0 for t in otras),
)
verificar(
    "P",
    "Reinicio: primera tarea cargada con 1 producto (cola = N-1)",
    primera.esta_procesando and primera.cantidad_en_espera() == 1,
)
linea.correr()
verificar("P", "Reinicio: la linea termina ok", linea.todos_finalizados())


# ----------------------------------------------------------------------
# Resumen final
# ----------------------------------------------------------------------
print()
print("=" * 70)
print("RESUMEN DE VERIFICACIONES")
print("=" * 70)
print()
print("Criterios verificados en cada test:")
print("  * Configuracion segun PDF: >=1 proceso, inicial unico, final unico,")
print("    cada proceso con >=1 tarea, encadenamiento bidireccional, tareas en orden.")
print("  * Ejecucion correcta: todos los productos finalizan, tiempos coherentes,")
print("    salida en orden FIFO, no quedan productos en cola ni tareas ocupadas.")
print(
    "  * Validaciones: rechazo de inicial/final duplicado y configuracion incompleta."
)
print("  * Control: pausa detiene el reloj, reanudar continua, reinicio limpia estado.")
print()

total = len(resultados)
ok = sum(1 for _, _, c in resultados if c)
fail = total - ok

# Tabla por test
print(f"{'Test':<6} {'OK':>4} {'FAIL':>5} {'Total':>6}")
print("-" * 25)
tests_unicos = []
for t, _, _ in resultados:
    if t not in tests_unicos:
        tests_unicos.append(t)
for t in tests_unicos:
    grupo = [r for r in resultados if r[0] == t]
    g_ok = sum(1 for _, _, c in grupo if c)
    g_total = len(grupo)
    print(f"{t:<6} {g_ok:>4} {g_total - g_ok:>5} {g_total:>6}")
print("-" * 25)
print(f"{'TOTAL':<6} {ok:>4} {fail:>5} {total:>6}")
print()

if fail == 0:
    print("Resultado: TODAS LAS PRUEBAS PASARON")
    sys.exit(0)
else:
    print("Resultado: HUBO FALLOS. Detalle:")
    for t, c, ok_ in resultados:
        if not ok_:
            print(f"  - [{t}] {c}")
    sys.exit(1)
