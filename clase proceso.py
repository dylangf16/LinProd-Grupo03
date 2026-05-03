class Proceso:
    def __init__(self, nombre, tareas):
        self.nombre = nombre
        self.tareas = tareas 
        
        # Conectar las tareas en orden
        for i in range(len(self.tareas) - 1):
            self.tareas[i].siguienteTarea = self.tareas[i + 1]
        
        self.siguienteProceso = None
        self.tiempoInicio = None
        self.tiempoFin = None

    def tick(self):
        """Avanza un ciclo de tiempo en todas las tareas del proceso."""
        tiempoActual = None
        for tarea in self.tareas:
            tarea.tick(tiempoActual)

    def recibirProducto(self, producto):
        """Recibe un producto y lo envía a la primera tarea."""
        if self.tareas:
            # Registrar el tiempo de inicio del proceso
            if self.tiempoInicio is None:
                self.tiempoInicio = producto.tiempoIngreso
            
            # Enviar producto a la primera tarea
            self.getPrimeraTarea().recibirProducto(producto)
        else:
            # Si no hay tareas, pasa al siguiente proceso
            if self.siguienteProceso:
                self.siguienteProceso.recibirProducto(producto)

    def getPrimeraTarea(self):
        """Devuelve la primera tarea del proceso."""
        if self.tareas:
            return self.tareas[0]
        return None

    def getUltimaTarea(self):
        """Devuelve la última tarea del proceso."""
        if self.tareas:
            return self.tareas[-1]
        return None
