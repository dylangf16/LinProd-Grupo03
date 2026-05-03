class Proceso:
    def __init__(self, nombre, tareas):
        self.nombre = nombre
        self.tareas = tareas  # lista ordenada de Tarea
        self.siguienteProceso = None

        self.tiempoInicio = None
        self.tiempoFin = None
