from langchain_community.document_loaders import PyPDFLoader
from docx import Document

class FileHelper:
    def extract_text_from_pdf(pdf_path):
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        return "\n".join([page.page_content for page in pages])

    def read_docx(file_path):
        doc = Document(file_path)
        text = []
        for para in doc.paragraphs:
            text.append(para.text)
        return "\n".join(text)

    def read_text_content(self, file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return content