class Proceso:
    def __init__(self, nombre, tareas, es_inicial=False, es_final=False):
        self.nombre = nombre
        self.nombre_proceso = nombre
        self.tareas = tareas
        self.es_inicial = es_inicial
        self.es_final = es_final

        # Enlaces de la línea de producción
        self.siguiente_proceso = None
        self.proceso_anterior = None

        # Conectar cada tarea con el proceso y encadenarlas en orden
        for i, tarea in enumerate(self.tareas):
            tarea.proceso = self
            if i + 1 < len(self.tareas):
                tarea.siguiente_tarea = self.tareas[i + 1]
            else:
                tarea.siguiente_tarea = None

    def conectar_siguiente(self, otro_proceso):
        """Enlaza este proceso con el siguiente, de forma bidireccional."""
        self.siguiente_proceso = otro_proceso
        otro_proceso.proceso_anterior = self

    def recibir_producto(self, producto):
        """Recibe un producto y lo envía a la primera tarea del proceso."""
        if not self.tareas:
            if self.siguiente_proceso is not None:
                self.siguiente_proceso.recibir_producto(producto)
            return
        self.tareas[0].recibir_producto(producto)

    def entregar_siguiente(self, producto, tiempo_actual):
        """Llamado por la última tarea cuando termina un producto.

        Si hay un proceso siguiente, lo entrega; si este es el proceso final,
        marca el producto como finalizado.
        """
        if self.siguiente_proceso is not None:
            self.siguiente_proceso.recibir_producto(producto)
        else:
            producto.finalizar(tiempo_actual)

    def tick(self, tiempo_actual):
        """Avanza un ciclo en todas las tareas en orden inverso, para que un
        producto entregado dentro del ciclo no se procese en el mismo ciclo.
        """
        for tarea in reversed(self.tareas):
            tarea.tick(tiempo_actual)

    def get_primera_tarea(self):
        return self.tareas[0] if self.tareas else None

    def get_ultima_tarea(self):
        return self.tareas[-1] if self.tareas else None

    def __str__(self):
        marcas = []
        if self.es_inicial:
            marcas.append("INICIAL")
        if self.es_final:
            marcas.append("FINAL")
        marca = f" [{', '.join(marcas)}]" if marcas else ""
        return f"Proceso {self.nombre}{marca} ({len(self.tareas)} tareas)"

    def __repr__(self):
        return self.__str__()
