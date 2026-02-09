import React, { useState } from "react";

const SearchPage = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [status, setStatus] = useState("");
  const [imageFile, setImageFile] = useState(null);
  const [activeTab, setActiveTab] = useState("text");

  // Text search
  const searchImages = async (e) => {
    e.preventDefault();
    if (!query) return;
    setResults([]);
    setStatus("🔎 Searching...");
    try {
      const res = await fetch("http://127.0.0.1:8000/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      if (!data.images || data.images.length === 0) {
        setStatus("No matches found 😢");
        return;
      }
      setResults(data.images.slice(0, 8));
      setStatus("");
    } catch (err) {
      console.error(err);
      setStatus("Something went wrong. Try again.");
    }
  };

  // Image OCR search
  const searchByImage = async () => {
    if (!imageFile) return alert("Select an image first!");
    setResults([]);
    setStatus("🔎 Extracting text from image...");
    const formData = new FormData();
    formData.append("file", imageFile);

    try {
      const res = await fetch("http://127.0.0.1:8000/search/image", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setStatus(`OCR detected: "${data.query}"`);
      if (!data.images || data.images.length === 0) {
        setStatus((prev) => prev + " — No matches found 😢");
        return;
      }
      setResults(data.images.slice(0, 8));
    } catch (err) {
      console.error(err);
      setStatus("Something went wrong during OCR search.");
    }
  };

  return (
    <div className="container">
      <h2 className="title">Jewelry Finder</h2>
      <p className="subtitle">Search jewelry by text or image</p>

      {/* Tab Switch */}
      <div className="tabs">
        <button
          className={activeTab === "text" ? "active" : ""}
          onClick={() => setActiveTab("text")}
        >
          Text Search
        </button>
        <button
          className={activeTab === "image" ? "active" : ""}
          onClick={() => setActiveTab("image")}
        >
          Image Search
        </button>
      </div>

      {/* TEXT SEARCH */}
      {activeTab === "text" && (
        <form className="search-bar" onSubmit={searchImages}>
          <div className="input-wrapper">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <label>Search Jewelry</label>
          </div>
          <button type="submit">Search</button>
        </form>
      )}

      {/* IMAGE SEARCH */}
      {activeTab === "image" && (
        <div className="image-search">
          <div className="input-wrapper">
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setImageFile(e.target.files[0])}
            />
          </div>

          {/* PREVIEW */}
          {imageFile && (
            <div className="image-preview">
              <p>Preview:</p>
              <img
                src={URL.createObjectURL(imageFile)}
                alt="Preview"
                style={{
                  maxWidth: "200px",
                  maxHeight: "200px",
                  marginTop: "10px",
                }}
              />
            </div>
          )}

          <button onClick={searchByImage}>Search</button>
        </div>
      )}

      {/* STATUS */}
      {status && <p className="status">{status}</p>}

      {/* RESULTS */}
      <div className="results-grid">
        {results.map((src, idx) => (
          <div key={idx} className="jewelry-card">
            <img
              src={`http://127.0.0.1:8000${src}`}
              alt={`Result ${idx + 1}`}
              className="result-img"
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default SearchPage;
