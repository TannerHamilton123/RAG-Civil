from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
import anthropic
import io
from dotenv import load_dotenv
from pypdf import PdfReader
import nltk
from openai import OpenAI
import heapq
import numpy as np #Numpy and norm are for cosine similarity between vectors
from numpy.linalg import norm

nltk.download('punkt_tab')
from nltk.tokenize import sent_tokenize

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


def get_embedding(text):
    response = OpenAI().embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def get_relevant_chunks(question):
    question_embedding = get_embedding(question)
    
    chunk_similarity = {}
    for file_name, chunk_dict in document_store.items():
        for chunk_number in chunk_dict:
            current_chunk = chunk_dict[chunk_number]
            A = current_chunk["embedding"]
            B = question_embedding

            # compute cosine similarity
            cosine_similarity= np.dot(A, B) / (norm(A) * norm(B))

            chunk_info = f"{file_name} page {current_chunk['page_number']}: {current_chunk['text']}"
            chunk_similarity[chunk_info] = cosine_similarity

    top_items = heapq.nlargest(5, chunk_similarity.items(), key=lambda item: item[1])
    relevant_chunks_text = ""
    for chunk_info, similarity in top_items:
        relevant_chunks_text += str(chunk_info) + "\n"
        


    return relevant_chunks_text





@app.get("/")
async def root():
    return {"message": "Hello World"}


class Request(BaseModel):
    question: str

client = anthropic.Anthropic()
@app.post("/ask_question")
def ask_question(request: Request):

    relevant_chunks = get_relevant_chunks(request.question)
    try:
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            system = "You're a civil engineering assistant. " \
            "Do not assume calculations or answers. " \
            "Only reference known knowledge, and reference any facts you make." \
            "Reference which document you got information from, and where within the document.",
            
            messages=[{
                "role":"user",
                "content": f"Here are the project documents:\n\n{relevant_chunks}\n\nQuestion: {request.question}"
                }]
            )
        return {"answer":message.content[0].text}
    
    except anthropic.BadRequestError:
        return{"answer": "Invalid request or context is maxxed out!"}






#The function scans the uploaded file.
#If the file is pdf, the text is scanned for each page and divided into sentences.
#Each sentence is added to a chunk of maximum token size.
#The document store is stored as a dictionary with the file name as the key and a list of chunks as the value.
#each chunk is a dictionary with a page number, text, and vector

@app.post("/upload_file")
async def upload_file(file: UploadFile = File(...), name:str = Form(...)):
    token_chunk = 100
    contents = await file.read()
    chunk_number = 1

    if name.endswith(".pdf"):
        #convert bytes to readable format
        reader = PdfReader(io.BytesIO(contents))
        text = ""
        page_number = 0
        document_store[name] = {}
        for page in reader.pages:
    
            page_number += 1
            token_count = 0
            
            
            sentences = sent_tokenize(page.extract_text())

            #For each sentence in the page, check if sentence would make the chunk token count larger than max. 
            for sentence in sentences:
                approx_tokens = len(sentence.split()) * 1.3 #an estimate of tokens per word
                if token_count + approx_tokens <= token_chunk:
                    text += sentence
                    token_count += approx_tokens
                else:
                    #if not, then store the current text, and create a new chunk.
                    document_store[name][chunk_number] = {}
                    document_store[name][chunk_number]["text"] = text
                    document_store[name][chunk_number]["embedding"] = get_embedding(text)
                    document_store[name][chunk_number]["page_number"] = page_number
                    token_count = approx_tokens
                    text = sentence
                    chunk_number += 1
                
            document_store[name][chunk_number] = {}
            document_store[name][chunk_number]["text"] = text
            document_store[name][chunk_number]["embedding"] = get_embedding(text)
            document_store[name][chunk_number]["page_number"] = page_number
            #reset for next page
            chunk_number += 1
            text = ""


        print("document" + name + " uploaded")

    return {"message": f"Stored document under '{name}'"}