class Producto:
    def __init__(self, id, tiempoIngreso):
        self.id = id
        self.tiempoIngreso = tiempoIngreso
        self.tiempoSalida = None
        self.historial = []  # [(nombreProceso, nombreTarea, tiempo)]
        self.estado = "en espera"

    def registrar_evento(self, proceso, tarea, tiempo):
        self.historial.append((proceso, tarea, tiempo))

    def finalizar(self, tiempoSalida):
        self.tiempoSalida = tiempoSalida
        self.estado = "finalizado"

    def duracion_total(self):
        if self.tiempoSalida is not None:
            return self.tiempoSalida - self.tiempoIngreso
        return None

    def __str__(self):
        return f"Producto {self.id} (Ingreso: {self.tiempoIngreso}, Salida: {self.tiempoSalida})"
