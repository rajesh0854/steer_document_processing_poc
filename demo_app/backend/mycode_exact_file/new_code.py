# Import required libraries
from PyPDF2 import PdfReader
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain_community.document_loaders import OnlinePDFLoader
from langchain.indexes import VectorstoreIndexCreator
import os
import json
from pathlib import Path

# Get the absolute path to the PDF file
current_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(current_dir, 'sample_docs', 'Enquiry form - Gulf Additives (Revised 11112024).pdf')
# pdf_path = os.path.join(current_dir, 'sample_docs', 'B - 083 05.05.2025.pdf')
# pdf_path=os.path.join(current_dir, 'sample_docs', 'EM19335_Quotation_with_material__23.05.2025.pdf')
#pdf_path=os.path.join(current_dir, 'sample_docs', 'Estimate_3444_26-05-2025_.pdf')



pdfreader = PdfReader(pdf_path)

# Extract text from PDF
raw_text = ''
page_contents = []
for i, page in enumerate(pdfreader.pages):
    content = page.extract_text()
    if content:
        raw_text += content
        page_contents.append({f"page_{i+1}": content})
        

# Create output JSON file
pdf_filename = Path(pdf_path).stem
output_json_path = os.path.join(current_dir, 'results', f"{pdf_filename}.json")

# Save the extracted text to JSON file
json_output = {
    "filename": pdf_filename,
    "total_pages": len(pdfreader.pages),
    "full_text": raw_text,
    "page_wise_content": page_contents
}

with open(output_json_path, 'w', encoding='utf-8') as json_file:
    json.dump(json_output, json_file, indent=4, ensure_ascii=False)

print(f"JSON output saved to: {output_json_path}")
#

