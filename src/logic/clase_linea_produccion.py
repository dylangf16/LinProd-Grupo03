from __future__ import annotations

from typing import TYPE_CHECKING

from clase_producto import Producto

if TYPE_CHECKING:
    from clase_proceso import Proceso


class LineaProduccion:
    def __init__(self, nombre: str = "Linea"):
        self.nombre: str = nombre
        self.procesos: list[Proceso] = []
        self.productos: list[Producto] = []
        self.cantidad_ingreso: int = 0
        self.tiempo_actual: int = 0
        self.pausada: bool = False

    def agregar_proceso(self, proceso: Proceso) -> None:
        if proceso.es_inicial:
            for p in self.procesos:
                if p.es_inicial:
                    raise ValueError("Ya existe un proceso inicial en la linea")
        if proceso.es_final:
            for p in self.procesos:
                if p.es_final:
                    raise ValueError("Ya existe un proceso final en la linea")
        if self.procesos:
            self.procesos[-1].conectar_siguiente(proceso)
        self.procesos.append(proceso)

    def eliminar_proceso(self, nombre: str) -> bool:
        proceso: Proceso | None = None
        for p in self.procesos:
            if p.nombre == nombre:
                proceso = p
                break
        if proceso is None:
            return False

        idx = self.procesos.index(proceso)
        anterior = self.procesos[idx - 1] if idx > 0 else None
        siguiente = self.procesos[idx + 1] if idx + 1 < len(self.procesos) else None

        if anterior is not None:
            anterior.siguiente_proceso = siguiente
        if siguiente is not None:
            siguiente.proceso_anterior = anterior

        proceso.siguiente_proceso = None
        proceso.proceso_anterior = None
        self.procesos.pop(idx)
        return True

    def limpiar(self) -> None:
        self.procesos = []
        self.productos = []
        self.cantidad_ingreso = 0
        self.tiempo_actual = 0
        self.pausada = False

    def get_proceso_inicial(self) -> Proceso | None:
        for p in self.procesos:
            if p.es_inicial:
                return p
        return None

    def get_proceso_final(self) -> Proceso | None:
        for p in self.procesos:
            if p.es_final:
                return p
        return None

    def cargar_productos(self, cantidad: int) -> None:
        cantidad = int(cantidad)
        if cantidad < 1:
            raise ValueError("La cantidad de productos debe ser >= 1")
        if not self.procesos:
            raise ValueError("La linea no tiene procesos")

        inicial = self.get_proceso_inicial()
        if inicial is None:
            raise ValueError("La linea no tiene un proceso inicial definido")
        if self.get_proceso_final() is None:
            raise ValueError("La linea no tiene un proceso final definido")

        self.cantidad_ingreso = cantidad
        self.productos = []
        for i in range(cantidad):
            producto = Producto(i + 1, self.tiempo_actual)
            self.productos.append(producto)
            inicial.recibir_producto(producto)

    def tick(self) -> None:
        if self.pausada:
            return
        self.tiempo_actual += 1
        # Recorrer en orden inverso para que un producto entregado de un
        # proceso al siguiente no se procese en el mismo ciclo.
        for proceso in reversed(self.procesos):
            proceso.tick(self.tiempo_actual)

    def correr(self, max_ciclos: int = 10000) -> None:
        ciclos = 0
        while not self.todos_finalizados() and ciclos < max_ciclos:
            if self.pausada:
                break
            self.tick()
            ciclos += 1

    def correr_hasta(self, t_objetivo: int) -> None:
        while self.tiempo_actual < t_objetivo and not self.todos_finalizados():
            if self.pausada:
                break
            self.tick()

    def pausar(self) -> None:
        self.pausada = True

    def reanudar(self) -> None:
        self.pausada = False

    def todos_finalizados(self) -> bool:
        if not self.productos:
            return False
        for p in self.productos:
            if not p.esta_finalizado():
                return False
        return True

    def reiniciar(self, cantidad: int | None = None) -> None:
        self.tiempo_actual = 0
        self.pausada = False
        for proceso in self.procesos:
            proceso.reiniciar()
        if cantidad is None:
            cantidad = max(1, self.cantidad_ingreso)
        self.cargar_productos(cantidad)

    def estado_completo_texto(self) -> str:
        lineas = []
        lineas.append(f"=== {self.nombre} | Ciclo T={self.tiempo_actual} ===")
        estado = "Pausada" if self.pausada else "En ejecucion"
        lineas.append(f"  Estado de la linea: {estado}")

        for proceso in self.procesos:
            lineas.append(f"  {proceso}")
            for tarea in proceso.tareas:
                lineas.append(f"    {tarea}")
                if tarea.producto_actual is not None:
                    lineas.append(
                        f"      Producto en proceso: Producto {tarea.producto_actual.id}"
                    )
                if tarea.contenido_esperando:
                    ids = [str(p.id) for p in tarea.contenido_esperando]
                    lineas.append(f"      Productos en cola: [{', '.join(ids)}]")

        if self.productos:
            total = len(self.productos)
            pendientes = 0
            en_proceso = 0
            finalizados = 0
            for p in self.productos:
                if p.estado == "en_espera":
                    pendientes += 1
                elif p.estado == "en_proceso":
                    en_proceso += 1
                elif p.estado == "finalizado":
                    finalizados += 1

            lineas.append("  ---")
            lineas.append(f"  Productos totales: {total}")
            lineas.append(f"  Pendientes de iniciar: {pendientes}")
            lineas.append(f"  En proceso: {en_proceso}")
            lineas.append(f"  Finalizados: {finalizados}/{total}")

        return "\n".join(lineas)

    def imprimir_estado(self) -> None:
        print(self.estado_completo_texto())

    def __str__(self):
        return (
            f"LineaProduccion {self.nombre} "
            f"({len(self.procesos)} procesos, T={self.tiempo_actual})"
        )
