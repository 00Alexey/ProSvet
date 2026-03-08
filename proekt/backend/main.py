import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

API_KEY = os.getenv("API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")


from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from proekt.backend.database import Base, engine
from proekt.routers import comments, files, ratings, users

print("APP START")
# Получить директорию проекта

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = exc.errors() or []
    message = "Validation error"
    if errors:
        message = "; ".join([e.get("msg", str(e)) for e in errors])
    return JSONResponse(status_code=422, content={"detail": message})


app.include_router(files.router)
app.include_router(comments.router)
app.include_router(ratings.router)

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === DATABASE ===

Base.metadata.create_all(bind=engine)

# === API ROUTERS ===
app.include_router(users.router)
app.include_router(users.users_router)


app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR / "static")),
    name="static",
)


@app.get("/")
def index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/index")
def index_route():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/login")
def login():
    return FileResponse(str(FRONTEND_DIR / "login.html"))


@app.get("/register")
def register():
    return FileResponse(str(FRONTEND_DIR / "register.html"))


@app.get("/notebook")
def notebook():
    return FileResponse(str(FRONTEND_DIR / "notebook.html"))


@app.get("/public")
def public():
    return FileResponse(str(FRONTEND_DIR / "public.html"))


@app.get("/folder")
def folder_page():
    return FileResponse(str(FRONTEND_DIR / "folder.html"))


@app.get("/viewer.html")
def viewer_html():
    return FileResponse(str(FRONTEND_DIR / "viewer.html"))


# uvicorn proekt.backend.main:app --reload


@app.get("/folder.html")
def folder_html():
    return FileResponse(str(FRONTEND_DIR / "folder.html"))


@app.get("/document-reader")
def document_reader():
    return FileResponse(str(FRONTEND_DIR / "document-reader.html"))


@app.get("/document-reader.html")
def document_reader_html():
    return FileResponse(str(FRONTEND_DIR / "document-reader.html"))


@app.get("/folder/{folder_id}")
def folder_page_by_id(folder_id: str):
    return FileResponse(str(FRONTEND_DIR / "folder.html"))


@app.get("/file")
def file_page():
    return FileResponse(str(FRONTEND_DIR / "file.html"))


@app.get("/settings")
def settings():
    return FileResponse(str(FRONTEND_DIR / "settings.html"))


@app.get("/favicon.ico")
def favicon():
    from fastapi import Response

    return Response(status_code=204)


@app.get("/public-folder")
def public_folder_page():
    return FileResponse(str(FRONTEND_DIR / "public-folder.html"))
