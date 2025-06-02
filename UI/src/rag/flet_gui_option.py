try:
    import flet as ft
except ImportError:
    print("Flet is not installed. Please run 'pip install flet' and try again.")
    exit(1)

from datetime import datetime
import time
import csv


def main(page: ft.Page):
    page.title = "Vectra"
    page.bgcolor = "white"
    page.padding = 30
    page.vertical_alignment = ft.MainAxisAlignment.START

    metrics_log = []

    # --- Components ---
    response_list = ft.ListView(
        expand=True,
        spacing=10,
        padding=10,
        auto_scroll=True
    )

    latency_text = ft.Text("", size=12, color="grey")

    def query_ai(e=None):
        prompt = query_input.value.strip()
        if not prompt:
            return

        now = datetime.now().strftime("%H:%M:%S")

        # User message
        response_list.controls.append(ft.Text("You", size=12, italic=True, color="gray"))
        response_list.controls.append(ft.Container(
            content=ft.Text(prompt, size=14, selectable=True),
            bgcolor="#d1c4e9",  # Light purple
            padding=10,
            border_radius=8
        ))

        # Simulated latency
        start_vector = time.time()
        time.sleep(0.1)
        vector_latency = time.time() - start_vector

        start_llm = time.time()
        time.sleep(0.2)
        response = f"You asked: '{prompt}'. This is a simulated AI response."
        llm_latency = time.time() - start_llm

        total_time = vector_latency + llm_latency

        response_list.controls.append(ft.Text("Vectra", size=12, italic=True, color="gray"))
        response_list.controls.append(ft.Container(
            content=ft.Text(response, size=14, selectable=True),
            bgcolor="#f2f2f2",  # Light gray
            padding=10,
            border_radius=8
        ))

        metrics_log.append((prompt, response, vector_latency, llm_latency, total_time))
        latency_text.value = (
            f"Vector DB Latency: {vector_latency:.2f}s | "
            f"LLM Latency: {llm_latency:.2f}s | Total Time: {total_time:.2f}s"
        )

        query_input.value = ""
        page.update()

    def export_csv(e=None):
        if not metrics_log:
            latency_text.value = "No data to export."
            page.update()
            return

        with open("metrics_log.csv", mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Prompt", "Response", "Vector Latency", "LLM Latency", "Total Time"])
            writer.writerows(metrics_log)

        latency_text.value = "Exported to metrics_log.csv"
        page.update()

    def clear_chat(e=None):
        response_list.controls.clear()
        latency_text.value = ""
        page.update()



    # --- Dialog Pop up Setup ---
    info_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("About Vectra", size=18, weight=ft.FontWeight.NORMAL, color="white"),
        content=ft.Container(
            content=ft.Text(
                "Vectra is a research tool that simulates how AI uses external data to improve answers "
                "through Retrieval-Augmented Generation (RAG). It shows how long it takes to fetch "
                "and respond using vector databases!\n\n"
                "Type a question asking Vectra about economics to receive a response!",
                color="white",
                size=14,
            ),
            bgcolor="#806491",  # Dark purple background
            padding=20,
            border_radius=10,
        ),
        actions=[
            ft.TextButton(
                "Let's Go!",
                on_click=lambda e: close_dialog(),
                style=ft.ButtonStyle(
                    bgcolor="#806491",
                    color="white",
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
    title = ft.Text("Vectra", size=32, weight=ft.FontWeight.BOLD, color="white")
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
        expand=True,
        on_submit=query_ai,
        suffix=ft.IconButton(
            icon="info_outline",
            icon_color="white",
            bgcolor="#000000",
            on_click=show_info_dialog,
            style=ft.ButtonStyle(shape=ft.CircleBorder())
        )
    )

    ask_button = ft.ElevatedButton(
        "↵",
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
    run_button = ft.ElevatedButton("Run Metrics", on_click=query_ai, style=ft.ButtonStyle(bgcolor="#001F3F", color="white"))
    export_button = ft.ElevatedButton("Export to CSV", on_click=export_csv, style=ft.ButtonStyle(bgcolor="#001F3F", color="white"))
    clear_button = ft.OutlinedButton("Clear Chat", on_click=clear_chat)

    button_row = ft.Row([
        run_button,
        export_button,
        clear_button
    ], spacing=20, alignment=ft.MainAxisAlignment.START)

    # Page Layout
    page.add(
        banner,
        ft.Divider(height=20, color="transparent"),
        input_row,
        ft.Container(content=response_list, expand=True, border_radius=10, bgcolor="#ffffff"),
        latency_text,
        button_row
    )


ft.app(target=main)
