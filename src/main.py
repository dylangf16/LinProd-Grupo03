import sys
from pathlib import Path

root = Path(__file__).parent.parent
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "src" / "logic"))

from src.interface.config_window import ConfigWindow
from src.interface.simulation import SimulationWindow


def main():
    ventana = ConfigWindow()
    linea = ventana.run()
    if linea is not None:
        print("=" * 58)
        print("LINEA LISTA para el modulo de simulacion.")
        print("=" * 58)
        simulador = SimulationWindow(
            linea,
            cantidad_productos=max(1, linea.cantidad_ingreso or 1),
        )
        simulador.run()
    else:
        print("Configuracion cancelada.")
    return linea


if __name__ == "__main__":
    main()
