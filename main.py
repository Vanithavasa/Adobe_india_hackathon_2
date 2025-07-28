import os
import json
import pdfplumber
import datetime
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load input JSON
with open("input.json", "r") as f:
    input_data = json.load(f)

persona = input_data["persona"]["role"]
job = input_data["job_to_be_done"]["task"]
documents = input_data["documents"]

# Load transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')  # Small, efficient

# Create query embedding
query = f"{persona} needs to: {job}"
query_embedding = model.encode(query)

# Store candidates
section_candidates = []

for doc in tqdm(documents, desc="Processing documents"):
    filepath = os.path.join("docs", doc["filename"])
    if not os.path.exists(filepath):
        print(f"❌ Missing file: {filepath}")
        continue

    with pdfplumber.open(filepath) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
            chunks = text.split("\n\n")
            for chunk in chunks:
                if not chunk.strip():
                    continue
                chunk_embedding = model.encode(chunk)
                score = cosine_similarity(
                    [query_embedding], [chunk_embedding]
                )[0][0]
                section_candidates.append({
                    "document": doc["filename"],
                    "page_number": i + 1,
                    "text": chunk.strip(),
                    "similarity": float(score)
                })

# Rank and extract top 5
top_sections = sorted(section_candidates, key=lambda x: x["similarity"], reverse=True)[:5]

# Format output
output = {
    "metadata": {
        "input_documents": [doc["filename"] for doc in documents],
        "persona": persona,
        "job_to_be_done": job,
        "processing_timestamp": datetime.datetime.now().isoformat()
    },
    "extracted_sections": [],
    "subsection_analysis": []
}

# Simulate titles using text slices
for rank, sec in enumerate(top_sections, start=1):
    output["extracted_sections"].append({
        "document": sec["document"],
        "section_title": sec["text"][:80] + ("..." if len(sec["text"]) > 80 else ""),
        "importance_rank": rank,
        "page_number": sec["page_number"]
    })
    output["subsection_analysis"].append({
        "document": sec["document"],
        "refined_text": sec["text"],
        "page_number": sec["page_number"]
    })

# Save output
with open("output.json", "w") as f:
    json.dump(output, f, indent=4)

print("✅ Output saved to output.json")

