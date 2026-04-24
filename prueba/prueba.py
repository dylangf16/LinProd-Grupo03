# linprod.py

import os
import random
import sys

CAPACIDAD_MAXIMA = 100


class Tarea:
    def __init__(self, nombre, tiempo_proceso):
        self.nombre = nombre
        self.tiempo_proceso = tiempo_proceso
        self.esta_procesando = False
        self.contenido_esperando = 0
        self.tiempo_restante = 0
        self.total_procesados = 0

    def recibir(self, cantidad):
        self.contenido_esperando += cantidad

    def tick(self):
        if self.esta_procesando:
            self.tiempo_restante -= 1
            if self.tiempo_restante == 0:
                self.esta_procesando = False
                self.total_procesados += 1

        if not self.esta_procesando and self.contenido_esperando > 0:
            self.esta_procesando = True
            self.contenido_esperando -= 1
            self.tiempo_restante = self.tiempo_proceso

    def __repr__(self):
        return (
            f"Tarea({self.nombre}, EP={self.esta_procesando}, "
            f"CE={self.contenido_esperando})"
        )


class Proceso:
    def __init__(self, nombre, tareas):
        self.nombre = nombre
        self.tareas = tareas
        self.tiempo_inicio = None
        self.tiempo_fin = None

    def recibir(self, cantidad):
        self.tareas[0].recibir(cantidad)

    def tick(self, tick_actual):
        for i, tarea in enumerate(self.tareas):
            tarea.tick()
            if i > 0 and not self.tareas[i - 1].esta_procesando:
                if self.tareas[i - 1].total_procesados > 0:
                    self.tareas[i].recibir(1)
                    self.tareas[i - 1].total_procesados -= 1

        if self.tiempo_inicio is None and self.tareas[0].esta_procesando:
            self.tiempo_inicio = tick_actual

        todas_listas = all(
            not t.esta_procesando and t.contenido_esperando == 0 for t in self.tareas
        )
        if todas_listas and self.tiempo_inicio is not None and self.tiempo_fin is None:
            self.tiempo_fin = tick_actual

    def finalizo(self):
        return self.tiempo_fin is not None


class LineaProduccion:
    def __init__(self, procesos, cantidad_ingreso):
        self.procesos = procesos
        self.cantidad_ingreso = cantidad_ingreso
        self.tick_actual = 0
        self.productos_finalizados = 0

    def iniciar(self):
        self.procesos[0].recibir(self.cantidad_ingreso)

    def simular(self):
        self.iniciar()
        MAX_TICKS = 1000

        while not self._todos_finalizaron() and self.tick_actual < MAX_TICKS:
            self.tick_actual += 1
            for i, proceso in enumerate(self.procesos):
                proceso.tick(self.tick_actual)
                if i > 0:
                    anterior = self.procesos[i - 1]
                    for tarea in anterior.tareas:
                        if tarea.total_procesados > 0:
                            proceso.recibir(tarea.total_procesados)
                            tarea.total_procesados = 0

        return self._generar_estadisticas()

    def _todos_finalizaron(self):
        return all(p.finalizo() for p in self.procesos)

    def _generar_estadisticas(self):
        stats = {
            "ticks_totales": self.tick_actual,
            "cantidad_productos": self.cantidad_ingreso,
            "procesos": [],
        }
        tarea_mayor_espera = None
        max_espera = 0

        for proceso in self.procesos:
            duracion = (proceso.tiempo_fin or self.tick_actual) - (
                proceso.tiempo_inicio or 0
            )
            stats["procesos"].append(
                {
                    "nombre": proceso.nombre,
                    "inicio": proceso.tiempo_inicio,
                    "fin": proceso.tiempo_fin,
                    "duracion": duracion,
                }
            )
            for tarea in proceso.tareas:
                if tarea.contenido_esperando > max_espera:
                    max_espera = tarea.contenido_esperando
                    tarea_mayor_espera = tarea.nombre

        stats["tarea_mayor_espera"] = tarea_mayor_espera
        return stats


def imprimir_estadisticas(stats):
    print("\n===== Estadísticas de la simulación =====")
    print(f"  Productos procesados : {stats['cantidad_productos']}")
    print(f"  Ticks totales        : {stats['ticks_totales']}")
    print(f"  Mayor espera en      : {stats['tarea_mayor_espera']}")
    print()
    for p in stats["procesos"]:
        print(f"  {p['nombre']}: T{p['inicio']} → T{p['fin']} ({p['duracion']} ticks)")


if __name__ == "__main__":
    t1 = Tarea("Tarea1", tiempo_proceso=1)
    t2 = Tarea("Tarea2", tiempo_proceso=2)
    t3 = Tarea("Tarea3", tiempo_proceso=2)
    t4 = Tarea("Tarea4", tiempo_proceso=2)

    p1 = Proceso("Proceso1", [t1, t2])
    p2 = Proceso("Proceso2", [t3, t4])

    linea = LineaProduccion(procesos=[p1, p2], cantidad_ingreso=5)
    estadisticas = linea.simular()
    imprimir_estadisticas(estadisticas)
