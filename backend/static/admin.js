async function upload() {

    const file = document.getElementById("fileInput").files[0];
    const msg = document.getElementById("msg");

    if (!file) return;

    const form = new FormData();
    form.append("file", file);

    msg.innerText = "Uploading...";

    const res = await fetch("/admin/upload", {
        method: "POST",
        body: form
    });

    const data = await res.json();

    msg.innerText = `Saved to ${data.metal} folder ✅`;
}
