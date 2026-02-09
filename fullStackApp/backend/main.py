import os
import shutil
import torch
import clip
import numpy as np
from PIL import Image
import easyocr
import tempfile

from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sklearn.metrics.pairwise import cosine_similarity
from fastapi.middleware.cors import CORSMiddleware

# ======================
# FASTAPI SETUP
# ======================
app = FastAPI()

# Allow CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.get("/admin")
def admin():
    return FileResponse("static/admin.html")

# ======================
# CLIP SETUP
# ======================
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)
model.eval()
print("CLIP running on:", device)

# ======================
# EasyOCR
# ======================
reader = easyocr.Reader(['en'])

# ======================
# Paths
# ======================
IMAGE_ROOT = "static/images"
METALS = ["gold", "silver", "copper"]

# ======================
# CLIP helpers
# ======================
def get_img_emb(path):
    img = preprocess(Image.open(path).convert("RGB")).unsqueeze(0).to(device)
    with torch.no_grad():
        vec = model.encode_image(img)
    return (vec / vec.norm(dim=-1, keepdim=True)).cpu().numpy()[0]

def get_text_emb(text):
    tokens = clip.tokenize([text]).to(device)
    with torch.no_grad():
        vec = model.encode_text(tokens)
    return (vec / vec.norm(dim=-1, keepdim=True)).cpu().numpy()[0]

# ======================
# Metal detection
# ======================
metal_prompts = {
    "gold": "gold jewelry yellow metal luxury",
    "silver": "silver jewelry white metal",
    "copper": "copper reddish metal"
}
metal_vectors = {m: get_text_emb(p) for m, p in metal_prompts.items()}

def detect_metal(img_vec):
    best = None
    best_score = -1
    for m, v in metal_vectors.items():
        score = np.dot(img_vec, v)
        if score > best_score:
            best_score = score
            best = m
    return best

# ======================
# In-memory index
# ======================
image_paths = []
image_vectors = []
image_metals = []

def index_all_images():
    image_paths.clear()
    image_vectors.clear()
    image_metals.clear()
    print("Indexing images...")
    for metal in METALS:
        folder = os.path.join(IMAGE_ROOT, metal)
        os.makedirs(folder, exist_ok=True)
        for f in os.listdir(folder):
            if f.lower().endswith((".jpg", ".png", ".jpeg", ".webp")):
                path = os.path.join(folder, f)
                image_paths.append(path)
                image_vectors.append(get_img_emb(path))
                image_metals.append(metal)
    print("Indexed:", len(image_paths))

index_all_images()

# ======================
# TEXT SEARCH
# ======================
@app.post("/search")
async def search(data: dict):
    query = data.get("query", "").strip()
    if not query:
        return {"images": []}

    q_vec = get_text_emb(query)
    sims = cosine_similarity([q_vec], image_vectors)[0]

    # Optional metal filter
    metal_filter = None
    for m in METALS:
        if m in query.lower():
            metal_filter = m

    scored = []
    for i, s in enumerate(sims):
        if metal_filter and image_metals[i] != metal_filter:
            continue
        scored.append((s, image_paths[i]))

    # Sort descending by similarity
    scored.sort(reverse=True, key=lambda x: x[0])

    # Dynamic threshold: only keep images significantly similar
    if scored:
        max_score = scored[0][0]
        threshold = max_score * 0.8
        scored = [p for s, p in scored if s >= threshold]

    # Return top 8 max
    results = [f"/static/{os.path.relpath(p,'static').replace(os.sep,'/')}" for p in scored[:8]]

    return {"images": results}

# ======================
# IMAGE SEARCH + OCR fallback
# ======================
@app.post("/search/image")
async def search_image(file: UploadFile = File(...)):
    # Safe temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        temp_path = tmp.name
        tmp.write(await file.read())

    results = []
    extracted_text = "jewelry"
    try:
        # 1️⃣ Extract text using OCR
        ocr_result = reader.readtext(temp_path, detail=0)
        extracted_text = " ".join(ocr_result).strip() or "jewelry"

        # 2️⃣ Embed image for similarity search
        img_vec = get_img_emb(temp_path)
        sims = cosine_similarity([img_vec], image_vectors)[0]

        scored = [(s, image_paths[i]) for i, s in enumerate(sims)]
        scored.sort(reverse=True, key=lambda x: x[0])

        # Dynamic threshold
        if scored:
            threshold = scored[0][0] * 0.8
            scored = [p for s, p in scored if s >= threshold]

        results = [f"/static/{os.path.relpath(p,'static').replace(os.sep,'/')}" for p in scored[:8]]

    except Exception as e:
        print("Image search failed:", e)

    finally:
        os.remove(temp_path)

    return {"query": extracted_text, "images": results}

# ======================
# ADMIN UPLOAD
# ======================
@app.post("/admin/upload")
async def upload(file: UploadFile = File(...)):
    # Save temp file safely
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        temp_path = tmp.name
        tmp.write(await file.read())

    try:
        vec = get_img_emb(temp_path)
        metal = detect_metal(vec)

        save_folder = os.path.join(IMAGE_ROOT, metal)
        os.makedirs(save_folder, exist_ok=True)

        final_path = os.path.join(save_folder, file.filename)
        shutil.move(temp_path, final_path)

        # Re-index instantly
        image_paths.append(final_path)
        image_vectors.append(vec)
        image_metals.append(metal)

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return {"status": "ok", "metal": metal}
