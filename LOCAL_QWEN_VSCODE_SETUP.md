# Local Qwen Coding Assistant Setup in VS Code

This guide outlines how to configure **VS Code** with the **Continue** extension to leverage your local **Ollama** server and the state-of-the-art **Qwen2.5-Coder** model for offline agentic coding, autocomplete, and chat.

---

## 1. Prerequisites (Ollama Setup)

Your local Ollama instance is serving at `http://localhost:11434` (or host IP `10.0.0.193`).
To download the optimized coding and search models, run the following commands in your shell:

```bash
# Pull the standard coder model (ideal for file edits & coding chat)
ollama pull qwen2.5-coder:7b

# Pull the lightweight autocomplete model (ideal for inline ghost text as you type)
ollama pull qwen2.5-coder:1.5b

# Pull the embeddings model (helps Continue index your workspace folder files)
ollama pull nomic-embed-text
```

---

## 2. VS Code Extension Installation

1. Open **VS Code**.
2. Click on the **Extensions** icon in the Activity Bar on the left side (`Ctrl + Shift + X`).
3. Search for **Continue** (published by `continue.dev`).
4. Click **Install**.

---

## 3. Continue Configuration

1. In VS Code, open the **Continue** sidebar panel (click the Continue icon on the left bar).
2. Click the **gear icon (Settings)** at the bottom-right corner of the Continue panel.
3. This opens `~/.continue/config.json`. Replace its contents with the configuration below:

```json
{
  "models": [
    {
      "title": "Qwen 2.5 Coder 7B",
      "provider": "ollama",
      "model": "qwen2.5-coder:7b"
    },
    {
      "title": "Qwen 3.6 27B (Strategic)",
      "provider": "ollama",
      "model": "qwen3.6:27b"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Qwen 2.5 Coder 1.5B (Autocomplete)",
    "provider": "ollama",
    "model": "qwen2.5-coder:1.5b"
  },
  "embeddingsProvider": {
    "provider": "ollama",
    "model": "nomic-embed-text"
  },
  "customCommands": [
    {
      "name": "refactor",
      "prompt": "Refactor the selected code to improve readability, performance, and structure.",
      "description": "Refactor selected code snippet"
    },
    {
      "name": "comment",
      "prompt": "Add clean docstrings and comments to the selected code.",
      "description": "Add comments to code"
    }
  ]
}
```

---

## 4. How to Use Continue

*   **Chat with your codebase (`Ctrl + L`)**:
    *   Opens a chat panel on the side.
    *   Type `@Files` or `@Codebase` to index and reference workspace files in your question.
    *   Example: *"@Codebase explain how the batch pipeline launches"*
*   **Inline Editing (`Ctrl + I`)**:
    *   Highlight a section of code in any editor file.
    *   Press `Ctrl + I`.
    *   Type your instruction (e.g. *"make this function safe with try-except, logging error"*).
    *   Accept/Reject the live diff directly in your editor.
*   **Ghost Text Autocomplete**:
    *   As you type, the lightweight `1.5b` model will instantly show gray text suggestions. Press `Tab` to accept.
