import os
import torch
import clip
import numpy as np
from PIL import Image
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sklearn.metrics.pairwise import cosine_similarity

# =========================
# FastAPI
# =========================

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def home():
    return FileResponse("static/index.html")


# =========================
# CLIP setup
# =========================

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)
model.eval()

print("CLIP running on:", device)


# =========================
# Load + index images
# =========================

IMAGE_ROOT = "static/images"

image_paths = []
image_vectors = []
image_metals = []   # gold / silver / copper


def get_image_emb(path):
    img = preprocess(Image.open(path).convert("RGB")).unsqueeze(0).to(device)

    with torch.no_grad():
        vec = model.encode_image(img)

    vec = vec / vec.norm(dim=-1, keepdim=True)
    return vec.cpu().numpy()[0]


print("🔵 Indexing images...")

for metal in os.listdir(IMAGE_ROOT):

    metal_path = os.path.join(IMAGE_ROOT, metal)

    if not os.path.isdir(metal_path):
        continue

    for f in os.listdir(metal_path):
        if f.lower().endswith((".jpg", ".png", ".jpeg", ".webp")):

            path = os.path.join(metal_path, f)

            image_paths.append(path)
            image_vectors.append(get_image_emb(path))
            image_metals.append(metal.lower())

print(f"✅ Indexed {len(image_paths)} images")

image_vectors = np.array(image_vectors)


# =========================
# Helpers
# =========================

METALS = ["gold", "silver", "copper"]


def detect_metal_from_text(text):
    text = text.lower()
    for m in METALS:
        if m in text:
            return m
    return None


def get_text_emb(text):
    tokens = clip.tokenize([text]).to(device)

    with torch.no_grad():
        vec = model.encode_text(tokens)

    vec = vec / vec.norm(dim=-1, keepdim=True)
    return vec.cpu().numpy()[0]


def search_clip(text, topk=12):
    query_vec = get_text_emb(text)
    sims = cosine_similarity([query_vec], image_vectors)[0]

    metal_filter = detect_metal_from_text(text)

    scored = []

    for i, score in enumerate(sims):

        # filter by metal if specified
        if metal_filter and image_metals[i] != metal_filter:
            continue

        scored.append((score, image_paths[i]))

    scored.sort(reverse=True)

    results = []

    for score, path in scored[:topk]:
        rel = os.path.relpath(path, "static")
        results.append(f"/static/{rel.replace(os.sep,'/')}")

    return results


# =========================
# API
# =========================

class SearchRequest(BaseModel):
    query: str


@app.post("/search")
async def search(data: SearchRequest):
    images = search_clip(data.query)
    return {"images": images}
