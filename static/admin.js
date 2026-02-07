document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("uploadBtn");
    if (!btn) {
        console.error("Upload button not found!");
        return;
    }
    btn.addEventListener("click", upload);
    console.log("Upload button listener attached");
});

async function upload() {
    const fileInput = document.getElementById("fileInput");
    const msg = document.getElementById("msg");

    if (!fileInput.files.length) {
        msg.innerText = "Please select a file first!";
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);

    msg.innerText = "Uploading...";

    try {
        const res = await fetch("/admin/upload", {
            method: "POST",
            body: formData
        });

        if (!res.ok) throw new Error("Upload failed");

        const data = await res.json();
        msg.innerText = `✅ Uploaded to ${data.metal} folder`;
        fileInput.value = "";

    } catch (err) {
        console.error(err);
        msg.innerText = "❌ Upload failed. Try again.";
    }
}
