from fastapi import FastAPI

from app.database import Base, engine
from app.routers import tickets

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Customer Support Backend",
    version="1.0.0",
    description=(
        "Ticket management API with AI-powered classification and reply drafting. "
        "Runs in demo mode (rule-based) without an OpenAI API key."
    ),
)
app.include_router(tickets.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
