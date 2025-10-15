import os
import sys
import socket
from urllib.parse import quote

DOWNLOAD_DIR = "downloads"

def save_file(filename: str, data: bytes) -> str:
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    # strip any path parts coming from the request
    base = os.path.basename(filename) or "downloaded_file"
    out_path = os.path.join(DOWNLOAD_DIR, base)
    with open(out_path, "wb") as f:
        f.write(data)
    return out_path

def recv_all(sock: socket.socket) -> bytes:
    chunks = []
    while True:
        buf = sock.recv(4096)
        if not buf:
            break
        chunks.append(buf)
    return b"".join(chunks)

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 client.py <host> <port> <path-or-file>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    req_path = sys.argv[3]

    # Ensure leading slash for the request path
    if not req_path.startswith("/"):
        req_path = "/" + req_path

    # Build HTTP/1.1 request; ask the server to close after response
    request = (
        f"GET {quote(req_path)} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).encode("ascii")

    # Connect and send
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(request)

        raw = recv_all(s)

    # Split headers/body
    sep = b"\r\n\r\n"
    pos = raw.find(sep)
    if pos == -1:
        sep = b"\n\n"
        pos = raw.find(sep)
    if pos == -1:
        print("Malformed HTTP response: no header/body separator")
        sys.exit(2)

    header_bytes = raw[:pos]
    body = raw[pos + len(sep):]

    # Decode headers and gather into a dict (case-insensitive)
    header_lines = header_bytes.decode("iso-8859-1", errors="replace").splitlines()
    status_line = header_lines[0] if header_lines else "HTTP/1.1 ???"
    print(status_line)

    headers = {}
    for line in header_lines[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()

    content_type = headers.get("content-type", "application/octet-stream").lower()

    # If not 200, just print the body as text so you see the error page
    if not status_line.startswith("HTTP/1.1 200"):
        try:
            print(body.decode("utf-8", errors="replace"))
        except Exception:
            pass
        return

    # Handle by content-type
    if content_type.startswith("text/html"):
        # Print HTML to stdout
        print(body.decode("utf-8", errors="replace"))
    elif content_type.startswith("image/png") or content_type.startswith("application/pdf"):
        out = save_file(req_path, body)
        print(f"Saved to {out}")
    else:
        # Default: save unknown types
        out = save_file(req_path, body)
        print(f"Saved (type: {content_type}) to {out}")

if __name__ == "__main__":
    main()
