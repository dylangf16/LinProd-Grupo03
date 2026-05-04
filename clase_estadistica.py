class Estadisticas:
    def __init__(self, linea):
        self.linea = linea

    def cantidad_productos_procesados(self):
        return sum(
            1 for producto in self.linea.productos if producto.estado == "finalizado"
        )

    def tiempo_total_simulacion(self):
        return self.linea.tiempo_actual

    def estadisticas_por_proceso(self):
        resultados = []

        for proceso in self.linea.procesos:
            productos_finalizados = [
                producto
                for producto in self.linea.productos
                if producto.tiempo_salida is not None
            ]

            if productos_finalizados:
                inicio = min(
                    producto.tiempo_ingreso for producto in productos_finalizados
                )
                fin = max(producto.tiempo_salida for producto in productos_finalizados)
                duracion = fin - inicio
            else:
                inicio = None
                fin = None
                duracion = None

            resultados.append(
                {
                    "proceso": proceso.nombre,
                    "inicio": inicio,
                    "fin": fin,
                    "duracion": duracion,
                }
            )

        return resultados

    def tarea_mayor_concentracion_espera(self):
        tarea_mayor = None
        mayor_cantidad = -1
        mayor_acumulado = -1

        for proceso in self.linea.procesos:
            for tarea in proceso.tareas:
                veces = (
                    tarea.veces_con_espera()
                    if hasattr(tarea, "veces_con_espera")
                    else 0
                )
                acumulado = (
                    tarea.total_espera_acumulada()
                    if hasattr(tarea, "total_espera_acumulada")
                    else 0
                )

                if veces > mayor_cantidad or (
                    veces == mayor_cantidad and acumulado > mayor_acumulado
                ):
                    mayor_cantidad = veces
                    mayor_acumulado = acumulado
                    tarea_mayor = tarea

        if tarea_mayor is None:
            return "No disponible"

        return tarea_mayor.nombre

    # -------- NUEVAS ESTADÍSTICAS DE TODA LA LÍNEA --------

    def tiempo_primer_producto(self):
        finalizados = [p for p in self.linea.productos if p.tiempo_salida is not None]

        if not finalizados:
            return None

        return min(p.tiempo_salida for p in finalizados)

    def tiempo_ultimo_producto(self):
        finalizados = [p for p in self.linea.productos if p.tiempo_salida is not None]

        if not finalizados:
            return None

        return max(p.tiempo_salida for p in finalizados)

    def tiempo_promedio_finalizacion(self):
        finalizados = [p for p in self.linea.productos if p.tiempo_salida is not None]

        if not finalizados:
            return 0

        tiempos = [p.tiempo_salida - p.tiempo_ingreso for p in finalizados]

        return sum(tiempos) / len(tiempos)

    def proceso_mayor_congestion(self):
        proceso_mayor = None
        mayor_espera = -1

        for proceso in self.linea.procesos:
            espera_proceso = 0

            for tarea in proceso.tareas:
                if hasattr(tarea, "total_espera_acumulada"):
                    espera_proceso += tarea.total_espera_acumulada()

            if espera_proceso > mayor_espera:
                mayor_espera = espera_proceso
                proceso_mayor = proceso

        if proceso_mayor is None:
            return "No disponible"

        return proceso_mayor.nombre

    def promedio_espera_tareas(self):
        tareas = [tarea for proceso in self.linea.procesos for tarea in proceso.tareas]

        if not tareas:
            return 0

        total_espera = 0
        total_registros = 0

        for tarea in tareas:
            if hasattr(tarea, "historial_espera"):
                total_espera += sum(tarea.historial_espera)
                total_registros += len(tarea.historial_espera)

        if total_registros == 0:
            return 0

        return total_espera / total_registros

    def proceso_y_tarea_mayor_espera(self):
        proceso_resultado = None
        tarea_resultado = None
        mayor_espera = -1

        for proceso in self.linea.procesos:
            for tarea in proceso.tareas:
                espera = (
                    tarea.total_espera_acumulada()
                    if hasattr(tarea, "total_espera_acumulada")
                    else 0
                )

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
        print(f"Tiempo total de simulación: {self.tiempo_total_simulacion()} segundos")
        print()

        print("Procesos:")
        for datos in self.estadisticas_por_proceso():
            print(
                f"- {datos['proceso']} inició en T{datos['inicio']}, "
                f"finalizó en T{datos['fin']} "
                f"y duró {datos['duracion']} segundos."
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
            f"Tiempo promedio de finalización: {self.tiempo_promedio_finalizacion():.2f} segundos"
        )
        print(f"Proceso con mayor congestionamiento: {self.proceso_mayor_congestion()}")
        print(f"Promedio de espera en tareas: {self.promedio_espera_tareas():.2f}")
        print(
            f"Proceso y tarea con mayor espera: {self.proceso_y_tarea_mayor_espera()}"
        )
        print("---------------------------------------")

        print("==================================")
