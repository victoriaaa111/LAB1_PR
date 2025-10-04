import os
import socket
import mimetypes
import sys
from urllib.parse import unquote, quote


PORT = int(os.environ.get("PORT", "8000"))
ALLOWED_EXTENSIONS = {".html", ".png", ".pdf"}


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

    lines = [f"<h1>Content of {req_path}</h1>", "<ul>"]

    if req_path != "/":
        # parent link
        parent = req_path.rstrip("/").rsplit("/", 1)[0]
        if not parent:
            parent = "/"
        else:
            parent += "/"
        lines.append(f'<li><a href="{quote(parent)}">..</a></li>')

    for name in entries:
        full = os.path.join(abs_dir, name)
        if os.path.isdir(full):
            href = quote(name) + "/"   # keep slash for dirs
            lines.append(f'<li>📁 <a href="{href}">{name}/</a></li>')
        else:
            ext = os.path.splitext(name)[1].lower()
            if ext in ALLOWED_EXTENSIONS:
                href = quote(name)
                icon = "🌐" if ext == ".html" else ("🖼️" if ext == ".png" else "📄")
                lines.append(f'<li>{icon} <a href="{href}">{name}</a></li>')

    lines.append("</ul>")
    return ("<html><head><meta charset='utf-8'></head><body>" +
            "\n".join(lines) + "</body></html>").encode("utf-8")


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
        print("Using: python server.py directory")
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
    print(f"Serving {root_dir} on http://0.0.0.0: {PORT}")


    while True:
        # returns a conn socket and client's address
        conn, addr = s.accept()
        try:
            data = conn.recv(4096)
            line = data.split(b"\r\n", 1)[0].decode(errors="replace")
            parts = line.split()
            if len(parts) != 3:
                respond(
                        conn,
                        "400 BAD REQUEST",
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

            # decode URL-encoded characters
            target = unquote(target)
            # map URL to relative path under root
            if target == "/":
                requested_rel = ""  # root directory
            else:
                requested_rel = target.lstrip("/")

            requested_abs = os.path.realpath(os.path.join(root_dir, requested_rel))

            # 1) Reject traversal
            if not _is_subpath(requested_abs, root_dir):
                _respond_404(conn)
                continue

            # 2) If it's a directory
            if os.path.isdir(requested_abs):
                if not target.endswith("/"):
                    _respond_301(conn, target + "/")
                    continue

                if target == "/":
                    body = _minimal_listing_html(target, requested_abs)
                    respond(conn, "200 OK",
                            {"Content-Type": "text/html; charset=utf-8",
                             "Content-Length": str(len(body)),
                             "Connection": "close"},
                            body)
                    continue

                index_path = os.path.join(requested_abs, "index.html")
                if os.path.isfile(index_path):
                    try:
                        with open(index_path, "rb") as f:
                            body = f.read()
                        respond(conn, "200 OK",
                                {"Content-Type": "text/html; charset=utf-8",
                                 "Content-Length": str(len(body)),
                                 "Connection": "close"},
                                body)
                        continue
                    except OSError:
                        _respond_404(conn)
                        continue
                else:
                    body = _minimal_listing_html(target, requested_abs)
                    respond(conn, "200 OK",
                            {"Content-Type": "text/html; charset=utf-8",
                             "Content-Length": str(len(body)),
                             "Connection": "close"},
                            body)
                    continue

            # 3) Regular file flow (use requested_abs consistently)
            ext = os.path.splitext(requested_abs)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                respond(conn, "404 Not Found",
                        {"Content-Type": "text/html; charset=utf-8",
                         "Connection": "close"},
                        b"<!doctype html><h1>404 Not Found</h1>")
                continue

            if not os.path.isfile(requested_abs):
                respond(conn, "404 Not Found",
                        {"Content-Type": "text/html; charset=utf-8",
                         "Connection": "close"},
                        b"<!doctype html><h1>404 Not Found</h1>")
                continue

            mime_type, _ = mimetypes.guess_type(requested_abs)
            if mime_type is None:
                respond(conn, "404 Not Found",
                        {"Content-Type": "text/html; charset=utf-8",
                         "Connection": "close"},
                        b"<!doctype html><h1>404 Not Found</h1>")
                continue

            try:
                with open(requested_abs, "rb") as f:
                    body = f.read()
                respond(conn, "200 OK",
                        {"Content-Type": mime_type,
                         "Content-Length": str(len(body)),
                         "Connection": "close"},
                        body)
            except OSError:
                respond(conn, "500 Internal Server Error",
                        {"Content-Type": "text/plain",
                         "Connection": "close"},
                        b"Internal Server Error")

        finally:
            conn.close()


if __name__ == "__main__":
    main()
