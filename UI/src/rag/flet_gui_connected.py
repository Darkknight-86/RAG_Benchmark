import flet as ft
import requests
import time
import csv
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Gateway URL
API_BASE_URL = "http://localhost:8000/api"

def call_api_gateway(prompt):
    """Call the API Gateway query endpoint and return response with timing."""
    try:
        # Make the API call with environment variables
        response = requests.post(
            f"{API_BASE_URL}/query",
            json={
                "query": prompt,
                "temperature": float(os.getenv("DEFAULT_TEMPERATURE", "0.7")),
                "max_tokens": int(os.getenv("DEFAULT_MAX_TOKENS", "200")),
                "top_k": int(os.getenv("DEFAULT_TOP_K", "5"))
            },
            headers={"Content-Type": "application/json"},
            timeout=90
        )

        if response.status_code == 200:
            data = response.json()

            # Extract response text
            response_text = data.get("response", "No response received")

            # Extract metrics from API Gateway
            metrics = data.get("metrics", {})
            vector_latency = metrics.get("vector_latency", 0)
            llm_latency = metrics.get("llm_latency", 0)
            total_time = metrics.get("total_time", 0)
            tokens_used = metrics.get("tokens_used", 0)
            model_name = metrics.get("model_name", "unknown")
            temperature = metrics.get("temperature", 0)
            max_tokens = metrics.get("max_tokens", 0)
            top_k = metrics.get("top_k", 0)

            # Extract sources
            sources = data.get("sources", [])

            # Format the response with sources only
            if sources:
                response_text += "\n\n--- Sources ---\n"
                for i, source in enumerate(sources, 1):
                    response_text += f"\n{i}. Score: {source.get('score', 'N/A')}\n"
                    response_text += f"   Content: {source.get('content', 'N/A')[:200]}...\n"

            return response_text, vector_latency, llm_latency, total_time, tokens_used, model_name, temperature, max_tokens, top_k

        else:
            error_msg = f"API Error: {response.status_code}"
            if response.text:
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('error', response.text)}"
                except:
                    error_msg += f" - {response.text}"
            return error_msg, 0, 0, 0, 0, "unknown", 0, 0, 0

    except requests.exceptions.Timeout:
        return "Error: Request timed out", 0, 0, 0, 0, "unknown", 0, 0, 0
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to API Gateway. Is it running?", 0, 0, 0, 0, "unknown", 0, 0, 0
    except Exception as e:
        return f"Error: {str(e)}", 0, 0, 0, 0, "unknown", 0, 0, 0

