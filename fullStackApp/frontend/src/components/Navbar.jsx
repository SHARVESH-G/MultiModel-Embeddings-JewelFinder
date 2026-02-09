import React from "react";

const Navbar = () => {
  return (
    <nav className="navbar">
      <a href="/" className="nav-logo">Jewelry Finder</a>
      <div className="nav-links">
        <a href="/" className="nav-button">Home</a>
        <a href="/admin" className="nav-button">Admin</a>
      </div>
    </nav>
  );
};

export default Navbar;
