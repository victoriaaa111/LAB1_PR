import os
import socket
import mimetypes
import sys
from urllib.parse import unquote, quote
import datetime

PORT = int(os.environ.get("PORT", "8000"))
ALLOWED_EXTENSIONS = {".html", ".png", ".pdf"}


def file_size(num_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} TB"


def respond(conn, status, headers, body):
    head = [f"HTTP/1.1 {status}".encode()]
    for k, v in headers.items():
        head.append(f"{k}: {v}".encode())
    head.append(b"")
    head.append(b"")
    conn.sendall(b"\r\n".join(head) + body)


def _is_subpath(child: str, parent: str) -> bool:
    child_real = os.path.realpath(child)
    parent_real = os.path.realpath(parent)
    try:
        return os.path.commonpath([child_real, parent_real]) == parent_real
    except ValueError:
        return False


def _minimal_listing_html(req_path: str, abs_dir: str) -> bytes:
    try:
        entries = sorted(os.listdir(abs_dir))
    except OSError:
        return b"<html><body><h1>Forbidden</h1></body></html>"

    lines = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "<meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<link rel='preconnect' href='https://fonts.googleapis.com'>",
        "<link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>",
        "<link href='https://fonts.googleapis.com/css2?family=Pixelify+Sans:wght@400;700&display=swap' rel='stylesheet'>",
        f"<title>Content of {req_path}</title>",
        "<style>",
        ":root{--bg:#EFD8D6;--card:#F7F3ED;--text:#422B23;--muted:#955A5C;--link:#8B3C46;--row:#EFD8D6;--border:#EFD8D6}",
        "*{box-sizing:border-box}",
        "body{margin:0;padding:28px 16px;background:var(--bg);color:var(--text);",
        "     font:14px/1.5 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif}",
        "header{max-width:960px;margin:0 auto 12px}",
        "h1{margin:0 0 8px;font-size:20px;font-weight:600}",
        "main{max-width:960px;margin:0 auto;background:var(--card);border-radius:14px;",
        "     padding:8px;box-shadow:0 8px 24px rgba(0,0,0,.18)}",
        "table{width:100%;border-collapse:separate;border-spacing:0;overflow:hidden}",
        "thead th{position:sticky;top:0;background:var(--card);border-bottom:1px solid var(--border);",
        "         text-align:left;font-weight:600;color:var(--muted);padding:12px 14px}",
        "tbody tr{background:var(--row)}",
        "tbody tr:nth-child(even){background:transparent}",
        "td{padding:10px 14px;border-bottom:1px solid var(--border)}",
        "a{color:var(--link);text-decoration:none}",
        "a:hover{text-decoration:underline}",
        "tr.dir td:first-child a::before{content:'📁  '}",
        "tr.file td:first-child a::before{content:'📄  '}",
        "tr.up   td:first-child a::before{content:'⬆  '}",
        "td:nth-child(2),td:nth-child(3){color:var(--muted);white-space:nowrap}",
        "@media (max-width: 640px){ thead th:nth-child(3), td:nth-child(3){display:none} }",
        ".parent-link{margin-bottom:8px; margin-top:8px; display:block;font-weight:600}",
        ".title-lab{font-family:'Pixelify Sans', sans-serif; color: #DBA1A2; font-size: 64px; margin-bottom: 16px; margin-top: 4px;}",
        ".center-title{display:flex; text-align: center; align-items: center; justify-content: center;}",
        "</style>",
        "</head>",
        "<body>",
        "<header>",
        "<div class='center-title'>",
        f"<h1 class='title-lab'>Victoria's 1st PR LAB</h1>"
        "</div>",
        f"<h1>Content of {req_path}</h1>",
        "</header>",
        "<main>",
    ]

    # Add parent directory link outside the table
    if req_path != "/":
        parent = req_path.rstrip("/").rsplit("/", 1)[0]
        parent = "/" if not parent else parent + "/"
        lines.append(f'<a class="parent-link" href="{quote(parent)}">⬆ Parent directory</a>')

    # Add the table
    lines.extend([
        "<table>",
        "<thead><tr><th>Name</th><th>Size</th><th>Last modified</th></tr></thead>",
        "<tbody>"
    ])

    for name in entries:
        full = os.path.join(abs_dir, name)
        if os.path.isdir(full):
            href = quote(name) + "/"
            row_class = "dir"
            size = "—"
        else:
            ext = os.path.splitext(name)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                continue
            href = quote(name)
            row_class = "file"
            size = file_size(os.path.getsize(full))

        ts = os.path.getmtime(full)
        mtime = datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M UTC")

        lines.append(
            f'<tr class="{row_class}">'
            f'<td><a href="{href}">{name if not os.path.isdir(full) else name + "/"}</a></td>'
            f"<td>{size}</td><td>{mtime}</td>"
            f"</tr>"
        )

    lines.append("</tbody></table></main></body></html>")
    return "\n".join(lines).encode("utf-8")

