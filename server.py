from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine 
from app.routes import auth, chat, journal
import uvicorn, os


app = FastAPI(title="MindPal Chatbot Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(journal.router)

os.environ['LANGSMITH_API_KEY'] = ""
os.environ['LANGSMITH_ENDPOINT'] = ""
os.environ['LANGSMITH_PROJECT'] = ""
os.environ['LANGSMITH_TRACING_V2'] = "true"
load_dotenv(dotenv_path=".env", override=True)

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Server:", "Database schemas are created successfully")

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

