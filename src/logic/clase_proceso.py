class Proceso:
    """Proceso de la línea que agrupa tareas por composición.

    Nota de diseño: `Tarea` no hereda de `Proceso`. Cada tarea mantiene una
    referencia a su proceso padre (`tarea.proceso`) para modelar una relación
    todo-parte simple y clara para esta simulación.
    """

    def __init__(self, nombre, tareas, es_inicial=False, es_final=False):
        """Crea un proceso y encadena sus tareas en el orden recibido."""
        nombre = str(nombre).strip()
        if not nombre:
            raise ValueError("El nombre del proceso no puede estar vacio")

        self.nombre = nombre
        self.tareas = list(tareas)
        if not self.tareas:
            raise ValueError("Cada proceso debe tener al menos una tarea")

        self.es_inicial = bool(es_inicial)
        self.es_final = bool(es_final)

        # Enlaces de la línea de producción
        self.siguiente_proceso = None
        self.proceso_anterior = None

        for i, tarea in enumerate(self.tareas):
            tarea.proceso = self
            tarea.siguiente_tarea = (
                self.tareas[i + 1] if i + 1 < len(self.tareas) else None
            )

    @property
    def nombre_proceso(self):
        """Alias de compatibilidad para consumidores existentes."""
        return self.nombre

    def conectar_siguiente(self, otro_proceso):
        """Enlaza este proceso con el siguiente, de forma bidireccional."""
        if otro_proceso is None:
            raise ValueError("El proceso siguiente no puede ser None")
        if otro_proceso is self:
            raise ValueError("Un proceso no puede conectarse consigo mismo")

        self.siguiente_proceso = otro_proceso
        otro_proceso.proceso_anterior = self

    def recibir_producto(self, producto):
        """Recibe un producto y lo envía a la primera tarea del proceso."""
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

    def reiniciar(self):
        """Reinicia el estado interno de todas sus tareas."""
        for tarea in self.tareas:
            tarea.reiniciar()

    def get_primera_tarea(self):
        """Retorna la primera tarea del proceso, o None si no hay tareas."""
        return self.tareas[0] if self.tareas else None

    def get_ultima_tarea(self):
        """Retorna la última tarea del proceso, o None si no hay tareas."""
        return self.tareas[-1] if self.tareas else None

    def __str__(self):
        """Devuelve una representación textual breve del proceso."""
        marcas = []
        if self.es_inicial:
            marcas.append("INICIAL")
        if self.es_final:
            marcas.append("FINAL")
        marca = f" [{', '.join(marcas)}]" if marcas else ""
        return f"Proceso {self.nombre}{marca} ({len(self.tareas)} tareas)"

    def __repr__(self):
        return self.__str__()
