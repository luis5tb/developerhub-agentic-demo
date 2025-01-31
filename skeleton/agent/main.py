from ui import create_ui

if __name__ == "__main__":
    # Create and launch the Gradio UI
    ui = create_ui()
    # ui.launch(server_name="0.0.0.0", server_port=8080)
    # Use queue to fix the issue with 30 seconds timeout
    ui.queue(api_open=False).launch(server_name="0.0.0.0", server_port=8080)