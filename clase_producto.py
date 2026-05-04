class Producto:
    def __init__(self, id, tiempo_ingreso):
        self.id = id
        self.tiempo_ingreso = tiempo_ingreso
        self.tiempo_salida = None
        self.estado = "en_espera"  # en_espera | en_proceso | finalizado

    def finalizar(self, tiempo_salida):
        self.tiempo_salida = tiempo_salida
        self.estado = "finalizado"

    def __str__(self):
        return (
            f"Producto {self.id} "
            f"(Ingreso: {self.tiempo_ingreso}, "
            f"Salida: {self.tiempo_salida}, "
            f"Estado: {self.estado})"
        )

    def __repr__(self):
        return self.__str__()
