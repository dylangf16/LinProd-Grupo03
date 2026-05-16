from __future__ import annotations

from clase_linea_produccion import LineaProduccion


class Estadisticas:
    def __init__(self, linea: LineaProduccion):
        self.linea: LineaProduccion = linea

    def cantidad_productos_procesados(self):
        cantidad = 0
        for producto in self.linea.productos:
            if producto.esta_finalizado():
                cantidad += 1
        return cantidad

    def tiempo_total_simulacion(self):
        return self.linea.tiempo_actual

    def estadisticas_por_proceso(self):
        resultados = []
        for proceso in self.linea.procesos:
            espera_total = 0
            for i, tarea in enumerate(proceso.tareas):
                # No contamos la primera tarea del proceso inicial: ahi se
                # acumula la cola de entrada de todos los productos.
                if proceso.es_inicial and i == 0:
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

    def tarea_mayor_concentracion_espera(self):
        tarea_mayor = None
        mayor_veces = -1
        mayor_acumulado = -1

        for proceso in self.linea.procesos:
            for i, tarea in enumerate(proceso.tareas):
                if proceso.es_inicial and i == 0:
                    continue

                veces = tarea.veces_con_espera()
                acumulado = tarea.total_espera_acumulada()

                if veces > mayor_veces:
                    mayor_veces = veces
                    mayor_acumulado = acumulado
                    tarea_mayor = tarea
                elif veces == mayor_veces and acumulado > mayor_acumulado:
                    mayor_acumulado = acumulado
                    tarea_mayor = tarea

        if tarea_mayor is None:
            return "No disponible"
        return tarea_mayor.nombre

    def tiempo_primer_producto(self):
        tiempos = []
        for producto in self.linea.productos:
            if producto.tiempo_salida is not None:
                tiempos.append(producto.tiempo_salida)
        if not tiempos:
            return None
        return min(tiempos)

    def tiempo_ultimo_producto(self):
        tiempos = []
        for producto in self.linea.productos:
            if producto.tiempo_salida is not None:
                tiempos.append(producto.tiempo_salida)
        if not tiempos:
            return None
        return max(tiempos)

    def tiempo_promedio_finalizacion(self):
        tiempos = []
        for producto in self.linea.productos:
            if producto.tiempo_salida is not None:
                tiempos.append(producto.tiempo_salida - producto.tiempo_ingreso)
        if not tiempos:
            return 0
        return sum(tiempos) / len(tiempos)

    def tiempo_total_procesamiento(self):
        total = 0
        for producto in self.linea.productos:
            if producto.tiempo_salida is not None:
                total += producto.tiempo_salida - producto.tiempo_ingreso
        return total

    def proceso_mayor_congestion(self):
        proceso_mayor = None
        mayor_espera = -1

        for proceso in self.linea.procesos:
            espera_total_proceso = 0
            for i, tarea in enumerate(proceso.tareas):
                if proceso.es_inicial and i == 0:
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

    def utilizacion_promedio_tareas(self):
        utilizaciones = []
        for proceso in self.linea.procesos:
            for i, tarea in enumerate(proceso.tareas):
                if proceso.es_inicial and i == 0:
                    continue
                if not tarea.historial_ocupacion:
                    continue
                utilizaciones.append(tarea.utilizacion())

        if not utilizaciones:
            return 0.0
        return sum(utilizaciones) / len(utilizaciones)

    def proceso_y_tarea_mayor_espera(self):
        proceso_resultado = None
        tarea_resultado = None
        mayor_espera = -1

        for proceso in self.linea.procesos:
            for i, tarea in enumerate(proceso.tareas):
                if proceso.es_inicial and i == 0:
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
        print("========== ESTADISTICAS ==========")
        print(
            f"Cantidad de productos procesados: {self.cantidad_productos_procesados()}"
        )
        print(f"Tiempo total de simulacion: {self.tiempo_total_simulacion()} ciclos")

        print()
        print("Procesos:")
        for datos in self.estadisticas_por_proceso():
            print(
                f"- {datos['proceso']} | Tareas: {datos['num_tareas']} | "
                f"Espera acumulada: {datos['espera_total']} ciclos"
            )

        print()
        print(
            f"Tarea con mayor concentracion de espera: {self.tarea_mayor_concentracion_espera()}"
        )

        print()
        print("----- REPORTE GENERAL DE LA LINEA -----")
        print(f"Primer producto finalizo en: T{self.tiempo_primer_producto()}")
        print(f"Ultimo producto finalizo en: T{self.tiempo_ultimo_producto()}")
        print(
            f"Tiempo promedio de finalizacion: {self.tiempo_promedio_finalizacion():.2f} ciclos"
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
        print(
            f"Utilizacion promedio de tareas (estadistica del grupo): "
            f"{self.utilizacion_promedio_tareas() * 100:.1f}%"
        )
        print("---------------------------------------")
        print("==================================")
