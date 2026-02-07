async function searchImages(e) {
    e.preventDefault();

    const query = document.getElementById("searchInput").value;
    const div = document.getElementById("results");

    div.innerHTML = "Searching...";

    const res = await fetch("/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query })
    });

    const data = await res.json();

    div.innerHTML = "";

    if (!data.images || data.images.length === 0) {
        div.innerHTML = "No matches 😢";
        return;
    }

    data.images.forEach(src => {
        const img = document.createElement("img");
        img.src = src;
        img.className = "result-img";
        div.appendChild(img);
    });
}
