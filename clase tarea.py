class Tarea:
    def __init__(self, nombre, tiempoProceso):
        self.nombre = nombre
        self.tiempoProceso = tiempoProceso  # duración en ticks
        self.estaProcesando = False  # indica si está ocupada
        self.contenidoEsperando = []  # lista de productos esperando
        self.productoActual = None  # producto en proceso
        self.ticksRestantes = 0  # tiempo que falta para terminar
        self.siguienteTarea = None  # referencia a la siguiente tarea

    def recibirProducto(self, producto):
        """Recibe un producto: si está libre lo procesa, si no lo encola."""
        if not self.estaProcesando:
            self.productoActual = producto
            self.estaProcesando = True
            self.ticksRestantes = self.tiempoProceso
        else:
            self.contenidoEsperando.append(producto)

    def tick(self, tiempoActual):
        """Avanza un ciclo de tiempo en la tarea."""
        if self.estaProcesando:
            self.ticksRestantes -= 1
            if self.ticksRestantes == 0:
                # Producto terminó en esta tarea
                producto = self.productoActual
                self.productoActual = None
                self.estaProcesando = False

                # Pasar al siguiente paso
                if self.siguienteTarea:
                    self.siguienteTarea.recibirProducto(producto)
        else:
            # Si está libre y hay productos esperando, toma el primero
            if self.contenidoEsperando:
                siguiente = self.contenidoEsperando.pop(0)  # saca el primero
                self.recibirProducto(siguiente)

    def estaLibre(self):
        """Devuelve True si la tarea no está procesando nada."""
        return not self.estaProcesando

    def __str__(self):
        estado = "ocupada" if self.estaProcesando else "libre"
        return f"Tarea {self.nombre} ({estado}, cola={len(self.contenidoEsperando)})"
