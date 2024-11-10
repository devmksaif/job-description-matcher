import streamlit as st
from llama_cpp import Llama
import json

# Load the Llama model
llm = Llama.from_pretrained(
    repo_id="HuggingFaceTB/SmolLM2-1.7B-Instruct-GGUF",
    filename="smollm2-1.7b-instruct-q4_k_m.gguf",
)

# Streamlit UI for Job Description Matcher
st.title("Job Description Matcher with AI")

# Step 1: Upload CV File
st.subheader("Upload CV File (Text format only)")
uploaded_file = st.file_uploader("Choose a file", type="txt")

cv_text = ""
if uploaded_file is not None:
    # Read the uploaded file content
    cv_text = uploaded_file.read().decode("utf-8")
    st.text_area("CV Content", cv_text, height=200)

# Step 2: Enter Job Descriptions
st.subheader("Enter Job Descriptions (Separate each description by a new line)")
job_descriptions = st.text_area("Job Descriptions", height=200)

# Button to trigger comparison
if st.button("Compare and Score") and cv_text:
    if job_descriptions:
        # Split job descriptions by line
        descriptions = job_descriptions.strip().split("\n")
        results = []

        for description in descriptions:
            # Create chat messages to prompt Llama for each job description
            messages = [
                {"role": "user", "content": f"Compare the following job description with this resume. Job Description: {description}. Resume: {cv_text}. Give a match score and brief analysis."}
            ]
            
            # Generate response using Llama
            response = llm.create_chat_completion(messages=messages)
            response_content = response["choices"][0]["message"]["content"]

            # Parse response content for a score and summary
            try:
                response_data = json.loads(response_content)
                results.append(response_data)
            except json.JSONDecodeError:
                results.append({
                    "Job Description": description,
                    "Analysis": response_content  # Use raw response if JSON parsing fails
                })

        # Display results
        st.write("### Match Scores and Analysis:")
        for result in results:
            st.write(f"**Job Description:** {result.get('Job Description', 'N/A')}")
            st.write(f"**Analysis:** {result.get('Analysis', 'No Analysis Available')}")
            st.write("---")
    else:
        st.warning("Please enter job descriptions.")
else:
    if not cv_text:
        st.warning("Please upload a CV file.")
