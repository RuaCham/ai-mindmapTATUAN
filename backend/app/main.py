# main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.pdf_routes      import router as pdf_router
from app.routes.mindmap_routes  import router as mindmap_router
from app.routes.mindmap_store_routes import router as store_router
from app.db.database import init_db

# Tạo thư mục storage
os.makedirs("storage/pdfs",     exist_ok=True)
os.makedirs("storage/previews", exist_ok=True)

app = FastAPI(
    title="AI Mindmap Generator",
    description="Tự động tạo mindmap từ PDF bằng thuật toán NLP",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://ai-mindmap-tatuan-last.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init database khi startup
@app.on_event("startup")
def startup():
    init_db()

app.include_router(pdf_router,    prefix="/api", tags=["PDF"])
app.include_router(mindmap_router,prefix="/api", tags=["Mindmap"])
app.include_router(store_router,  prefix="/api", tags=["Store"])

@app.get("/")
def root():
    return {"status": "ok", "version": "2.0.0"}
