from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from clase_producto import Producto
    from clase_tarea import Tarea


class Proceso:
    def __init__(
        self,
        nombre: str,
        tareas: list[Tarea],
        es_inicial: bool = False,
        es_final: bool = False,
    ):
        self.nombre: str = nombre
        self.tareas: list[Tarea] = list(tareas)
        self.es_inicial: bool = es_inicial
        self.es_final: bool = es_final

        self.siguiente_proceso: Proceso | None = None
        self.proceso_anterior: Proceso | None = None

        for i in range(len(self.tareas)):
            tarea = self.tareas[i]
            tarea.proceso = self
            if i + 1 < len(self.tareas):
                tarea.siguiente_tarea = self.tareas[i + 1]
            else:
                tarea.siguiente_tarea = None

    def conectar_siguiente(self, otro_proceso: Proceso) -> None:
        self.siguiente_proceso = otro_proceso
        otro_proceso.proceso_anterior = self

    def recibir_producto(self, producto: Producto) -> None:
        self.tareas[0].recibir_producto(producto)

    def entregar_siguiente(self, producto: Producto, tiempo_actual: int) -> None:
        if self.siguiente_proceso is not None:
            self.siguiente_proceso.recibir_producto(producto)
        else:
            producto.finalizar(tiempo_actual)

    def tick(self, tiempo_actual: int) -> None:
        for tarea in reversed(self.tareas):
            tarea.tick(tiempo_actual)

    def reiniciar(self) -> None:
        for tarea in self.tareas:
            tarea.reiniciar()

    def get_primera_tarea(self) -> Tarea | None:
        if not self.tareas:
            return None
        return self.tareas[0]

    def get_ultima_tarea(self) -> Tarea | None:
        if not self.tareas:
            return None
        return self.tareas[-1]

    def __str__(self):
        marca = ""
        if self.es_inicial:
            marca = " [INICIAL]"
        elif self.es_final:
            marca = " [FINAL]"
        return f"Proceso {self.nombre}{marca} ({len(self.tareas)} tareas)"
