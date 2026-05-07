import sys
from pathlib import Path

root = Path(__file__).parent.parent
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "src" / "logic"))

from src.interface.config_window import ConfigWindow


def main():
    ventana = ConfigWindow()
    linea = ventana.run()
    if linea is not None:
        print("=" * 58)
        print("LINEA LISTA para el modulo de simulacion.")
        print("=" * 58)
        linea.imprimir_estado()
    else:
        print("Configuracion cancelada.")
    return linea


if __name__ == "__main__":
    main()
