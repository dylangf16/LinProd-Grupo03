class Proceso:
    def __init__(self, nombre, tareas, es_inicial=False, es_final=False):
        self.nombre = nombre
        self.tareas = list(tareas)
        self.es_inicial = es_inicial
        self.es_final = es_final

        self.siguiente_proceso = None
        self.proceso_anterior = None

        for i in range(len(self.tareas)):
            tarea = self.tareas[i]
            tarea.proceso = self
            if i + 1 < len(self.tareas):
                tarea.siguiente_tarea = self.tareas[i + 1]
            else:
                tarea.siguiente_tarea = None

    def conectar_siguiente(self, otro_proceso):
        self.siguiente_proceso = otro_proceso
        otro_proceso.proceso_anterior = self

    def recibir_producto(self, producto):
        self.tareas[0].recibir_producto(producto)

    def entregar_siguiente(self, producto, tiempo_actual):
        if self.siguiente_proceso is not None:
            self.siguiente_proceso.recibir_producto(producto)
        else:
            producto.finalizar(tiempo_actual)

    def tick(self, tiempo_actual):
        for tarea in reversed(self.tareas):
            tarea.tick(tiempo_actual)

    def reiniciar(self):
        for tarea in self.tareas:
            tarea.reiniciar()

    def get_primera_tarea(self):
        if not self.tareas:
            return None
        return self.tareas[0]

    def get_ultima_tarea(self):
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
