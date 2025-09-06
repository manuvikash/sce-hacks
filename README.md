# 📘 Doc Mint

Doc Mint is an **AI-powered developer tool** that generates **production-ready API documentation** directly from a GitHub repository.  
Give it a repo URL, and Doc Mint automatically analyzes the codebase, detects frameworks, extracts endpoints, and produces an **OpenAPI 3.0 specification** — which can be used with [Mintlify](https://mintlify.com), Swagger UI, Postman, or any other OpenAPI-compatible documentation platform.

This project was originally prototyped at **SCE Hacks (SJSU)** where it won 🥉 3rd place, and is now being actively developed into a full-featured tool.

---

## ✨ Features
- 🚀 **Automatic API Docs** – Generate a complete OpenAPI 3.0 JSON from a GitHub repo URL.  
- 🧠 **Agentic LLM Pipeline** – AI-guided analysis that understands repo structure, detects frameworks, and extracts routes.  
- 🔍 **Dynamic Route Parsing** – Uses custom regex and code analysis to discover API endpoints automatically.  
- 📄 **OpenAPI Integration** – Outputs standards-compliant specs usable with Swagger, Postman, Mintlify, or any API docs platform.  
- ⚡ **Fast Setup** – Works with minimal configuration, no manual annotation required.  

---

## 🛠️ How It Works
1. **Input** – Provide a GitHub repository URL.  
2. **Repo Fetching** – Uses GitHub’s API (Octokit) to fetch code and directory structure.  
3. **Framework Detection** – Identifies frameworks (Express, Flask, FastAPI, etc.) based on repo analysis.  
4. **Endpoint Extraction** – Generates regex rules to detect routes and handlers.  
5. **Agentic LLM Processing** – An LLM parses code, reasons about endpoints, and assembles documentation.  
6. **OpenAPI Output** – Produces a valid OpenAPI 3.0 JSON file.  
7. **Docs Integration** – Feed the spec into Mintlify, Swagger UI, or Postman for live API documentation.  

---

## ⚙️ Tech Stack
- **Backend**: Node.js, Express  
- **AI/LLM**: OpenAI API / Gemini API (agentic reasoning pipeline)  
- **Repo Access**: GitHub API (Octokit)  
- **Documentation**: OpenAPI 3.0, Mintlify integration  
- **Other**: Regex-based static analysis, JSON streaming  

---

## 🚀 Getting Started

### Prerequisites
- Node.js (>=18)  
- GitHub Personal Access Token (for Octokit)  
- OpenAI API Key (or Gemini API key)  

### Installation
```bash
# Clone the repo
git clone https://github.com/manuvikash/sce-hacks.git
cd sce-hacks

# Install dependencies
npm install
```

### Run the Backend
```bash
# Set environment variables
export GITHUB_TOKEN=your_token_here
export OPENAI_API_KEY=your_key_here

# Start the development server
npm run dev
```

### Run the Frontend
```bash
npm run start
```

### Generate Docs
```bash
curl -X POST http://localhost:3000/generateDocs \
  -H "Content-Type: application/json" \
  -d '{"repoUrl": "https://github.com/username/repo"}'
```

---

## 🧭 Roadmap
We’re actively developing Doc Mint beyond its hackathon origins. Planned features include:
- ✅ Support for multiple frameworks (Express, Flask, FastAPI, Django REST)  
- ✅ Improved parameter and response type inference  
- 🔄 Local caching for faster repeated analysis  
- 🔄 Web UI for uploading repos or browsing docs  
- 🔄 Plugin system for custom analyzers  

---

## 🤝 Contributing
Contributions are welcome!  

1. Fork the repo  
2. Create your feature branch (`git checkout -b feature/your-feature`)  
3. Commit your changes (`git commit -m 'Add new feature'`)  
4. Push to the branch (`git push origin feature/your-feature`)  
5. Open a Pull Request  

Issues and feature requests can be submitted through the [GitHub Issues](../../issues) tab.  

---

## 👨‍💻 Authors
- [Manuvikash Saravanakumar](https://github.com/manuvikash)  
- [Satheesh Kumar G R](https://https://github.com/satheesh18)  

---

## 📜 License
MIT License – feel free to use, modify, and build upon Doc Mint.
