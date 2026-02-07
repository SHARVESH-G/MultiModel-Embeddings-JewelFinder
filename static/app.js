async function searchImages(e) {
    e.preventDefault();
    const query = document.getElementById("searchInput").value.trim();
    const div = document.getElementById("results");
    const status = document.getElementById("status");
    if (!query) return;

    div.innerHTML = "";
    status.textContent = "🔎 Searching...";

    try {
        const res = await fetch("/search", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query })
        });
        const data = await res.json();
        status.textContent = "";

        if (!data.images || data.images.length === 0) {
            status.textContent = "No matches found 😢";
            return;
        }

        data.images.forEach(src => {
            const img = document.createElement("img");
            img.src = src;
            img.className = "result-img";
            div.appendChild(img);
        });
    } catch (err) {
        status.textContent = "Something went wrong. Try again.";
        console.error(err);
    }
}

async function searchByImage() {
    const div = document.getElementById("results");
    const status = document.getElementById("status");
    const fileInput = document.getElementById("imageInput");

    if (!fileInput.files.length) return alert("Select an image first!");

    const file = fileInput.files[0];
    div.innerHTML = "";
    status.textContent = "🔎 Extracting text from image...";

    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch("/search/image", { method: "POST", body: formData });
        const data = await res.json();
        status.textContent = `OCR detected: "${data.query}"`;

        if (!data.images || data.images.length === 0) {
            status.textContent += " — No matches found 😢";
            return;
        }

        data.images.forEach(src => {
            const img = document.createElement("img");
            img.src = src;
            img.className = "result-img";
            div.appendChild(img);
        });
    } catch (err) {
        status.textContent = "Something went wrong during OCR search.";
        console.error(err);
    }
}
