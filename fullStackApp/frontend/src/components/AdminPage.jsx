import React, { useState } from "react";

const AdminPage = () => {
  const [file, setFile] = useState(null);
  const [msg, setMsg] = useState("");

  const upload = async () => {
    if (!file) return setMsg("Please select a file first!");
    const formData = new FormData();
    formData.append("file", file);
    setMsg("Uploading...");
    try {
      const res = await fetch("http://127.0.0.1:8000/admin/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setMsg(`✅ Uploaded to ${data.metal} folder`);
      setFile(null);
    } catch (err) {
      console.error(err);
      setMsg("❌ Upload failed. Try again.");
    }
  };

  return (
    <div className="container">
      <h2 className="title">Admin Panel</h2>
      <p className="subtitle">Upload new jewelry items</p>

      <div className="upload-section">
        <div className="upload-card">
          <input
            type="file"
            onChange={(e) => setFile(e.target.files[0])}
            id="fileInput"
          />
          <label htmlFor="fileInput">Select Jewelry Image</label>
          <button onClick={upload}>Upload</button>
          {msg && <p className="status">{msg}</p>}
        </div>
      </div>
    </div>
  );
};

export default AdminPage;
