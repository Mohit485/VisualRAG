"""Run this file whenever you want to add new PDFs or images to your
knowledge base
It looks inside data/pdfs/ and data/images/, processes everything it finds,
and saves the results into the chroma_db/ folder (created automatically the
first time you run this)."""

import os
import fitz # pdf rendering python library
from ragcore import add_image, add_text

PDF_FOLDER = "data/pdfs"
IMAGE_FOLDER = "data/images"
RENDERED_PAGES_FOLDER = "data/rendered_pages"  # PDF pages get saved here as PNGs

os.makedirs(RENDERED_PAGES_FOLDER, exist_ok= True)
def process_pdf(pdf_path):
    """
    For every page in a PDF, we do TWO things:
      1. Pull out the raw text and save it as a text chunk
      2. Render the page as a PNG image and save it as an image chunk
    """
    filename = os.path.basename(pdf_path)
    doc = fitz.open(pdf_path)
    print(f"Processing {filename} ({len(doc)} pages)...")

    for page_number in range(len(doc)):
        page = doc[page_number]
        #text side
        text = page.get_text().strip()
        if text:  # skip blank/near-empty pages (e.g. a title page with just a logo)
            add_text(text=text, source=filename, page=page_number + 1)
        # --- Image side ---
        # dpi=150 is a good balance: sharp enough to read small labels
        # inside a figure, but not so huge that it slows down CPU embedding.
        pixmap = page.get_pixmap(dpi=150)
        image_path = os.path.join(
            RENDERED_PAGES_FOLDER, f"{filename}_page{page_number + 1}.png"
        )
        pixmap.save(image_path)
        add_image(image_path=image_path, source=filename, page=page_number + 1)
        try:
            os.remove(image_path)
        except OSError:
            pass
 
    doc.close()
    print(f"  -> done with {filename}")
    doc.close()
    print(f"  -> done with {filename}")


def process_image(image_path):
# Adds a standalone image (e.g. a diagram screenshot you saved from a paper or slide) directly into the knowledge base. No text side exists
    filename = os.path.basename(image_path)
    add_image(image_path=image_path, source=filename, page="N/A")
    print(f"Added image: {filename}")

if __name__== "__main__":
    found_anything = False
 
    if os.path.isdir(PDF_FOLDER):
        for file in os.listdir(PDF_FOLDER):
            if file.lower().endswith(".pdf"):
                process_pdf(os.path.join(PDF_FOLDER, file))
                found_anything = True
 
    if os.path.isdir(IMAGE_FOLDER):
        for file in os.listdir(IMAGE_FOLDER):
            if file.lower().endswith((".png", ".jpg", ".jpeg")):
                process_image(os.path.join(IMAGE_FOLDER, file))
                found_anything = True

    if not found_anything:
        print(
            "No files found. Put some PDFs in data/pdfs/ and/or images in "
            "data/images/, then run this script again."
        )
    else:
        print("\nAll done! Your knowledge base is saved in the chroma_db/ folder.")
 

