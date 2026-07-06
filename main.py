from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
import anthropic
import io
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

# class UploadedDocument(BaseModel):
#     name: str
#     filepath: str

client = anthropic.Anthropic()
@app.post("/ask_question")
def ask_question(request: Request):

    document_context = ""
    for file in document_store:
        text = f"Document{file}: {document_store[file]}\n"
        document_context += text


    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        system = "You're a civil engineering assistant. " \
        "Do not assume calculations or answers. " \
        "Only reference known knowledge, and reference any facts you make." \
        "Reference which document you got information from, and where within the document.",
        
        messages=[{
            "role":"user",
            "content": f"Here are the project documents:\n\n{document_context}\n\nQuestion: {request.question}"
            }]
        )
    return {"answer":message.content[0].text}



@app.post("/upload_file")
async def upload_file(file: UploadFile = File(...), name:str = Form(...)):
    contents = await file.read()

    if name.endswith(".pdf"):
        #convert bytes to readable format
        reader = PdfReader(io.BytesIO(contents))
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        document_store[name] = text
        print("document" + name + " uploaded")

    return {"message": f"Stored document under '{name}'"}