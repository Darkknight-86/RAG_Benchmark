import tkinter as tk
from tkinter import scrolledtext, messagebox
import time
import csv
import os
import requests
import json
from datetime import datetime

from ttkbootstrap import Style
from ttkbootstrap.widgets import Entry, Button, Label, Frame

# API Gateway URL
API_BASE_URL = "http://localhost:8000/api"

# Helper to make API calls
def call_api_gateway(prompt):
    """Call the API Gateway query endpoint and return response with timing."""
    start_time = time.time()

    try:
        # Make the API call
        response = requests.post(
            f"{API_BASE_URL}/query",
            json={"query": prompt, "top_k": 5},
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        total_time = time.time() - start_time

        if response.status_code == 200:
            data = response.json()

            # Extract response text
            response_text = data.get("response", "No response received")

            # Extract metadata
            metadata = data.get("metadata", {})
            vector_latency = metadata.get("latency", 0)
            tokens_used = metadata.get("tokens_used", 0)

            # Extract sources
            sources = data.get("sources", [])

            # Format the response with sources
            if sources:
                response_text += "\n\n--- Sources ---\n"
                for i, source in enumerate(sources, 1):
                    response_text += f"\n{i}. Score: {source.get('score', 'N/A')}\n"
                    response_text += f"   Content: {source.get('content', 'N/A')[:200]}...\n"

            return response_text, vector_latency, total_time - vector_latency, total_time, tokens_used

        else:
            error_msg = f"API Error: {response.status_code}"
            if response.text:
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('error', response.text)}"
                except:
                    error_msg += f" - {response.text}"
            return error_msg, 0, 0, total_time, 0

    except requests.exceptions.Timeout:
        return "Error: Request timed out", 0, 0, time.time() - start_time, 0
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to API Gateway. Is it running?", 0, 0, time.time() - start_time, 0
    except Exception as e:
        return f"Error: {str(e)}", 0, 0, time.time() - start_time, 0

# Helper to add placeholder to ttkbootstrap Entry
def add_placeholder_to_entry(entry_widget, placeholder_text):
    def on_focus_in(event):
        if entry_widget.get() == placeholder_text:
            entry_widget.delete(0, "end")
            entry_widget.config(foreground="black")

    def on_focus_out(event):
        if entry_widget.get() == "":
            entry_widget.insert(0, placeholder_text)
            entry_widget.config(foreground="gray")

    entry_widget.insert(0, placeholder_text)
    entry_widget.config(foreground="gray")
    entry_widget.bind("<FocusIn>", on_focus_in)
    entry_widget.bind("<FocusOut>", on_focus_out)

