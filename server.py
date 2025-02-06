from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import pdfplumber
import re
import json
from io import BytesIO

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific origins for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def download_pdf(pdf_url):
    response = requests.get(pdf_url)
    if response.status_code == 200:
        return BytesIO(response.content)
    else:
        raise HTTPException(status_code=400, detail=f"Failed to download PDF: {response.status_code}")

def extract_text_from_pdf(pdf_stream):
    text = ""
    with pdfplumber.open(pdf_stream) as pdf:
        for page in pdf.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text += extracted_text + "\n"
    return text

def parse_questions(text):
    question_pattern = re.compile(
        r"(\d+\..*?)\n(a\) .*?)\n(b\) .*?)\n(c\) .*?)\n(d\) .*?)\nAnswer:\s*([a-d]\))",
        re.DOTALL
    )

    questions = []
    for match in question_pattern.findall(text):
        question_text = match[0].strip()
        options = [{"name": match[i].strip()} for i in range(1, 5)]
        correct_letter = match[5].strip()
        correct_ans = next(option["name"] for option in options if option["name"].startswith(correct_letter))

        questions.append({
            "question": question_text,
            "options": options,
            "correctAns": correct_ans
        })

    return questions

@app.post("/parse-pdf")
async def parse_pdf(data: dict):
    pdf_url = data.get("pdfUrl")
    if not pdf_url:
        raise HTTPException(status_code=400, detail="Missing pdfUrl")

    try:
        pdf_stream = download_pdf(pdf_url)
        pdf_text = extract_text_from_pdf(pdf_stream)
        questions = parse_questions(pdf_text)
        return {"data": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/healthCheck")
async def checkHealth(data: dict):
     check = True;
     return {"success":check}
