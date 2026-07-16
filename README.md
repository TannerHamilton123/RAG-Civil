# RAG-Civil

## Introduction
RAG Civil is an Application layer for civil engineers to interact with AI models while conveniently providing organized project-specific documents through the user interface.

## Use Case
A civil engineer visits this site and uploads documents relevant to their project(s). Then the engineer asks questions about the project, and an AI assistant reviews only the documents and responds with cited answers for the engineer. 

## Frontend
Basic HTML with JS script.
Frontend handles sending the text and files to FastAPI endpoints, and recieving AI responses.

## Backend
FastAPI - 2 API's
### Upload_Document
HTML sends document and name to API, and the API processes this information for making available for RAG.
### Submit_Question
User's question is concatenated with assistant instructions, the context of the conversation, and relevant chunks from documents.

## Chunking
When a file is uploaded and sent to the API, the material is copied into chunks, which are texts of information of smaller token size.
The function loops through each page of the pdf and extracts the text. There a multiple ways to determine how to delineate chunks. I chose to divide by sentences with a limit of 100 tokens (or one sentence that may be greater than 100 tokens.).
The function uses nltk_tokenize (a ML function) to divide the page text into sentences. I assumed that 1 word = 1.3 tokens. To be more accurate I could use [] but would add cost. The sentence is counted for tokens and added to current chunk or new chunk.

## Vectorization
Each chunk is passed into OpenAI embedding model. The model returns a vector representation of semantic meaning, and this is stored with the associated chunk within the overal document store dictionary.

## Retrieval
When a query is sent by the user, the text of the query is vectorized in the same way chunks are. Then the backend compares the query vector against all chunks available using cosine similarity. I chose for the top 5 similar chunks to be chosen as relevant. The relevant chunks are concatenated with their document name and page number, then included in the context of the message to Claude.
