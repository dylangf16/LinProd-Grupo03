from clase_producto import Producto


class LineaProduccion:
    def __init__(self, nombre="Linea"):
        self.nombre = nombre
        self.procesos = []
        self.productos = []  # productos inyectados a la línea
        self.cantidad_ingreso = 0
        self.tiempo_actual = 0
        self.pausada = False

    def agregar_proceso(self, proceso):
        """Agrega un proceso al final de la línea y lo encadena con el anterior.

        Valida que solo exista un proceso inicial y un proceso final.
        """
        if proceso.es_inicial and any(p.es_inicial for p in self.procesos):
            raise ValueError("Ya existe un proceso inicial en la línea")
        if proceso.es_final and any(p.es_final for p in self.procesos):
            raise ValueError("Ya existe un proceso final en la línea")
        if self.procesos:
            self.procesos[-1].conectar_siguiente(proceso)
        self.procesos.append(proceso)

    def eliminar_proceso(self, nombre):
        """Elimina un proceso por nombre y reconecta los vecinos."""
        proceso = next((p for p in self.procesos if p.nombre == nombre), None)
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

    def limpiar(self):
        """Vacía toda la línea (procesos y productos)."""
        self.procesos.clear()
        self.productos.clear()
        self.cantidad_ingreso = 0
        self.tiempo_actual = 0
        self.pausada = False

    def get_proceso_inicial(self):
        return next((p for p in self.procesos if p.es_inicial), None)

    def get_proceso_final(self):
        return next((p for p in self.procesos if p.es_final), None)

    def cargar_productos(self, cantidad):
        """Crea `cantidad` productos y los inyecta al proceso inicial."""
        cantidad = int(cantidad)
        if cantidad < 1:
            raise ValueError("La cantidad de productos debe ser >= 1")

        if not self.procesos:
            raise ValueError("La línea no tiene procesos")

        inicial = self.get_proceso_inicial()
        if inicial is None:
            raise ValueError("La línea no tiene un proceso inicial definido")
        if self.get_proceso_final() is None:
            raise ValueError("La línea no tiene un proceso final definido")

        self.cantidad_ingreso = cantidad
        self.productos = [Producto(i + 1, self.tiempo_actual) for i in range(cantidad)]
        for prod in self.productos:
            inicial.recibir_producto(prod)

    def tick(self):
        """Avanza un ciclo de tiempo en toda la línea."""
        if self.pausada:
            return
        self.tiempo_actual += 1
        # Recorrer en orden inverso para que un producto entregado de un
        # proceso al siguiente no se procese en el mismo ciclo.
        for proceso in reversed(self.procesos):
            proceso.tick(self.tiempo_actual)

    def correr(self, max_ciclos=10000):
        """Avanza la simulación hasta que todos los productos finalicen,
        se pause la línea, o se alcance `max_ciclos`.
        """
        ciclos = 0
        while not self.todos_finalizados() and ciclos < max_ciclos:
            if self.pausada:
                break
            self.tick()
            ciclos += 1

    def correr_hasta(self, t_objetivo):
        """Avanza la simulación hasta el tiempo `t_objetivo` (o hasta pausarse)."""
        while self.tiempo_actual < t_objetivo and not self.todos_finalizados():
            if self.pausada:
                break
            self.tick()

    def pausar(self):
        self.pausada = True

    def reanudar(self):
        self.pausada = False

    def todos_finalizados(self):
        """True si hay productos en la línea y todos están finalizados."""
        return bool(self.productos) and all(p.esta_finalizado() for p in self.productos)

    def reiniciar(self, cantidad=None):
        """Reinicia la simulación con los mismos procesos y tareas.

        Si `cantidad` es None, vuelve a usar la cantidad anterior.
        """
        self.tiempo_actual = 0
        self.pausada = False
        for proceso in self.procesos:
            proceso.reiniciar()
        cantidad = cantidad if cantidad is not None else max(1, self.cantidad_ingreso)
        self.cargar_productos(cantidad)

    def estado_completo_texto(self):
        """Devuelve un texto multilinea con el estado completo de la linea.

        Incluye: cada proceso, cada tarea (tiempo proceso, en proceso, en cola),
        producto siendo atendido, productos en cola, y el resumen global de
        productos pendientes / en proceso / finalizados.
        """
        lineas = []
        lineas.append(f"=== {self.nombre} | Ciclo T={self.tiempo_actual} ===")
        lineas.append(
            f"  Estado de la linea: {'Pausada' if self.pausada else 'En ejecucion'}"
        )

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
            pendientes = sum(1 for p in self.productos if p.estado == "en_espera")
            en_proceso = sum(1 for p in self.productos if p.estado == "en_proceso")
            finalizados = sum(1 for p in self.productos if p.estado == "finalizado")
            lineas.append("  ---")
            lineas.append(f"  Productos totales: {total}")
            lineas.append(f"  Pendientes de iniciar: {pendientes}")
            lineas.append(f"  En proceso: {en_proceso}")
            lineas.append(f"  Finalizados: {finalizados}/{total}")

        return "\n".join(lineas)

    def imprimir_estado(self):
        """Imprime el estado completo de la linea en el ciclo actual."""
        print(self.estado_completo_texto())

    def __str__(self):
        return (
            f"LineaProduccion {self.nombre} "
            f"({len(self.procesos)} procesos, T={self.tiempo_actual})"
        )

    def __repr__(self):
        return self.__str__()
