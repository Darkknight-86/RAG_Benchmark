import tkinter as tk
from tkinter import scrolledtext, messagebox
import time, csv, os

from ttkbootstrap import Style
from ttkbootstrap.widgets import Entry, Button, Label, Frame

# Simulated response with latency tracking
def get_ai_response_with_latency(prompt):
    start_vector = time.time()
    time.sleep(0.1)  # Simulated vector DB delay
    vector_latency = time.time() - start_vector

    start_llm = time.time()
    response = f"You asked: '{prompt}'. This is a simulated AI response."
    time.sleep(0.2)  # Simulated LLM delay
    llm_latency = time.time() - start_llm

    total_time = vector_latency + llm_latency
    return response, vector_latency, llm_latency, total_time

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
        root.title("Vectra")
        root.geometry("750x550")
        root.configure(bg="white")
        
        self.metrics_log = []

        # Top banner (custom purple secondary color)
        self.banner = Frame(root, style="Custom.TFrame", height=150)
        self.banner.pack(fill="x", side="top")

        self.title_label = Label(
            self.banner, text="Vectra", style="CustomInverse.TLabel",
            font=("Verdana", 20, "bold")
        )
        self.title_label.pack(pady=30)

        # Input frame holds query entry (left) and Ask AI button (right)
        input_frame = Frame(root, style="WhiteBg.TFrame")
        input_frame.pack(fill="x", padx=20, pady=20)

        self.query_entry = Entry(input_frame, font=("Verdana", 10), style="Custom.TEntry")
        self.query_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Add placeholder text to the query entry
        add_placeholder_to_entry(self.query_entry, "Enter your query...")

        # Bind Enter key to submit the query
        self.query_entry.bind("<Return>", lambda event: self.query_ai())

        self.ask_button = Button(
            input_frame, text="^", command=self.query_ai,
            style="AskButton.TButton", width=4
        )
        self.ask_button.pack(side="left", padx=(10, 0))

        # Response Area (manually styled)
        self.response_area = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, width=85, height=10,
            bg="lavender", fg="slate blue", font=("Helvetica", 11),
            insertbackground="white"
        )
        self.response_area.pack(pady=10)

        # Metrics label (custom inverse primary style)
        self.metrics_label = Label(
            root, text="", font=("Helvetica", 10),
            style="CustomInversePrimary.TLabel"
        )
        self.metrics_label.pack(pady=5)

        # Button frame (custom primary color)
        btn_frame = Frame(root, style="WhiteBg.TFrame")
        btn_frame.pack(pady=10)

        self.run_button = Button(
            btn_frame, text="Run Metrics", command=self.run_metrics,
            style="Custom.TButton", width=15
        )
        self.run_button.grid(row=0, column=0, padx=10)

        self.export_button = Button(
            btn_frame, text="Export to CSV", command=self.export_csv,
            style="Custom.TButton", width=15
        )
        self.export_button.grid(row=0, column=1, padx=10)

    def query_ai(self):
        prompt = self.query_entry.get().strip()
        if not prompt or prompt == "Enter your query...":
            self.response_area.delete('1.0', tk.END)
            self.response_area.insert(tk.END, "Please enter a query.")
            self.metrics_label.config(text="")
            return

        response, vector_latency, llm_latency, total_time = get_ai_response_with_latency(prompt)
        self.response_area.delete('1.0', tk.END)
        self.response_area.insert(tk.END, response)

        self.metrics_log.append((prompt, response, vector_latency, llm_latency, total_time))
        self.metrics_label.config(
            text=f"Vector DB Latency: {vector_latency:.3f}s | LLM Latency: {llm_latency:.3f}s | Total Time: {total_time:.3f}s"
        )

    def run_metrics(self):
        self.query_ai()

    def export_csv(self):
        if not self.metrics_log:
            messagebox.showinfo("No Data", "There are no metrics to export.")
            return

        file_exists = os.path.isfile("metrics_log.csv")
        with open("metrics_log.csv", mode="a", newline="") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Prompt", "Response", "Vector Latency (s)", "LLM Latency (s)", "Total Time (s)"])
            writer.writerows(self.metrics_log)

        messagebox.showinfo("Exported", "Metrics exported to metrics_log.csv")
        self.metrics_log.clear()

# Run the app
if __name__ == "__main__":
    style = Style("flatly")

    # Define your custom colors/styles here
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

    style.configure("Custom.TFrame", background="#806491")  # banner
    style.configure("WhiteBg.TFrame", background="white")   # white sections
    style.configure("CustomInverse.TLabel", background="#806491", foreground="white")  # banner title
    style.configure("CustomInversePrimary.TLabel", background="white", foreground="#444444")  # latency

    # Custom style for Ask AI button with background #02315E
    style.configure("AskButton.TButton",
                    font=("Helvetica", 14, "normal"),
                    foreground="white",
                    background="#02315E",
                    bordercolor="#02315E",
                    focusthickness=3,
                    focuscolor="white",
                    padding=10)

    root = style.master
    app = AIQueryApp(root)
    root.mainloop()
