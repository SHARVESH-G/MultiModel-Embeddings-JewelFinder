// LoginPage.jsx
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { logins } from "../data.js"; // your login array

const LoginPage = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");
  const navigate = useNavigate();

  // If already logged in, redirect to admin
  useEffect(() => {
    if (localStorage.getItem("isLoggedIn") === "true") {
      navigate("/admin");
    }
  }, [navigate]);

  const handleLogin = (e) => {
    e.preventDefault();
    const user = logins.find(
      (u) => u.username === username && u.password === password
    );

    if (user) {
      localStorage.setItem("isLoggedIn", "true"); // mark as logged in
      setMsg("✅ Login successful!");
      setTimeout(() => navigate("/admin"), 500);
    } else {
      setMsg("❌ Invalid username or password.");
    }
  };

  return (
    <div className="container">
      <h2 className="title">Admin Login</h2>
      <p className="subtitle">Enter credentials to access admin panel</p>

      <form onSubmit={handleLogin} className="upload-section">
        <div className="input-wrapper">
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <label>Username</label>
        </div>

        <div className="input-wrapper">
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <label>Password</label>
        </div>

        <button type="submit">Login</button>
        {msg && <p className="status">{msg}</p>}
      </form>
    </div>
  );
};

export default LoginPage;
