from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel #Pydantic's BaseModel is a way of describing "what shape of data do I expect to receive".
from ragcore import ask
import gradio as gr
import os 
import shutil


from ragcore import ask
from ingest import process_pdf, process_image, PDF_FOLDER, IMAGE_FOLDER
from app import demo  # the Gradio Blocks interface defined in app_ui.py

app= FastAPI(title= "VisualRAG")
class Question(BaseModel):
    question : str

@app.get("/")
def health_check():
    # A simple endpoint just to confirm the server is alive and reachable.
    return {"status": "ok", "message": "VisualRAG is running"}

@app.post("/ask")
def ask_question(payload: Question):
    """
    Receives a question, runs it through our RAG pipeline (search + Groq),
    and returns the answer with sources.
    """

    result = ask(payload.question)
    return result

@app.post("/ingest")
async def ingest_file(file: UploadFile = File(...)):
    """Lets you add a file to the knowledge base through the raw API -- e.g.
    from curl, Postman, or another program -- independent of the Gradio
    UI"""
    filename= file.filename
    extension= filename.lower().split(".")[-1]
    if extension== "pdf":
        save_dir= PDF_FOLDER
    elif extension== ("jpg", "png", "jpeg"):
        save_dir= IMAGE_FOLDER
    else:
        return {"error": "Unsupported file type. Please upload a PDF, PNG, or JPG."}
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer) # standard safe way to save an uploaded file
 
    if extension == "pdf":
        process_pdf(save_path)
    else:
        process_image(save_path)

        
    try:
        os.remove(save_path)
    except OSError:
        pass
 
    return {"status": "success", "message": f"{filename} added to the knowledge base"}

app = gr.mount_gradio_app(app, demo, path="/ui")