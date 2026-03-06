import os
import sys

# Ruta absoluta al proyecto (útil en cPanel para evitar problemas de imports)
sys.path.insert(0, os.path.dirname(__file__))

# Función obligatoria para Phusion Passenger (cPanel)
def application(environ, start_response):
    """
    Lazy Loading: 
    Importamos a2wsgi y main DENTRO de la función.
    Si las dependencias (como fastapi, a2wsgi) aún no están instaladas (ej. durante el setup inicial de cPanel),
    el script no "crasheará" al arrancar el contenedor WSGI y nos dejará instalar las dependencias tranquilamente.
    """
    from main import app
    from a2wsgi import ASGIMiddleware
    
    # Convertimos la app ASGI (FastAPI) a WSGI para que Passenger de cPanel la entienda
    wsgi_app = ASGIMiddleware(app)
    
    return wsgi_app(environ, start_response)
