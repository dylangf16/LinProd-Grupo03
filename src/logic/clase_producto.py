class Producto:
    EN_ESPERA = "en_espera"
    EN_PROCESO = "en_proceso"
    FINALIZADO = "finalizado"

    def __init__(self, id, tiempo_ingreso):
        self.id = id
        self.tiempo_ingreso = tiempo_ingreso
        self.tiempo_salida = None
        self.estado = self.EN_ESPERA

    def iniciar_proceso(self):
        self.estado = self.EN_PROCESO

    def finalizar(self, tiempo_salida):
        self.tiempo_salida = tiempo_salida
        self.estado = self.FINALIZADO

    def esta_finalizado(self):
        return self.estado == self.FINALIZADO

    def __str__(self):
        return (
            f"Producto {self.id} "
            f"(Ingreso: {self.tiempo_ingreso}, "
            f"Salida: {self.tiempo_salida}, "
            f"Estado: {self.estado})"
        )

    def __repr__(self):
        return self.__str__()
