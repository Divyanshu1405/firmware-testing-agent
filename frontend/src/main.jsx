import React from "react";
import { createRoot } from "react-dom/client";

function App() {
  return (
    <main style={{ fontFamily: "sans-serif", padding: 32 }}>
      <h1>PS3 Firmware Testing Agent</h1>
      <p>Bare-bones frontend. Connect to the FastAPI backend next.</p>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
