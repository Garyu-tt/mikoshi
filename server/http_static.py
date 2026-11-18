"""CSP-constrained read-only IDE client asset handler."""


def send_static(handler, root, name, mime):
    data = (root / 'client' / name).read_bytes()
    handler.send_response(200)
    handler.send_header('Content-Type', mime)
    handler.send_header('Content-Security-Policy',
        "default-src 'self'; connect-src 'self'; script-src 'self'; style-src 'self'")
    handler.send_header('X-Content-Type-Options', 'nosniff')
    handler.send_header('Content-Length', str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)
