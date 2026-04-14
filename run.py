"""
run.py — SnapIT
Lanzador unificado: arranca la API y abre el frontend en el navegador.

Uso:
    python run.py           → arranca todo
    python run.py --port 8080
    python run.py --no-browser   → solo la API, sin abrir el navegador
"""

import argparse
import subprocess
import sys
import time
import threading
import webbrowser
from pathlib import Path


def check_dependencies():
    """Verifica que las dependencias críticas están instaladas."""
    missing = []
    for pkg in ['fastapi', 'uvicorn', 'sqlmodel', 'PIL']:
        try:
            __import__(pkg if pkg != 'PIL' else 'PIL')
        except ImportError:
            missing.append(pkg if pkg != 'PIL' else 'pillow')

    if missing:
        print(f"\n⚠️  Faltan dependencias: {', '.join(missing)}")
        print("   Ejecuta: pip install -r requirements.txt\n")
        sys.exit(1)

    # Aviso sobre ultralytics (necesario para detección real)
    try:
        import ultralytics  # noqa
    except ImportError:
        print("⚠️  ultralytics no instalado — la detección YOLO no funcionará.")
        print("   Instala con: pip install ultralytics")
        print("   (La API arrancará igualmente)\n")


def open_browser_delayed(url: str, delay: float = 2.0):
    """Abre el navegador tras un breve delay para que la API esté lista."""
    def _open():
        time.sleep(delay)
        webbrowser.open(url)
    threading.Thread(target=_open, daemon=True).start()


def start_server(port: int, open_browser: bool):
    root = Path(__file__).parent
    frontend = root / "frontend" / "index.html"

    print("\n" + "═"*50)
    print("  🎯  SnapIT")
    print("═"*50)
    app_url = f"http://localhost:{port}/app"
    print(f"  App:      {app_url}")
    print(f"  API:      http://localhost:{port}")
    print(f"  Docs:     http://localhost:{port}/docs")
    print("═"*50)
    print("  Ctrl+C para detener\n")

    if open_browser:
        open_browser_delayed(app_url)

    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "api.main:app",
            "--reload",
            "--port", str(port),
            "--host", "0.0.0.0",
        ], cwd=root)
    except KeyboardInterrupt:
        print("\n\n  👋 SnapIT detenido.\n")


def main():
    parser = argparse.ArgumentParser(description="SnapIT — lanzador")
    parser.add_argument("--port",       type=int, default=8000, help="Puerto de la API (default: 8000)")
    parser.add_argument("--no-browser", action="store_true",    help="No abrir el navegador automáticamente")
    args = parser.parse_args()

    check_dependencies()
    start_server(args.port, not args.no_browser)


if __name__ == "__main__":
    main()
