from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import db
from .routes import chat

app = FastAPI(
    title="Chat Summarization and Insights API",
    description="A FastAPI-based REST API that processes user chat data and generates summaries using Gemini API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)

@app.on_event("startup")
async def startup_event():
    await db.connect_db()

@app.on_event("shutdown")
async def shutdown_event():
    await db.close_db()

@app.get("/")
async def root():
    return {"message": "Welcome to Chat Summarization and Insights API"}