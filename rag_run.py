import os
import json
import time
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
from dotenv import load_dotenv
from upstash_vector import Index
from groq import Groq

# Load environment variables
load_dotenv()

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(SCRIPT_DIR, "foods.json")
LLM_MODEL = "llama-3.1-8b-instant"
GROQ_RATE_LIMIT_WAIT = 1  # seconds between requests if rate limited

# Load data
with open(JSON_FILE, "r", encoding="utf-8") as f:
    food_data = json.load(f)

# Setup Upstash Vector
try:
    vector_index = Index(
        url=os.getenv("UPSTASH_VECTOR_REST_URL"),
        token=os.getenv("UPSTASH_VECTOR_REST_TOKEN"),
    )
    print("[OK] Connected to Upstash Vector")
except Exception as e:
    print(f"[ERROR] Failed to initialize Upstash Vector: {e}")
    print("Please ensure UPSTASH_VECTOR_REST_URL and UPSTASH_VECTOR_REST_TOKEN are set in .env")
    vector_index = None

# Setup Groq LLM Client
try:
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    print("[OK] Groq client initialized")
except Exception as e:
    print(f"[ERROR] Failed to initialize Groq client: {e}")
    print("Please ensure GROQ_API_KEY is set in .env")
    groq_client = None

# Initialize food data in vector database
def initialize_vector_db():
    """Upsert all food items to Upstash Vector (embeddings are automatic)"""
    if not vector_index:
        print("[ERROR] Vector database not available")
        return False
    
    print(f"[INFO] Preparing {len(food_data)} food items...")
    
    vectors_to_upsert = []
    for item in food_data:
        # Enhance text with region/type (same as before)
        enriched_text = item["text"]
        if "region" in item:
            enriched_text += f" This food is popular in {item['region']}."
        if "type" in item:
            enriched_text += f" It is a type of {item['type']}."
        
        # Prepare for Upstash (raw text, no embedding needed)
        vectors_to_upsert.append({
            "id": item["id"],
            "text": enriched_text,
            "metadata": {
                "original_id": item["id"],
                "region": item.get("region", "Unknown"),
                "type": item.get("type", "Unknown"),
            }
        })
    
    try:
        vector_index.upsert(vectors_to_upsert)
        print(f"[OK] Upserted {len(vectors_to_upsert)} items to Upstash Vector")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to upsert to Upstash Vector: {e}")
        return False

# Initialize vector database with food data
initialize_vector_db()

# Note: Ollama is no longer needed
print("[INFO] Ollama has been replaced with Groq Cloud API for LLM generation")
print("[INFO] Embeddings are handled by Upstash Vector automatically")
print("=" * 60)

# RAG query function
def rag_query(question, gui_callback=None):
    """Query the RAG system using Upstash Vector and Groq LLM."""
    try:
        if not vector_index:
            raise Exception("ERROR: Vector database not initialized")
        
        if not groq_client:
            raise Exception("ERROR: Groq client not initialized. Check GROQ_API_KEY in .env")

        # Step 1: Query Upstash Vector with raw text (embedding done server-side)
        results = vector_index.query(
            data=question,
            top_k=3,
            include_metadata=True
        )

        # Step 2: Extract documents from Upstash response format
        top_docs = [r["text"] for r in results]
        top_ids = [r["id"] for r in results]
        top_scores = [r["score"] for r in results]

        # Step 3: Display retrieved documents in GUI
        sources_text = "[SOURCES & RELEVANCE]\n"
        for i, (doc, score) in enumerate(zip(top_docs, top_scores)):
            sources_text += f"\n[{i + 1}] (Relevance: {score:.2f})\n    {doc}\n"
        
        if gui_callback:
            gui_callback("sources", sources_text)

        # Step 4: Build prompt from context
        context = "\n".join(top_docs)
        user_message = f"""Use the following context to answer the question.

Context:
{context}

Question: {question}
Answer:"""

        # Step 5: Query Groq with streaming
        try:
            stream = groq_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful food expert. Answer questions about food based on the provided context."
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                temperature=0.7,
                max_tokens=1024,
                stream=True,
                stop=None
            )
        except Exception as e:
            if "401" in str(e):
                raise Exception("ERROR: Invalid Groq API key. Check GROQ_API_KEY in .env")
            elif "429" in str(e):
                raise Exception("ERROR: Groq API rate limited. Please wait before retrying.")
            elif "503" in str(e):
                raise Exception("ERROR: Groq API temporarily unavailable. Please try again.")
            else:
                raise Exception(f"ERROR: Groq API error: {str(e)}")

        # Step 6: Stream response and update GUI
        full_response = ""
        if gui_callback:
            gui_callback("answer_start", "")
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                if gui_callback:
                    gui_callback("answer_update", content)
        
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
        self.root.title("RAG Food Q&A - Upstash + Groq")
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
