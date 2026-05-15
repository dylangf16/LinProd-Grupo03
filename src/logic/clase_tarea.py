class Tarea:
    def __init__(self, nombre, tiempo_proceso):
        self.nombre = nombre
        self.tiempo_proceso = int(tiempo_proceso)

        self.esta_procesando = False
        self.producto_actual = None
        self.ticks_restantes = 0

        self.contenido_esperando = []

        self.siguiente_tarea = None
        self.proceso = None

        self.historial_espera = []
        self.historial_ocupacion = []
        self.total_inicios = 0

    def recibir_producto(self, producto):
        if not self.esta_procesando:
            self.iniciar_procesamiento(producto)
        else:
            self.contenido_esperando.append(producto)

    def iniciar_procesamiento(self, producto):
        self.producto_actual = producto
        self.esta_procesando = True
        self.ticks_restantes = self.tiempo_proceso
        self.total_inicios += 1
        producto.iniciar_proceso()

    def tick(self, tiempo_actual):
        self.historial_espera.append(len(self.contenido_esperando))
        self.historial_ocupacion.append(self.esta_procesando)

        if self.esta_procesando:
            self.ticks_restantes -= 1
            if self.ticks_restantes <= 0:
                producto = self.producto_actual
                self.producto_actual = None
                self.esta_procesando = False

                if self.siguiente_tarea is not None:
                    self.siguiente_tarea.recibir_producto(producto)
                elif self.proceso is not None:
                    self.proceso.entregar_siguiente(producto, tiempo_actual)

        if not self.esta_procesando and self.contenido_esperando:
            siguiente = self.contenido_esperando.pop(0)
            self.iniciar_procesamiento(siguiente)

    def esta_libre(self):
        return not self.esta_procesando

    def cantidad_en_espera(self):
        return len(self.contenido_esperando)

    def veces_con_espera(self):
        veces = 0
        for cantidad in self.historial_espera:
            if cantidad > 0:
                veces += 1
        return veces

    def total_espera_acumulada(self):
        return sum(self.historial_espera)

    def ticks_ocupada(self):
        ticks = 0
        for ocupada in self.historial_ocupacion:
            if ocupada:
                ticks += 1
        return ticks

    def utilizacion(self):
        if not self.historial_ocupacion:
            return 0.0
        return self.ticks_ocupada() / len(self.historial_ocupacion)

    def reiniciar(self):
        self.esta_procesando = False
        self.producto_actual = None
        self.ticks_restantes = 0
        self.contenido_esperando = []
        self.historial_espera = []
        self.historial_ocupacion = []
        self.total_inicios = 0

    def __str__(self):
        en_proceso = "Si" if self.esta_procesando else "No"
        return (
            f"Tarea {self.nombre} | "
            f"Tiempo proceso={self.tiempo_proceso}, "
            f"En proceso={en_proceso}, "
            f"En cola={len(self.contenido_esperando)}"
        )
