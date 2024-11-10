from fastapi import FastAPI, File, UploadFile, Form
from transformers import pipeline
from typing import List
import json

# Initialize FastAPI app
app = FastAPI()

# Initialize the text generation pipeline with the Qwen model
pipe = pipeline("text-generation", model="Qwen/Qwen2.5-1.5B-Instruct")

# Endpoint to upload CV file and store CV text
@app.post("/upload-cv/")
async def upload_cv(file: UploadFile = File(...)):
    content = await file.read()
    cv_text = content.decode("utf-8")
    return {"cv_text": cv_text}

# Endpoint to compare job descriptions with the CV text
@app.post("/compare/")
async def compare_job_cv(job_descriptions: str = Form(...), cv_text: str = Form(...)):
    # Split job descriptions by line
    descriptions = job_descriptions.strip().split("\n")
    results = []
    
    for description in descriptions:
        # Create prompt for the Qwen model
        prompt = f"Compare the following job description with this resume. Job Description: {description}. Resume: {cv_text}. Give a match score and brief analysis."
        
        # Generate response using the text generation pipeline
        response = pipe(prompt, max_length=100, num_return_sequences=1)
        response_content = response[0]["generated_text"]
        
        # Parse response content for score and summary if JSON formatted
        try:
            response_data = json.loads(response_content)
            results.append(response_data)
        except json.JSONDecodeError:
            results.append({
                "Job Description": description,
                "Analysis": response_content  # Use raw response if JSON parsing fails
            })
    
    return {"results": results}

 
