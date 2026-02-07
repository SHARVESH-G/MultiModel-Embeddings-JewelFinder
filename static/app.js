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
    }
}
