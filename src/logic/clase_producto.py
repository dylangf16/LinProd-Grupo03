class Producto:
    """Entidad que fluye por la línea de producción."""

    EN_ESPERA = "en_espera"
    EN_PROCESO = "en_proceso"
    FINALIZADO = "finalizado"

    def __init__(self, id, tiempo_ingreso):
        """Inicializa identificador y tiempo de ingreso al sistema."""
        self.id = id
        self.tiempo_ingreso = tiempo_ingreso
        self.tiempo_salida = None
        self.estado = self.EN_ESPERA

    def iniciar_proceso(self):
        """Marca el producto como en proceso."""
        self.estado = self.EN_PROCESO

    def finalizar(self, tiempo_salida):
        """Marca el producto como finalizado y guarda su tiempo de salida."""
        self.tiempo_salida = tiempo_salida
        self.estado = self.FINALIZADO

    def esta_finalizado(self):
        """Retorna True si el producto ya terminó su recorrido."""
        return self.estado == self.FINALIZADO

    def __str__(self):
        """Devuelve una representación textual breve del producto."""
        return (
            f"Producto {self.id} "
            f"(Ingreso: {self.tiempo_ingreso}, "
            f"Salida: {self.tiempo_salida}, "
            f"Estado: {self.estado})"
        )

    def __repr__(self):
        return self.__str__()
