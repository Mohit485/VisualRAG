import os
import shutil
import gradio as gr
 
from ragcore import ask
from ingest import process_pdf, process_image, PDF_FOLDER, IMAGE_FOLDER

def upload_file(file):
    if file is None:
        return "Please choose a file first."
    filename= os.path.basename(file)
    extension = filename.lower().split(".")[-1]
    if extension == "pdf":
        save_dir = PDF_FOLDER
    elif extension in ("png", "jpg", "jpeg"):
        save_dir = IMAGE_FOLDER
    else:
        return "Unsupported file type. Please upload a PDF, PNG, or JPG."
    
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)
    shutil.copy(file, save_path)

    if extension == "pdf":
        process_pdf(save_path)
    else:
        process_image(save_path)
 
    return f"'{filename}' added to the knowledge base. Go to the 'Ask a question' tab to try it."

def ask_question(question):
    if not question or not question.strip():
        return "Type a question first."
 
    result = ask(question)
    sources = "\n".join(f"- {s}" for s in result["sources"])
    return f"{result['answer']}\n\n**Sources:**\n{sources}"
# GRADIO
with gr.Blocks(title="VisualRAG") as demo:
    gr.Markdown("# VisualRAG")
    with gr.Tab("1. Add to knowledge base"):
        file_input = gr.File(
            label="Upload a PDF or image",
            file_types=[".pdf", ".png", ".jpg", ".jpeg"],
        )
        upload_button = gr.Button("Add to knowledge base")
        upload_status = gr.Markdown()
        # .click() wires the button to a function: when clicked, take the current value of file_input, pass it into upload_file(), and
        upload_button.click(fn=upload_file, inputs=file_input, outputs=upload_status)
    with gr.Tab("2. Ask a question"):
        question_input = gr.Textbox(
            label="Your question",
            placeholder="e.g. What loss function does the paper use?",
        )
        ask_button = gr.Button("Ask")
        answer_output = gr.Textbox(label="answer", lines=10, interactive= False)
        ask_button.click(fn=ask_question, inputs=question_input, outputs=answer_output)

if __name__== "__main__":
    demo.launch()