# 🧠 RAG-Food: Simple Retrieval-Augmented Generation with ChromaDB + Ollama

## 📝 Latest Updates & Features

### ✨ New Features Added
- ✅ **Secure Credential Management**: `.env` file for storing username and email (kept private via .gitignore)
- ✅ **Enhanced GUI**: Improved Tkinter interface with real-time streaming responses
- ✅ **Comprehensive Documentation**: Added screenshots and visual documentation in `/Documentation` folder
- ✅ **Updated Credentials**: Project now maintained by azzaoalloush (azzaoalloush@gmail.com)
- ✅ **Improved Error Handling**: Better connection and timeout error messages for Ollama
- ✅ **Source Attribution**: Retrieved documents are displayed with IDs for transparency

---

## 🔧 Project Overview

This is a **minimal working RAG (Retrieval-Augmented Generation)** demo using:

- ✅ Local LLM via [Ollama](https://ollama.com/)
- ✅ Local embeddings via `mxbai-embed-large`
- ✅ [ChromaDB](https://www.trychroma.com/) as the vector database
- ✅ A simple food dataset in JSON (Indian foods, fruits, etc.)

---

## 🎯 What This Does

This app allows you to ask questions like:

- “Which Indian dish uses chickpeas?”
- “What dessert is made from milk and soaked in syrup?”
- “What is masala dosa made of?”

It **does not rely on the LLM’s built-in memory**. Instead, it:

1. **Embeds your custom text data** (about food) using `mxbai-embed-large`
2. Stores those embeddings in **ChromaDB**
3. For any question, it:
   - Embeds your question
   - Finds relevant context via similarity search
   - Passes that context + question to a local LLM (`llama3.2`)
4. Returns a natural-language answer grounded in your data.

---

## 📦 Requirements

### ✅ Software

- Python 3.8+
- Ollama installed and running locally
- ChromaDB installed

### ✅ Ollama Models Needed

Run these in your terminal to install them:

```bash
ollama pull llama3.2
ollama pull mxbai-embed-large
````

> Make sure `ollama` is running in the background. You can test it with:
>
> ```bash
> ollama run llama3.2
> ```

---

## 🛠️ Installation & Setup

### 1. Clone this repository

```bash
git clone https://github.com/azzaoalloush/Alloush-Food-Rag.git
cd Alloush-Food-Rag
```

### 2. Set up credentials (Optional)

Create a `.env` file in the project root with your credentials:

```
USERNAME=azzaoalloush
EMAIL=azzaoalloush@gmail.com
```

> Note: The `.env` file is ignored by git for security purposes.

### 3. Install Python dependencies

```bash
pip install chromadb requests
```

### 4. Run the RAG app

```bash
python rag_run.py
```

**First-time setup will:**
- Load food data from `foods.json` (90+ international dishes)
- Generate embeddings for all food items using `mxbai-embed-large`
- Store embeddings in ChromaDB persistent database
- Launch an interactive Tkinter GUI

---

## 📁 Project Structure

```
Alloush-Food-Rag/
├── rag_run.py              # Main application with Tkinter GUI
├── foods.json              # Comprehensive food knowledge base (90+ items)
├── .env                    # Credentials file (git-ignored)
├── README.md               # This file
├── chroma_db/              # Vector database storage
│   └── chroma.sqlite3      # ChromaDB persistent storage
└── Documentation/          # Screenshots and visual guides
    └── *.png               # GUI screenshots and usage examples
```

---

## 🧠 How It Works (Step-by-Step)

1. **Data Loading**: Foods data is loaded from `foods.json` (international cuisine database)
2. **Text Enrichment**: Each food item is enhanced with region and type metadata
3. **Embedding**: Text is embedded using Ollama's `mxbai-embed-large` model
4. **Storage**: Embeddings are persisted in ChromaDB
5. **Query Processing**: When you ask a question:
   - Question is embedded using the same model
   - Top 3 most relevant food items are retrieved via similarity search
   - Retrieved sources are displayed in the GUI
   - Context + question is sent to `llama3.2` LLM
   - Response is streamed in real-time to the GUI

### GUI Features
- **Question Input**: Enter natural language questions
- **Retrieved Sources**: View the top 3 matching documents with IDs
- **Real-time Streaming**: Answers appear as they're generated
- **Error Handling**: Clear error messages if Ollama is not running

---

## 🔍 Example Questions to Try

The system is trained on diverse international cuisines. Try asking:

**About Indian Food:**
- "Which Indian dish uses chickpeas?"
- "What is tandoori chicken?"
- "What is Masala Dosa filled with?"

**About Other Cuisines:**
- "What is Pad Thai made of?"
- "Tell me about Sushi"
- "What is Peking duck?"

**Nutritional & Health:**
- "What foods are high in protein?"
- "Which dishes contain seafood?"
- "What vegetarian options are available?"

**Geographic Queries:**
- "What Japanese dishes do you know?"
- "Tell me about Thai cuisine"
- "What are some Middle Eastern dishes?"

---

## 🚀 Future Enhancements

- [ ] Add web UI using Flask or Gradio
- [ ] Expand food database with recipes and nutritional info
- [ ] Implement embedding caching to improve performance
- [ ] Support for PDF/document uploads as data sources
- [ ] Multi-language support for international queries
- [ ] Docker containerization for easy deployment
- [ ] Database export functionality
- [ ] Advanced filtering by cuisine type, dietary restrictions, etc.

---

## 🛠️ Troubleshooting

### Ollama Connection Error
```
[ERROR] Ollama is not running at http://localhost:11434
```
**Solution**: Start Ollama with `ollama serve` in a terminal

### Model Not Found Error
```
ERROR: Failed to get embedding from Ollama
```
**Solution**: Ensure models are installed:
```bash
ollama pull llama3.2
ollama pull mxbai-embed-large
```

### ChromaDB Errors
- Clear the `chroma_db/` folder and restart the app to rebuild the database

---

## � About This Project

This project demonstrates a practical implementation of **Retrieval-Augmented Generation (RAG)**, combining local LLMs with vector databases for contextually accurate responses. It's designed to be:

- **Privacy-focused**: All processing happens locally
- **Lightweight**: Minimal dependencies, easy to modify
- **Extensible**: Can be adapted to any domain with new JSON data

## 👨‍💻 Credits & Acknowledgments

**Maintained by:** azzaoalloush (azzaoalloush@gmail.com)

**Built with:**
- [Ollama](https://ollama.com) - Local LLM runtime
- [ChromaDB](https://www.trychroma.com) - Vector database
- [mxbai-embed-large](https://ollama.com/library/mxbai-embed-large) - Embedding model
- [llama3.2](https://ollama.com/library/llama3.2) - LLM model
- Python Tkinter - GUI framework

**Food Data Inspiration:** 🍛 International cuisine databases and culinary traditions from 🌍 around the world

---

## 📜 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs or issues
- Suggest improvements or new features
- Submit pull requests with enhancements
- Share feedback or documentation improvements

---

**Last Updated:** February 8, 2026

