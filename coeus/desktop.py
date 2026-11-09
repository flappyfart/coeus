def main():
    from coeus import __version__
    from coeus.server import background, start_watch
    url = background(4371)
    start_watch()
    try:
        import webview
    except ImportError:
        print(f"The window library is not installed. Open {url}")
        return
    webview.create_window(f"Coeus {__version__}", url, width=1180, height=800, background_color="#04181C")
    webview.start()
