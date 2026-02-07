import os
import shutil
import torch
import clip
import numpy as np
from PIL import Image

from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sklearn.metrics.pairwise import cosine_similarity


# ======================
# FASTAPI
# ======================

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.get("/admin")
def admin():
    return FileResponse("static/admin.html")


# ======================
# CLIP setup
# ======================

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)
model.eval()

print("CLIP running on:", device)


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
# Metal routing
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
# SEARCH API
# ======================

@app.post("/search")
async def search(data: dict):
    query = data["query"]

    q_vec = get_text_emb(query)
    sims = cosine_similarity([q_vec], image_vectors)[0]

    metal_filter = None
    for m in METALS:
        if m in query.lower():
            metal_filter = m

    scored = []

    for i, s in enumerate(sims):
        if metal_filter and image_metals[i] != metal_filter:
            continue
        scored.append((s, image_paths[i]))

    scored.sort(reverse=True)

    results = []

    for s, p in scored[:12]:
        rel = os.path.relpath(p, "static")
        results.append(f"/static/{rel.replace(os.sep,'/')}")

    return {"images": results}


# ======================
# ADMIN UPLOAD + CLUSTER
# ======================

@app.post("/admin/upload")
async def upload(file: UploadFile = File(...)):
    temp_path = f"temp_{file.filename}"

    with open(temp_path, "wb") as f:
        f.write(await file.read())

    vec = get_img_emb(temp_path)

    metal = detect_metal(vec)

    save_folder = os.path.join(IMAGE_ROOT, metal)
    os.makedirs(save_folder, exist_ok=True)

    final_path = os.path.join(save_folder, file.filename)

    shutil.move(temp_path, final_path)

    # re-index instantly
    image_paths.append(final_path)
    image_vectors.append(vec)
    image_metals.append(metal)

    return {"status": "ok", "metal": metal}
