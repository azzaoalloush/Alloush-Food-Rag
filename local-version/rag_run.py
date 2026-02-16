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
try:
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        food_data = json.load(f)
except UnicodeDecodeError:
    # Fallback encoding if UTF-8 fails
    with open(JSON_FILE, "r", encoding="latin-1") as f:
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
    """Verify all food items are in Upstash Vector (embeddings are automatic per BGE model)"""
    if not vector_index:
        print("[ERROR] Vector database not available")
        return False
    
    try:
        # Check current index status
        info = vector_index.info()
        vector_count = info.vector_count if hasattr(info, 'vector_count') else 0
        
        if vector_count == 0:
            print(f"[INFO] Vector DB is empty. Ingesting {len(food_data)} food items...")
            
            vectors_to_upsert = []
            for i, item in enumerate(food_data):
                # Enhance text with region/type for better semantic search
                enriched_text = item.get("text", "")
                if "region" in item:
                    enriched_text += f" This food is popular in {item['region']}."
                if "type" in item:
                    enriched_text += f" It is a type of {item['type']}."
                
                # Use 'data' for auto-embedding, store text in metadata for retrieval
                vectors_to_upsert.append({
                    "id": str(i),
                    "data": enriched_text,  # Upstash will auto-embed this
                    "metadata": {
                        "text": enriched_text,  # Store original text for retrieval
                        "original_id": item.get("id", str(i))
                    }
                })
            
            # Upsert in batches
            batch_size = 10
            for batch_idx in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[batch_idx:batch_idx + batch_size]
                vector_index.upsert(vectors=batch)
            
            print(f"[OK] Ingested {len(vectors_to_upsert)} items to Upstash Vector")
            return True
        else:
            print(f"[OK] Vector DB has {vector_count} vectors ready")
            return True
    except Exception as e:
        print(f"[ERROR] Vector DB initialization: {e}")
        return False

# Initialize vector database with food data
initialize_vector_db()

# Note: Ollama is no longer needed
print("[INFO] Ollama has been replaced with Groq Cloud API for LLM generation")
print("[INFO] Embeddings are handled by Upstash Vector automatically")
print("=" * 60)

# RAG query function
def rag_query(question, gui_callback=None):
    """Query the RAG system using Upstash Vector and Groq LLM with fallback support."""
    try:
        if not groq_client:
            raise Exception("Groq client not initialized. Check GROQ_API_KEY in .env")

        # Step 1: Try to retrieve context from Vector DB, fallback to direct search if auth fails
        context = None
        use_vector_db = False
        
        if vector_index:
            try:
                results = vector_index.query(
                    data=question,
                    top_k=3,
                    include_metadata=True
                )
                
                if results and len(results) > 0:
                    top_docs = []
                    top_scores = []
                    
                    # Extract text from QueryResult objects by using ID to look up food_data
                    for r in results:
                        try:
                            # Get text from food_data using the ID
                            result_id = int(r.id) if hasattr(r, 'id') else None
                            if result_id is not None and result_id < len(food_data):
                                food_item = food_data[result_id]
                                text = food_item.get("text", "")
                                if "region" in food_item:
                                    text += f" This food is popular in {food_item['region']}."
                                if "type" in food_item:
                                    text += f" It is a type of {food_item['type']}."
                                
                                top_docs.append(text)
                                score = getattr(r, 'score', 0)
                                top_scores.append(score)
                        except (ValueError, IndexError, KeyError, TypeError):
                            continue
                    
                    if top_docs:
                        # Display sources
                        sources_text = "[SOURCES & RELEVANCE]\n"
                        for i, (doc, score) in enumerate(zip(top_docs, top_scores)):
                            sources_text += f"\n[{i + 1}] (Relevance: {score:.2f})\n    {doc[:100]}...\n"
                        
                        if gui_callback:
                            gui_callback("sources", sources_text)
                        
                        context = "\n".join(top_docs)
                        use_vector_db = True
                    
            except Exception as vector_err:
                # Vector DB query error - fallback to keyword search
                error_msg = str(vector_err)
                if "Unauthorized" in error_msg:
                    if gui_callback:
                        sources_msg = "[SOURCES] Vector DB authentication failed.\nUsing keyword matching from food database.\n"
                        gui_callback("sources", sources_msg)
                else:
                    if gui_callback:
                        gui_callback("sources", f"[INFO] Using keyword matching (Vector query: {error_msg[:80]}...)\n")
        
        # Step 2: If no Vector DB context, use fallback from food_data
        if not context:
            # Simple keyword-based fallback context from food_data
            question_lower = question.lower()
            matching_foods = []
            
            for food in food_data[:10]:  # Use first 10 items as base context
                text_lower = food.get("text", "").lower()
                if any(word in text_lower for word in question_lower.split()):
                    matching_foods.append(food["text"])
            
            if not matching_foods:
                # Use random selection if no keyword match
                matching_foods = [food["text"] for food in food_data[:5]]
            
            context = "\n".join(matching_foods[:3])
        
        # Step 3: Build message for Groq
        user_message = f"""Use the following food knowledge to answer the question. Be helpful and accurate.

Food Knowledge:
{context}

Question: {question}
Answer:"""

        # Step 4: Query Groq with streaming
        try:
            stream = groq_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful and knowledgeable food expert. Provide accurate, concise answers about food."
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
        except Exception as groq_err:
            error_text = str(groq_err)
            if "401" in error_text:
                raise Exception("Invalid Groq API key. Check GROQ_API_KEY in .env")
            elif "429" in error_text:
                raise Exception("Groq API rate limited. Please wait before retrying.")
            elif "503" in error_text:
                raise Exception("Groq API temporarily unavailable. Please try again.")
            else:
                raise Exception(f"Groq API error: {error_text}")

        # Step 5: Stream response and update GUI
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
        error_msg = str(e)
        if gui_callback:
            gui_callback("error", f"[ERROR] {error_msg}")
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
