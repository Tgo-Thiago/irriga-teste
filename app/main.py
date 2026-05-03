from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import pivo
from routes import auth

app = FastAPI(
    title="API de Dimensionamento de Pivô",
    version="1.0.0"
)

# CORS — aceita qualquer origem (adequado para beta)
# Nota: allow_credentials=True é incompatível com allow_origins=["*"]
# Por isso listamos explicitamente os domínios conhecidos + wildcard via regex
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://irrigatech-frontend.vercel.app",
        "https://irrigatech-frontend-git-main-thiagos-projects-6cd47749.vercel.app",
        "https://irrigatech.agr.br",
        "https://www.irrigatech.agr.br",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pivo.router, prefix="/api")
app.include_router(auth.router, prefix="/auth")


@app.get("/")
def root():
    return {"status": "ok", "service": "Irrigatech API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}
