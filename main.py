from fastapi import FastAPI, UploadFile
from pydantic import BaseModel
import anthropic
from dotenv import load_dotenv
from pypdf import PdfReader

load_dotenv()

from fastapi.middleware.cors import CORSMiddleware


#Stores all the info from uploaded documents
document_store = {}
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/number/{number}")
async def get_number(number: int):
    return {"message": f"The number is {number}"}

class Request(BaseModel):
    question: str

class UploadedDocument(BaseModel):
    name: str
    filepath: str

client = anthropic.Anthropic()
@app.post("/ask_question")
def ask_question(request: Request):
    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        system = "You're a civil engineering assistant. " \
        "Do not assume calculations or answers. " \
        "Only reference known knowledge, and reference any facts you make.",
        
        messages=[{
            "role":"user",
            "content":request.question
            }]
        )
    return {"answer":message.content[0].text}

@app.post("/upload_file")
def upload_file(file: UploadFile, category:str):
    
    doc = PdfReader(file)
    text = ""
    for page in doc.pages:
        text+= page.extract_text()
    document_store[file.name] = text


    