class Estadisticas:
    def __init__(self, linea):
        self.linea = linea

    @staticmethod
    def _es_tarea_entrada_inicial(proceso, indice_tarea, incluir_entrada_inicial):
        return (
            not incluir_entrada_inicial
            and getattr(proceso, "es_inicial", False)
            and indice_tarea == 0
        )

    def _productos_finalizados(self):
        return [
            producto
            for producto in self.linea.productos
            if producto.tiempo_salida is not None
        ]

    def cantidad_productos_procesados(self):
        return sum(1 for producto in self.linea.productos if producto.esta_finalizado())

    def tiempo_total_simulacion(self):
        return self.linea.tiempo_actual

    def estadisticas_por_proceso(self, incluir_entrada_inicial=False):
        resultados = []

        for proceso in self.linea.procesos:
            espera_total = 0
            for indice_tarea, tarea in enumerate(proceso.tareas):
                if self._es_tarea_entrada_inicial(
                    proceso, indice_tarea, incluir_entrada_inicial
                ):
                    continue
                espera_total += tarea.total_espera_acumulada()

            resultados.append(
                {
                    "proceso": proceso.nombre,
                    "num_tareas": len(proceso.tareas),
                    "espera_total": espera_total,
                }
            )

        return resultados

    def tarea_mayor_concentracion_espera(self, incluir_entrada_inicial=False):
        tarea_mayor = None
        mayor_veces = -1
        mayor_acumulado = -1

        for proceso in self.linea.procesos:
            for indice_tarea, tarea in enumerate(proceso.tareas):
                if self._es_tarea_entrada_inicial(
                    proceso, indice_tarea, incluir_entrada_inicial
                ):
                    continue

                veces = tarea.veces_con_espera()
                acumulado = tarea.total_espera_acumulada()

                if veces > mayor_veces or (
                    veces == mayor_veces and acumulado > mayor_acumulado
                ):
                    mayor_veces = veces
                    mayor_acumulado = acumulado
                    tarea_mayor = tarea

        if tarea_mayor is None:
            return "No disponible"

        return tarea_mayor.nombre

    def tiempo_primer_producto(self):
        finalizados = self._productos_finalizados()

        if not finalizados:
            return None

        return min(producto.tiempo_salida for producto in finalizados)

    def tiempo_ultimo_producto(self):
        finalizados = self._productos_finalizados()

        if not finalizados:
            return None

        return max(producto.tiempo_salida for producto in finalizados)

    def tiempo_promedio_finalizacion(self):
        finalizados = self._productos_finalizados()

        if not finalizados:
            return 0

        tiempos = [
            producto.tiempo_salida - producto.tiempo_ingreso for producto in finalizados
        ]

        return sum(tiempos) / len(tiempos)

    def tiempo_total_procesamiento(self):
        finalizados = self._productos_finalizados()

        if not finalizados:
            return 0

        return sum(
            producto.tiempo_salida - producto.tiempo_ingreso for producto in finalizados
        )

    def proceso_mayor_congestion(self, incluir_entrada_inicial=False):
        proceso_mayor = None
        mayor_espera = -1

        for proceso in self.linea.procesos:
            espera_total_proceso = 0

            for indice_tarea, tarea in enumerate(proceso.tareas):
                if self._es_tarea_entrada_inicial(
                    proceso, indice_tarea, incluir_entrada_inicial
                ):
                    continue
                espera_total_proceso += tarea.total_espera_acumulada()

            if espera_total_proceso > mayor_espera:
                mayor_espera = espera_total_proceso
                proceso_mayor = proceso

        if proceso_mayor is None:
            return "No disponible"

        return proceso_mayor.nombre

    def promedio_espera_tareas(self):
        total_espera = 0
        total_inicios = 0

        for proceso in self.linea.procesos:
            for tarea in proceso.tareas:
                total_espera += sum(tarea.historial_espera)
                total_inicios += tarea.total_inicios

        if total_inicios == 0:
            return 0

        return total_espera / total_inicios

    def proceso_y_tarea_mayor_espera(self, incluir_entrada_inicial=False):
        proceso_resultado = None
        tarea_resultado = None
        mayor_espera = -1

        for proceso in self.linea.procesos:
            for indice_tarea, tarea in enumerate(proceso.tareas):
                if self._es_tarea_entrada_inicial(
                    proceso, indice_tarea, incluir_entrada_inicial
                ):
                    continue

                espera = tarea.total_espera_acumulada()

                if espera > mayor_espera:
                    mayor_espera = espera
                    proceso_resultado = proceso
                    tarea_resultado = tarea

        if proceso_resultado is None or tarea_resultado is None:
            return "No disponible"

        return f"{proceso_resultado.nombre} - {tarea_resultado.nombre}"

    def mostrar_resumen(self):
        print()
        print("========== ESTADÍSTICAS ==========")

        print(
            f"Cantidad de productos procesados: {self.cantidad_productos_procesados()}"
        )
        print(f"Tiempo total de simulación: {self.tiempo_total_simulacion()} ciclos")

        print()
        print("Procesos:")
        for datos in self.estadisticas_por_proceso():
            print(
                f"- {datos['proceso']} | Tareas: {datos['num_tareas']} | "
                f"Espera acumulada: {datos['espera_total']} ciclos"
            )

        print()
        print(
            f"Tarea con mayor concentración de espera: {self.tarea_mayor_concentracion_espera()}"
        )

        print()
        print("----- REPORTE GENERAL DE LA LÍNEA -----")
        print(f"Primer producto finalizó en: T{self.tiempo_primer_producto()}")
        print(f"Último producto finalizó en: T{self.tiempo_ultimo_producto()}")
        print(
            f"Tiempo promedio de finalización: {self.tiempo_promedio_finalizacion():.2f} ciclos"
        )
        print(f"Proceso con mayor congestionamiento: {self.proceso_mayor_congestion()}")
        print(
            f"Tiempo promedio de espera para iniciar una tarea: {self.promedio_espera_tareas():.2f} ciclos"
        )
        print(
            f"Proceso y tarea con mayor tiempo de espera: {self.proceso_y_tarea_mayor_espera()}"
        )
        print(
            f"Tiempo total de procesamiento (suma de todos los productos): "
            f"{self.tiempo_total_procesamiento()} ciclos"
        )
        print("---------------------------------------")

        print("==================================")