def _respond_301(conn, location: str):
    body = (f"<html><body>Moved: <a href=\"{location}\">{location}</a></body></html>").encode("utf-8")
    respond(conn, "301 Moved Permanently",
            {"Location": location,
             "Content-Type": "text/html; charset=utf-8",
             "Content-Length": str(len(body)),
             "Connection": "close"},
            body)


def _respond_404(conn):
    body = b"<html><body><h1>404 Not Found</h1></body></html>"
    respond(conn, "404 Not Found",
            {"Content-Type": "text/html; charset=utf-8",
             "Content-Length": str(len(body)),
             "Connection": "close"},
            body)


def main():
    if len(sys.argv) != 2:
        print("Usage: python server.py <directory>")
        sys.exit(1)

    root_dir = sys.argv[1]
    if not os.path.isdir(root_dir):
        print(f"Error: Directory '{root_dir}' does not exist.")
        sys.exit(1)

    root_dir = os.path.abspath(root_dir)
    print(f"Serving directory: {root_dir}")

    # creates new tcp socket with IPv4 and TCP
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # allows restart without "Address already in use"
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", PORT))
    # handles one client at a time
    s.listen(1)
    print(f"Server running on http://0.0.0.0:{PORT}")
    print(f"Access locally: http://localhost:{PORT}")
    print(f"Press Ctrl+C to stop")

    while True:
        # returns a conn socket and client's address
        conn, addr = s.accept()
        print(f"Connection from {addr}")
        try:
            data = conn.recv(4096)
            line = data.split(b"\r\n", 1)[0].decode(errors="replace")
            print(f"Request: {line}")
            parts = line.split()
            if len(parts) != 3:
                respond(
                        conn,
                        "400 Bad Request",
                        {
                            "Content-Type": "text/plain",
                            "Connection": "close"
                        },
                        b"Bad Request"
                )
                continue
            method, target, version = parts
            if method != "GET":
                respond(conn, "405 Method Not Allowed",
                        {"Allow": "GET",
                         "Content-Type": "text/plain",
                         "Connection": "close"},
                        b"Only GET is allowed")
                continue

            # ensure URL path starts with "/"
            if not target.startswith("/"):
                target = "/"

            # decode URL encoded characters
            target = unquote(target)
            # map URL to relative path under root
            if target == "/":
                requested_rel = ""  # root directory
            else:
                requested_rel = target.lstrip("/")

            requested_abs = os.path.realpath(os.path.join(root_dir, requested_rel))

            # 1) reject traversal
            if not _is_subpath(requested_abs, root_dir):
                _respond_404(conn)
                continue

            # 2) if it's a directory
            if os.path.isdir(requested_abs):
                # enforce trailing slash for directories
                if not target.endswith("/"):
                    _respond_301(conn, target + "/")
                    continue

                # always show listing
                body = _minimal_listing_html(target, requested_abs)
                respond(conn, "200 OK",
                        {"Content-Type": "text/html; charset=utf-8",
                         "Content-Length": str(len(body)),
                         "Connection": "close"},
                        body)
                continue

            # 3) regular file flow
            ext = os.path.splitext(requested_abs)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                _respond_404(conn)
                continue

            if not os.path.isfile(requested_abs):
                _respond_404(conn)
                continue

            mime_type, _ = mimetypes.guess_type(requested_abs)
            if mime_type is None:
                _respond_404(conn)
                continue

            try:
                with open(requested_abs, "rb") as f:
                    body = f.read()
                respond(conn, "200 OK",
                        {"Content-Type": mime_type,
                         "Content-Length": str(len(body)),
                         "Connection": "close"},
                        body)
                print(f"Served: {requested_rel} ({mime_type})")
            except OSError:
                respond(conn, "500 Internal Server Error",
                        {"Content-Type": "text/plain",
                         "Connection": "close"},
                        b"Internal Server Error")

        except Exception as e:
            print(f"Error handling request: {e}")
        finally:
            conn.close()


if __name__ == "__main__":
    main()