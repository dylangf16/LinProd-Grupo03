class Tarea:
    def __init__(self, nombre, tiempo_proceso):
        self.nombre = nombre
        self.tiempo_proceso = tiempo_proceso  # duración en ticks

        # Estado de procesamiento
        self.esta_procesando = False
        self.producto_actual = None
        self.ticks_restantes = 0

        # Cola FIFO de productos esperando
        self.contenido_esperando = []

        # Enlaces hacia el resto de la línea
        self.siguiente_tarea = None
        self.proceso = None  # asignado por Proceso al construirse

        # historial para estadística
        self.historial_espera = []

    @property
    def tiempo_procesamiento(self):
        """Alias para cumplir requerimientos sin romper compatibilidad."""
        return self.tiempo_proceso

    @tiempo_procesamiento.setter
    def tiempo_procesamiento(self, valor):
        self.tiempo_proceso = valor

    @property
    def estado_ocupado(self):
        """Alias semántico del estado de procesamiento de la tarea."""
        return self.esta_procesando

    @estado_ocupado.setter
    def estado_ocupado(self, valor):
        self.esta_procesando = valor

    def recibir_producto(self, producto):
        """Recibe un producto: si está libre lo procesa, si no lo encola (FIFO)."""
        if not self.esta_procesando:
            self._iniciar_procesamiento(producto)
        else:
            self.contenido_esperando.append(producto)

    def _iniciar_procesamiento(self, producto):
        self.producto_actual = producto
        self.esta_procesando = True
        self.ticks_restantes = self.tiempo_proceso
        producto.estado = "en_proceso"

    def tick(self, tiempo_actual):
        """Avanza un ciclo de tiempo. Si termina con un producto lo entrega
        a la siguiente tarea o, si es la última del proceso, al proceso. Tras
        quedar libre, atiende al siguiente en cola dentro del mismo tick.
        """
        self.historial_espera.append(self.cantidad_en_espera())
        if self.esta_procesando:
            self.ticks_restantes -= 1
            if self.ticks_restantes == 0:
                producto = self.producto_actual
                self.producto_actual = None
                self.esta_procesando = False

                if self.siguiente_tarea is not None:
                    self.siguiente_tarea.recibir_producto(producto)
                elif self.proceso is not None:
                    self.proceso.entregar_siguiente(producto, tiempo_actual)

        if not self.esta_procesando and self.contenido_esperando:
            siguiente = self.contenido_esperando.pop(0)
            self._iniciar_procesamiento(siguiente)

    def esta_libre(self):
        return not self.esta_procesando

    def cantidad_en_espera(self):
        return len(self.contenido_esperando)

    def veces_con_espera(self):
        return sum(1 for ce in self.historial_espera if ce > 0)

    def total_espera_acumulada(self):
        return sum(self.historial_espera)

    def __str__(self):
        ep = "S" if self.esta_procesando else "N"
        return (
            f"Tarea {self.nombre} | "
            f"TP={self.tiempo_proceso}, EP={ep}, CE={self.cantidad_en_espera()}"
        )

    def __repr__(self):
        return self.__str__()

    def __getattr__(self, nombre_atributo):
        """Delega atributos faltantes de Tarea a su Proceso padre."""
        proceso_padre = self.__dict__.get("proceso")
        if proceso_padre is not None:
            try:
                return getattr(proceso_padre, nombre_atributo)
            except AttributeError:
                pass

        raise AttributeError(
            f"'{self.__class__.__name__}' no tiene el atributo '{nombre_atributo}'"
        )
