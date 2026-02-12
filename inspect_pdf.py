import fitz # PyMuPDF
import sys

def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    for page in doc:
        print(f"--- Page {page.number} ---")
        text = page.get_text()
        # Safe printing for Windows console
        print(text.encode('ascii', errors='replace').decode('ascii'))
    doc.close()

if __name__ == "__main__":
    pdf_path = r"d:\development\NextLeap-RAG-MF\raw\schemes\HDFC_Flexi_Cap_Fund\HDFC_FlexiCap_Fund_Facts_Jan_2026.pdf"
    extract_text(pdf_path)
