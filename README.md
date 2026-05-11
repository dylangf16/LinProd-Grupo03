# LinProd
Proyecto 2 del curso: CE5507 – Modelación Hardware Software Orientado a Objetos

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
