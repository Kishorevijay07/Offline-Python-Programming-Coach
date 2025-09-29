// src/App.jsx
import React, { useState, useEffect, useRef } from "react";
import "./App.css";

function App() {
  const [code, setCode] = useState("");
  const [reasoning, setReasoning] = useState("");
  const [debugOutput, setDebugOutput] = useState("");
  const [loading, setLoading] = useState(false);
  const [typingTimeout, setTypingTimeout] = useState(null);

  const editorRef = useRef(null);

  // Auto-send reasoning (debounced)
  useEffect(() => {
    if (!code.trim()) {
      setReasoning("");
      return;
    }
    if (typingTimeout) clearTimeout(typingTimeout);
    const timeout = setTimeout(() => {
      fetchReasoning(code);
    }, 800);
    setTypingTimeout(timeout);
    return () => clearTimeout(timeout);
  }, [code]);

  const fetchReasoning = async (codeText) => {
    try {
      const res = await fetch("http://localhost:5000/reasoning", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: codeText }),
      });
      const data = await res.json();
      setReasoning(data.reasoning || "No reasoning provided.");
    } catch {
      setReasoning("Error fetching reasoning.");
    }
  };

  const handleDebug = async () => {
    if (!code.trim()) return;
    setLoading(true);
    try {
      const res = await fetch("http://localhost:5000/debug", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code }),
      });
      const data = await res.json();
      setDebugOutput(data.output || "No output.");
    } catch {
      setDebugOutput("Error fetching debug output.");
    } finally {
      setLoading(false);
    }
  };

  // --- Auto indent & tab handler ---
  const handleKeyDown = (e) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const textarea = editorRef.current;
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const newValue = code.substring(0, start) + "    " + code.substring(end);
      setCode(newValue);
      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd = start + 4;
      }, 0);
    }

    if (e.key === "Enter") {
      const textarea = editorRef.current;
      const start = textarea.selectionStart;
      const beforeCursor = code.substring(0, start);
      const lineStart = beforeCursor.lastIndexOf("\n") + 1;
      const currentLine = beforeCursor.substring(lineStart);
      const indentMatch = currentLine.match(/^\s*/);
      let indent = indentMatch ? indentMatch[0] : "";

      // If line ends with ':', add extra indent
      if (currentLine.trim().endsWith(":")) {
        indent += "    ";
      }

      e.preventDefault();
      const newValue =
        code.substring(0, start) + "\n" + indent + code.substring(start);
      setCode(newValue);
      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd =
          start + 1 + indent.length;
      }, 0);
    }
  };

  return (
    <div className="app">
      <div className="editor-section">
        <div className="editor-header">
          <h2>Python Code Editor</h2>
          <button onClick={handleDebug} disabled={loading}>
            ▶ Run Debug
          </button>
        </div>
        <textarea
          ref={editorRef}
          className="editor"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Write your Python code here..."
        />
      </div>

      <div className="output-section">
        <div className="reasoning">
          <h3>💡 Reasoning (auto updates)</h3>
          <pre>{reasoning}</pre>
        </div>
        <div className="debug">
          <h3>🐞 Debug Output</h3>
          <pre>{debugOutput}</pre>
        </div>
      </div>
    </div>
  );
}

export default App;
