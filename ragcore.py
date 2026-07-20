import os
import base64
from dotenv import load_dotenv
from groq import Groq
from langchain_community.vectorstores import Chroma
from langchain_experimental.open_clip import OpenCLIPEmbeddings

load_dotenv() #load_dotenv() reads the .env file sitting in this same folder and copies its values (like GROQ_API_KEY) into the environment

#The Embedding Model (CLIP)
#open_clip_torch is the free, open-source rebuild of CLIP (made by LAION). We're using "ViT-B-32", the SMALLEST/FASTEST version 
print("Loading CLIP model... (first run downloads ~350MB, then it's cached on disk)")

embedding_fn= OpenCLIPEmbeddings(
    model_name= "ViT-B-32",
    checkpoint= "laion2b_s34b_b79k"
)

# the Vector Database
#ChromaDB's whole job is: store thousands of these number-lists, and when we hand it a new one, quickly tell us which stored ones are the closest match 

chroma_dir= "chroma_db"

vectorstore= Chroma(
    collection_name= "research_companion",
    embedding_function= embedding_fn,
    persist_directory= chroma_dir #persist_directory means Chroma saves everything to a folder on disk
)

# Groq client
groq_client= Groq(api_key= os.environ.get("GROQ_API_KEY"))
TEXT_MODEL = os.environ.get("GROQ_TEXT_MODEL", "openai/gpt-oss-20b")
VISION_MODEL = os.environ.get("GROQ_VISION_MODEL", "qwen/qwen3.6-27b")

#Adding text to Knowledge base
def add_text(text, source, page):
    vectorstore.add_texts(
        texts=[text],
        metadatas=[{"type": "text", "source": source, "page": str(page)}],
    )

#Adding Image to Knowledge Base
def add_image(image_path, source, page):
    vectorstore.add_images(
        uris=[image_path],
        metadatas=[{"type": "image", "source": source, "page": str(page)}],
    )

# Searching The Knowledge Base
def search(query, k=5):
    return vectorstore.similarity_search(query, k=k )

# 7. ASKING GROQ TO WRITE THE ANSWER
def ask(query, k=5):
    """
    The full RAG pipeline in one function:
      1. Search the vector DB for relevant chunks
      2. Split the results into text pieces and image pieces
      3. Send everything to Groq and ask it to answer USING ONLY this
         retrieved material -- this is what makes the answer "grounded":
         the model isn't guessing from general training knowledge, it's
         reading exactly what we handed it
      4. Return the answer plus a list of sources, so you can go verify
         it against the original PDF page yourself
    """
    results= search(query, k=k)
    text_pieces=[]
    image_pieces=[]
    sources=[]


    for doc in results:
        meta= doc.metadata
        sources.append(f"{meta['source']} (page {meta['page']})")
        if meta["type"]== "text":
            text_pieces.append(doc.page_content)
        else:
            image_pieces.append(doc.page_content)

    # Simple string joining -- nothing fancy needed here.
    context_text = "\n\n".join(text_pieces) if text_pieces else "(no text matches found)"
    instructions = (
        "You are a research assistant helping with a literature review. "
        "Answer the question using ONLY the context and images provided "
        "below. If the answer isn't in them, say you don't know instead "
        "of guessing.\n\n"
        f"Context:\n{context_text}\n\nQuestion: {query}"
    )
    # If we retrieved any images, we MUST use the vision model and attach the images to the message.
    if image_pieces:
        content= [{"type": "text", "text": instructions}]
        for imgb64 in image_pieces:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{imgb64}"},
            })

        model_to_use= VISION_MODEL
        messages= [{"role": "user", "content": content}]
    else:
        model_to_use= TEXT_MODEL
        messages = [{"role": "user", "content": instructions}]

    response= groq_client.chat.completions.create(
        model= model_to_use,
        messages= messages,
        temperature=0.2,# low temperature = stick close to the facts, less "creative" drift
        max_tokens= 800
        )

    answers= response.choices[0].message.content
    return{"answer": answers, "sources": sources}