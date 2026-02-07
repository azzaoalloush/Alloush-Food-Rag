import os
import json
import chromadb
import requests
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(SCRIPT_DIR, "chroma_db")
COLLECTION_NAME = "foods"
JSON_FILE = os.path.join(SCRIPT_DIR, "foods.json")
EMBED_MODEL = "mxbai-embed-large"
LLM_MODEL = "llama3.2"

# Load data
with open(JSON_FILE, "r", encoding="utf-8") as f:
    food_data = json.load(f)

# Setup ChromaDB
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

# Ollama embedding function
def get_embedding(text):
    response = requests.post("http://localhost:11434/api/embeddings", json={
        "model": EMBED_MODEL,
        "prompt": text
    })
    return response.json()["embedding"]

# Add only new items
existing_ids = set(collection.get()['ids'])
new_items = [item for item in food_data if item['id'] not in existing_ids]

if new_items:
    print(f"[NEW] Adding {len(new_items)} new documents to Chroma...")
    
    # Batch process embeddings
    documents = []
    ids = []
    embeddings = []
    
    for item in new_items:
        # Enhance text with region/type
        enriched_text = item["text"]
        if "region" in item:
            enriched_text += f" This food is popular in {item['region']}."
        if "type" in item:
            enriched_text += f" It is a type of {item['type']}."
        
        emb = get_embedding(enriched_text)
        documents.append(item["text"])
        embeddings.append(emb)
        ids.append(item["id"])
    
    # Add all at once
    collection.add(
        documents=documents,
        embeddings=embeddings,
        ids=ids
    )
else:
    print("[OK] All documents already in ChromaDB.")

# RAG query function
def rag_query(question, gui_callback=None):
    """Query the RAG system and optionally update GUI with results."""
    try:
        # Step 1: Embed the user question
        q_emb = get_embedding(question)

        # Step 2: Query the vector DB
        results = collection.query(query_embeddings=[q_emb], n_results=3)

        # Step 3: Extract documents
        top_docs = results['documents'][0]
        top_ids = results['ids'][0]

        # Step 4: Display retrieved documents in GUI
        sources_text = "[SOURCES]\n"
        for i, doc in enumerate(top_docs):
            sources_text += f"\n[{i + 1}] ID: {top_ids[i]}\n    {doc}\n"
        
        if gui_callback:
            gui_callback("sources", sources_text)

        # Step 5: Build prompt from context
        context = "\n".join(top_docs)
        prompt = f"""Use the following context to answer the question.

Context:
{context}

Question: {question}
Answer:"""

        # Step 6: Generate answer with Ollama (streaming)
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": True
        }, stream=True, timeout=60)

        # Step 7: Stream response and update GUI
        full_response = ""
        if gui_callback:
            gui_callback("answer_start", "")
        
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    response_text = chunk.get("response", "")
                    full_response += response_text
                    if gui_callback:
                        gui_callback("answer_update", response_text)
                except json.JSONDecodeError:
                    continue
        
        return full_response.strip()
    
    except Exception as e:
        error_msg = f"[ERROR] {str(e)}"
        if gui_callback:
            gui_callback("error", error_msg)
        return ""


# Tkinter GUI
class RAGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RAG Food Q&A")
        self.root.geometry("1000x700")
        
        # Question input
        input_frame = tk.Frame(root)
        input_frame.pack(padx=10, pady=10, fill=tk.X)
        
        tk.Label(input_frame, text="Question:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.question_input = tk.Entry(input_frame, font=("Arial", 10))
        self.question_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.question_input.bind("<Return>", lambda e: self.ask_question())
        
        self.ask_btn = tk.Button(input_frame, text="Ask", command=self.ask_question, fg="white", bg="green")
        self.ask_btn.pack(side=tk.LEFT, padx=5)
        
        # Sources display
        tk.Label(root, text="Retrieved Sources:", font=("Arial", 9, "bold")).pack(anchor=tk.W, padx=10, pady=(5, 0))
        self.sources_text = scrolledtext.ScrolledText(root, height=8, font=("Courier", 9))
        self.sources_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=False)
        
        # Answer display
        tk.Label(root, text="Generated Answer:", font=("Arial", 9, "bold")).pack(anchor=tk.W, padx=10, pady=(5, 0))
        self.answer_text = scrolledtext.ScrolledText(root, height=12, font=("Courier", 9))
        self.answer_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        self.querying = False
    
    def update_gui(self, update_type, content):
        """Callback for updating GUI from RAG query."""
        if update_type == "sources":
            self.sources_text.config(state=tk.NORMAL)
            self.sources_text.delete(1.0, tk.END)
            self.sources_text.insert(tk.END, content)
            self.sources_text.config(state=tk.DISABLED)
        
        elif update_type == "answer_start":
            self.answer_text.config(state=tk.NORMAL)
            self.answer_text.delete(1.0, tk.END)
            self.answer_text.insert(tk.END, "[Generating answer...]\n")
        
        elif update_type == "answer_update":
            self.answer_text.config(state=tk.NORMAL)
            self.answer_text.insert(tk.END, content)
            self.answer_text.see(tk.END)
            self.answer_text.config(state=tk.DISABLED)
        
        elif update_type == "error":
            self.answer_text.config(state=tk.NORMAL)
            self.answer_text.delete(1.0, tk.END)
            self.answer_text.insert(tk.END, content)
            self.answer_text.config(state=tk.DISABLED)
        
        self.root.update()
    
    def ask_question(self):
        """Handle question submission."""
        question = self.question_input.get().strip()
        if not question:
            messagebox.showwarning("Empty Question", "Please enter a question.")
            return
        
        if self.querying:
            messagebox.showwarning("Busy", "Already processing a question.")
            return
        
        self.querying = True
        self.ask_btn.config(state=tk.DISABLED)
        self.sources_text.config(state=tk.NORMAL)
        self.sources_text.delete(1.0, tk.END)
        self.sources_text.insert(tk.END, "[Retrieving sources...]\n")
        self.sources_text.config(state=tk.DISABLED)
        
        # Run in background thread
        def query_thread():
            try:
                rag_query(question, gui_callback=self.update_gui)
            finally:
                self.querying = False
                self.ask_btn.config(state=tk.NORMAL)
        
        threading.Thread(target=query_thread, daemon=True).start()


# Launch GUI
if __name__ == "__main__":
    root = tk.Tk()
    gui = RAGUI(root)
    root.mainloop()
