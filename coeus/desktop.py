def main():
    from coeus.server import background
    url = background(4371)
    try:
        import webview
    except ImportError:
        print(f"The window library is not installed. Open {url}")
        return
    webview.create_window("Coeus", url, width=1100, height=760, background_color="#04181C")
    webview.start()
