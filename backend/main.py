from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback
import models
from database import engine
from routers import auth, projects, threads

# Esto le dice a SQLAlchemy que cree las tablas en MySQL basadas en tus modelos
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dev Network API", description="API REST para red social de programadores")

# Registrar Routers
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(threads.router)

# --- REGLA ESTRICTA DE CPANEL: CORS y Manejador 500 ---
origins = [
    "http://localhost:5000",
    "https://localhost:5001",
    "https://devnest.rsanjur.com", # Dominio de producción
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def debug_exception_handler(request, exc):
    """El 'Error Hunter' obligatorio para cPanel para evitar perder la cabecera CORS en 500s"""
    origin = request.headers.get("origin")
    allow_origin = origin if origin in origins else origins[0]
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "trace": traceback.format_exc()},
        headers={
            "Access-Control-Allow-Origin": allow_origin,
            "Access-Control-Allow-Credentials": "true"
        }
    )

@app.get("/")
def read_root():
    return {"mensaje": "¡El backend está funcionando correctamente!"}