def main(page: ft.Page):
    print("Starting application...")
    page.title = "Vectra - RAG System UI"
    page.bgcolor = "white"
    page.padding = 30
    page.vertical_alignment = ft.MainAxisAlignment.START

    # --- Components ---
    response_list = ft.ListView(
        expand=True,
        spacing=10,
        padding=10,
        auto_scroll=True
    )

    status_text = ft.Text("Status: Checking connection...", size=12, color="grey")
    latency_text = ft.Text("", size=12, color="grey")

    def check_api_connection():
        """Check if API Gateway is accessible."""
        try:
            print("Checking API connection...")
            response = requests.get(f"{API_BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print("API Gateway is accessible")
                status_text.value = "Status: Connected to API Gateway ✓"
                status_text.color = "green"
            else:
                print(f"API Gateway returned status code: {response.status_code}")
                status_text.value = "Status: API Gateway error"
                status_text.color = "red"
        except Exception as e:
            print(f"Error connecting to API Gateway: {str(e)}")
            status_text.value = "Status: Cannot connect to API Gateway ✗"
            status_text.color = "red"
        page.update()

    def query_ai(e=None):
        prompt = query_input.value.strip()
        if not prompt:
            return

        # User message
        response_list.controls.append(ft.Text("You", size=12, italic=True, color="#001F3F"))
        response_list.controls.append(ft.Container(
            content=ft.Text(prompt, size=14, selectable=True, color="#001F3F"),
            bgcolor="#d1c4e9",  # Light purple
            padding=10,
            border_radius=8
        ))

        # Call the API
        response, vector_latency, llm_latency, total_time, tokens, model_name, temperature, max_tokens, top_k = call_api_gateway(prompt)

        # AI response
        response_list.controls.append(ft.Text("Vectra", size=12, italic=True, color="#001F3F"))
        response_list.controls.append(ft.Container(
            content=ft.Text(response, size=14, selectable=True, color="#001F3F"),
            bgcolor="#f2f2f2",  # Light gray
            padding=10,
            border_radius=8
        ))

        # Update metrics display with model info
        latency_text.value = (
            f"Model: {model_name} | "
            f"Vector: {vector_latency:.3f}s | "
            f"LLM: {llm_latency:.3f}s | "
            f"Total: {total_time:.3f}s | "
            f"Tokens: {tokens}"
        )

        query_input.value = ""
        page.update()

    def export_metrics(e=None):
        """Export metrics from API Gateway."""
        try:
            response = requests.get(f"{API_BASE_URL}/metrics/export")
            if response.status_code == 200:
                data = response.json()
                latency_text.value = f"Exported to {data['filepath']}"
            else:
                latency_text.value = "Error exporting metrics"
        except Exception as e:
            latency_text.value = f"Error: {str(e)}"
        page.update()

    def clear_chat(e=None):
        response_list.controls.clear()
        latency_text.value = ""
        page.update()

    # --- Dialog Pop up Setup ---
    info_dialog = ft.AlertDialog(
        modal=True,
        bgcolor="#806491",
        title=ft.Text("Welcome to Vectra!", size=20, weight=ft.FontWeight.W_500, color="white"),
        content=ft.Container(
            content=ft.Text(
                spans=[
                    ft.TextSpan(
                        text="Vectra is a research tool that uses AI to provide answers through "
                            "Retrieval-Augmented Generation (RAG). It shows real-time metrics for "
                            "vector database and LLM performance!\n\n⭐Ask Vectra any question to "
                            "see how it works ⭐",
                        style=ft.TextStyle(color="white", weight=ft.FontWeight.W_200, size=14)
                    )
                ]
            ),
            bgcolor="#806491",
            border=ft.border.all(2, "#806491"),
            border_radius=10,
            padding=0
        ),
        actions=[
            ft.TextButton(
                "Let's Go!",
                on_click=lambda e: close_dialog(),
                style=ft.ButtonStyle(
                    bgcolor="white",
                    color="black",
                    overlay_color="#EAEAEA",
                    shape=ft.RoundedRectangleBorder(radius=8),
                ),
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def show_info_dialog(e=None):
        info_dialog.open = True
        page.update()

    def close_dialog():
        info_dialog.open = False
        page.update()

    # Add dialog to page overlay
    page.overlay.append(info_dialog)

    # --- UI Layout ---
    # Banner and Title
    title = ft.Text("Vectra RAG System", size=32, weight=ft.FontWeight.BOLD, color="white")
    banner = ft.Container(
        content=title,
        alignment=ft.alignment.center,
        bgcolor="#806491",
        padding=30,
        border_radius=10
    )

    # Query Input
    query_input = ft.TextField(
        label="Enter your query...",
        border_radius=10,
        border_color="#CCCCCC",
        color="#001F3F",
        expand=True,
        on_submit=query_ai,
        suffix=ft.IconButton(
            icon="info_outline",
            icon_color="white",
            icon_size=17,
            width=33,
            bgcolor="#000000",
            on_click=show_info_dialog,
            style=ft.ButtonStyle(shape=ft.CircleBorder())
        )
    )

    ask_button = ft.ElevatedButton(
        "↑",
        on_click=query_ai,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            bgcolor="#001F3F",
            color="white"
        )
    )

    input_row = ft.Row([
        query_input,
        ask_button
    ], spacing=10)

    # Bottom Buttons
    export_button = ft.ElevatedButton(
        "Export Metrics",
        on_click=export_metrics,
        style=ft.ButtonStyle(bgcolor="#001F3F", color="white")
    )
    clear_button = ft.OutlinedButton("Clear Chat", on_click=clear_chat)

    button_row = ft.Row([
        export_button,
        clear_button
    ], spacing=20, alignment=ft.MainAxisAlignment.START)

    # Page Layout
    page.add(
        banner,
        ft.Divider(height=20, color="transparent"),
        status_text,
        input_row,
        ft.Container(content=response_list, expand=True, border_radius=10, bgcolor="#ffffff"),
        latency_text,
        button_row
    )

    # Check API connection on startup
    check_api_connection()
    # Show info dialog on first load
    show_info_dialog()

ft.app(target=main)