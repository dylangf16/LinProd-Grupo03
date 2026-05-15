# LinProd
Proyecto 2 del curso: CE5507 – Modelación Hardware Software Orientado a Objetos

Simulador de línea de producción con procesos, tareas, productos, animación
en tiempo real y reporte estadístico final. Implementado 100% en Python con
Pygame para la interfaz gráfica.

## Requisitos previos

- Python 3.13.13 instalado ([descargar aquí](https://www.python.org/downloads/release/python-31313/))

### Verificar instalación de Python 3.13.13

**Windows:**
```powershell
py -3.13 --version
```

**macOS:**
```bash
python3.13 --version
```

La salida esperada es `Python 3.13.3`. Si el comando no se reconoce o muestra una versión diferente, descarga e instala Python 3.13.3 desde el enlace de arriba.

## Configuración del entorno virtual

### Windows

```powershell
# Crear el entorno virtual
py -3.13 -m venv .venv

# Activar el entorno virtual
.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
```

### macOS

```bash
# Crear el entorno virtual
python3.13 -m venv .venv

# Activar el entorno virtual
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

> Para desactivar el entorno virtual en cualquier plataforma, ejecutar `deactivate` en la consola donde está activado el venv.

## Ejecución

Con el entorno virtual activado y desde la raíz del repositorio:

```bash
python src/main.py
```

Esto abre la **ventana de configuración**. Allí puedes:

- Crear procesos con el botón **+ Añadir proceso**.
- Marcar un proceso como **inicial** o **final** dentro del modal de cada proceso (la GUI garantiza que solo exista uno de cada).
- Añadir tareas dentro de cada proceso, con su nombre y tiempo de ejecución en ciclos.
- Reordenar los procesos intermedios desde la tarjeta usando los chevrons `←` `→` (el inicial siempre queda primero y el final último).
- Guardar / cargar la configuración como JSON con los botones inferiores (o `Ctrl+S` / `Ctrl+L`).
- Pulsar **Iniciar simulación** para abrir el modal que pide la cantidad de productos.

En la **ventana de simulación**:

- **Iniciar / Pausar** controlan el avance por ciclos. Al pausar se imprime el estado completo de la línea en consola.
- **Tomar Foto** guarda en `src/interface/assets/capturas/` un `.png` con el panel y un `.txt` con el estado textual.
- **ReConfigurar** vuelve a la ventana de configuración manteniendo el flujo abierto.
- **Finalizar** corre la simulación al final y abre el reporte.

Atajos de teclado en la simulación: `Espacio` alterna iniciar/pausar, `P` pausa, `S` toma foto, `Esc` cierra la ventana.

## Pruebas funcionales

Existe una suite manual de pruebas que valida el modelo (5 configuraciones distintas, validaciones de inicial/final único, pausa/reinicio):

```bash
python src/logic/test_linea_produccion.py
```