# Main Application
class AIQueryApp:
    def __init__(self, root):
        self.root = root
        root.title("Vectra - RAG System UI")
        root.geometry("850x650")
        root.configure(bg="white")

        self.metrics_log = []

        # Top banner
        self.banner = Frame(root, style="Custom.TFrame", height=150)
        self.banner.pack(fill="x", side="top")

        self.title_label = Label(
            self.banner, text="Vectra RAG System", style="CustomInverse.TLabel",
            font=("Verdana", 20, "bold")
        )
        self.title_label.pack(pady=30)

        # Status indicator
        self.status_frame = Frame(root, style="WhiteBg.TFrame")
        self.status_frame.pack(fill="x", padx=20, pady=(10, 0))

        self.status_label = Label(
            self.status_frame, text="Status: Checking connection...",
            style="Status.TLabel", font=("Helvetica", 10)
        )
        self.status_label.pack(side="left")

        # Check API connection on startup
        self.check_api_connection()

        # Input frame
        input_frame = Frame(root, style="WhiteBg.TFrame")
        input_frame.pack(fill="x", padx=20, pady=20)

        self.query_entry = Entry(input_frame, font=("Verdana", 10), style="Custom.TEntry")
        self.query_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        add_placeholder_to_entry(self.query_entry, "Enter your query...")
        self.query_entry.bind("<Return>", lambda event: self.query_ai())

        self.ask_button = Button(
            input_frame, text="Ask", command=self.query_ai,
            style="AskButton.TButton", width=6
        )
        self.ask_button.pack(side="left", padx=(10, 0))

        # Response Area
        self.response_area = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, width=95, height=15,
            bg="lavender", fg="slate blue", font=("Helvetica", 11),
            insertbackground="white"
        )
        self.response_area.pack(pady=10, padx=20)

        # Metrics label
        self.metrics_label = Label(
            root, text="", font=("Helvetica", 10),
            style="CustomInversePrimary.TLabel"
        )
        self.metrics_label.pack(pady=5)

        # Button frame
        btn_frame = Frame(root, style="WhiteBg.TFrame")
        btn_frame.pack(pady=10)

        self.export_button = Button(
            btn_frame, text="Export to CSV", command=self.export_csv,
            style="Custom.TButton", width=15
        )
        self.export_button.pack()

    def check_api_connection(self):
        """Check if API Gateway is accessible."""
        try:
            print("Checking API connection...")
            response = requests.get(f"{API_BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print("API Gateway is accessible")
                self.status_label.config(text="Status: Connected to API Gateway ✓", foreground="green")
            else:
                print(f"API Gateway returned status code: {response.status_code}")
                self.status_label.config(text="Status: API Gateway error", foreground="red")
        except Exception as e:
            print(f"Error connecting to API Gateway: {str(e)}")
            self.status_label.config(text="Status: Cannot connect to API Gateway ✗", foreground="red")

    def query_ai(self):
        prompt = self.query_entry.get().strip()
        if not prompt or prompt == "Enter your query...":
            self.response_area.delete('1.0', tk.END)
            self.response_area.insert(tk.END, "Please enter a query.")
            self.metrics_label.config(text="")
            return

        # Update UI to show processing
        self.response_area.delete('1.0', tk.END)
        self.response_area.insert(tk.END, "Processing query...")
        self.root.update()

        # Call the API
        response, vector_latency, llm_latency, total_time, tokens = call_api_gateway(prompt)

        # Display response
        self.response_area.delete('1.0', tk.END)
        self.response_area.insert(tk.END, response)

        # Log metrics
        self.metrics_log.append({
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response[:200] + "..." if len(response) > 200 else response,
            "vector_latency": vector_latency,
            "llm_latency": llm_latency,
            "total_time": total_time,
            "tokens_used": tokens
        })

        # Update metrics display
        self.metrics_label.config(
            text=f"Vector Latency: {vector_latency:.3f}s | LLM Latency: {llm_latency:.3f}s | Total: {total_time:.3f}s | Tokens: {tokens}"
        )

    def export_csv(self):
        if not self.metrics_log:
            messagebox.showinfo("No Data", "There are no metrics to export.")
            return

        filename = f"rag_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, mode="w", newline="") as file:
            fieldnames = ["timestamp", "prompt", "response", "vector_latency", "llm_latency", "total_time", "tokens_used"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.metrics_log)

        messagebox.showinfo("Exported", f"Metrics exported to {filename}")
        self.metrics_log.clear()

if __name__ == "__main__":
    print("Starting application...")
    root = tk.Tk()
    print("Creating style...")
    style = Style(theme="cosmo")

    # Configure custom styles
    style.configure("Custom.TButton",
                    font=("Helvetica", 11, "bold"),
                    foreground="white",
                    background="#2F70AF",
                    bordercolor="#00457E",
                    focusthickness=3,
                    focuscolor="#00457E",
                    padding=10)

    style.configure("Custom.TEntry",
                    foreground="black",
                    fieldbackground="white",
                    bordercolor="#806491",
                    font=("Verdana", 10),
                    padding=5)

    style.configure("Custom.TFrame", background="#806491")
    style.configure("WhiteBg.TFrame", background="white")
    style.configure("CustomInverse.TLabel", background="#806491", foreground="white")
    style.configure("CustomInversePrimary.TLabel", background="white", foreground="#444444")
    style.configure("Status.TLabel", background="white")

    style.configure("AskButton.TButton",
                    font=("Helvetica", 12, "bold"),
                    foreground="white",
                    background="#02315E",
                    bordercolor="#02315E",
                    focusthickness=3,
                    focuscolor="white",
                    padding=10)

    print("Initializing app...")
    app = AIQueryApp(root)
    print("Starting main loop...")
    root.lift()  # Lift window to the front
    root.attributes('-topmost', True)  # Make window stay on top
    root.after_idle(root.attributes, '-topmost', False)  # Allow other windows to come to front after
    root.mainloop()