import re
import os
from typing import List
from fastapi import FastAPI
from fastapi import Form
from importlib_resources import contents
from pydantic import BaseModel
from fastapi import UploadFile, File
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ✅ ADDED (CORS for frontend connection)
from fastapi.middleware.cors import CORSMiddleware

def semantic_similarity(text1, text2):
    aliases = {
        "ml": "machine learning",
        "py": "python",
        "web dev": "web development"
    }

    # Normalize text
    for short, full in aliases.items():
        text1 = text1.replace(short, full)
        text2 = text2.replace(short, full)

    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([text1, text2])
    similarity = cosine_similarity(vectors[0], vectors[1])

    return similarity[0][0]

app = FastAPI()

# ✅ ADDED (CORS middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResumeListRequest(BaseModel):
    job_description: str
    resumes: list[str]

@app.get("/")
def home():
    return {"message": "AI Resume Screening Backend is running"}

@app.get("/health")
def health_check():
    return {"status": "OK", "service": "AI Resume Screening"}

class JobDescription(BaseModel):
    text: str

@app.post("/rank-resumes")
def rank_resumes(data: ResumeListRequest):

    jd = re.sub(r'[^\w\s]', '', data.job_description.lower())

    skills = {
        "python": 5,
        "fastapi": 4,
        "react": 3,
        "java": 4,
        "sql": 4,
        "machine learning": 8,
        "data science": 7,
        "web development": 5
    }

    skill_aliases = {
    "python": ["python", "py"],
    "fastapi": ["fastapi"],
    "react": ["react"],
    "java": ["java"],
    "sql": ["sql"],
    "machine learning": ["machine learning", "ml"],
    "data science": ["data science", "data analysis"],
    "web development": ["web development", "web dev"]
    }

    jd_skills = set()
    for skill, aliases in skill_aliases.items():
        for alias in aliases:
            if alias in jd:
                jd_skills.add(skill)

    results = []

    for resume_text in data.resumes:

        resume = re.sub(r'[^\w\s]', '', resume_text.lower())

        resume_skills = set()
        for skill, aliases in skill_aliases.items():
            for alias in aliases:
                if alias in resume:
                    resume_skills.add(skill)
                    break

        common_skills = jd_skills.intersection(resume_skills)

        total_weight = sum(skills[skill] for skill in jd_skills)
        if total_weight == 0:
            keyword_score = 0
            semantic_score = 0
            final_score = 0
        else:
            matched_weight = sum(skills[skill] for skill in common_skills)
            keyword_score = (matched_weight / total_weight) * 100
            semantic_score = semantic_similarity(jd, resume) * 100
            final_score = (0.7 * keyword_score) + (0.3 * semantic_score)

        experience_bonus = 0
        years = re.findall(r'\d+\s+year', resume)
        if years:
            experience_bonus = min(int(years[0].split()[0]), 5)

        clean_text = re.sub(r'\S+@\S+|\d{10}', '', resume_text)
        preview = clean_text.strip()[:120]
        results.append({
        "resume_preview": resume_text.replace("\n", " ")[:120],
        "score": round(final_score, 2),
        "matched_skills": 
        list(common_skills)
        })

    results = sorted(results, key=lambda x: x["score"], reverse=True)
    for i, res in enumerate(results):
        res["rank"] = i + 1

    return {"ranked_resumes": results}

@app.post("/rank-from-files")
def rank_from_files(job_description: str = Form(...)):

    folder_path = "resumes"

    # ✅ ADDED (safe check)
    if not os.path.exists(folder_path):
        return {"error": "Resumes folder not found"}

    resumes = []

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        with open(file_path, "r") as file:
            content = file.read()
            resumes.append(content)

    data = ResumeListRequest(
        job_description=job_description,
        resumes=resumes
    )

    return rank_resumes(data)

import pdfplumber

@app.post("/upload-resume")
def upload_resume(
    files: List[UploadFile] = File(...),
    job_description: str = Form(...)
):
    contents = []
    for file in files:

        # ✅ ADDED (safety check)
        if not file.filename:
            continue

        file.file.seek(0)

        if file.filename.endswith(".txt"):
            content = file.file.read().decode("utf-8", errors="ignore")

        elif file.filename.endswith(".pdf"):
            content = ""
            with pdfplumber.open(file.file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        content += text
        else:
            continue

        if content.strip():
            contents.append(content)

    print("FILES RECEIVED:", len(files))
    print("CONTENTS CREATED:", len(contents))

    unique_contents = []
    seen = set()
    for content in contents:
        normalized = content.strip().lower()
        if normalized not in seen:
            unique_contents.append(content)
            seen.add(normalized)

    job_description = job_description

    data = ResumeListRequest(
        job_description=job_description,
        resumes=unique_contents
    )

    print("After dedup:", len(unique_contents))
    result = rank_resumes(data)

    print("Final resumes sent to ranking:", len(unique_contents))

    return result