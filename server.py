import os, socket


PORT = int(os.environ.get("PORT", "8000"))
ROOT = os.environ.get("ROOT", "/app/public").rstrip("/")


def respond(conn, status, headers, body):
    head = [f"HTTP/1.1 {status}".encode()]
    for k, v in headers.items():
        head.append(f"{k}: {v}".encode())
    head.append(b"")
    head.append(b"")
    conn.sendall(b"\r\n".join(head) + body)


def main():
    # creates new tcp socket with IPv4 and TCP
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # allows restart without "Address already in use"
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", PORT))
    # handles one client at a time
    s.listen(1)
    print(f"Serving {ROOT} on http://0.0.0.0: {PORT}")

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
                respond(conn, "405 Method not allowed",
                        {"Allow": "GET",
                         "Content-Type": "text/plain",
                         "Connection": "close"},
                        b"Only GET is allowed")
                continue

            # for now serve only / or /index.html
            if target in ("/", "/index.html"):
                path = os.path.join(ROOT, "index.html")
                try:
                    with open(path, "rb") as f:
                        body = f.read()
                    respond(conn, "200 OK",
                            {"Content-Type": "text/html; charset=utf-8",
                             "Content-Length": str(len(body)),
                             "Connection": "close"},
                            body)
                except OSError:
                    respond(conn, "404 Not Found",
                            {"Content-Type": "text/html; charset=utf-8", "Connection": "close"},
                            b"<!doctype html><h1>404 Not Found</h1>"
                            )
            else:
                respond(conn, "404 Not Found",
                        {"Content-Type": "text/html; charset=utf-8", "Connection": "close"},
                        b"<!doctype html><h1>404 Not Found</h1>")

        finally:
            conn.close()


if __name__ == "__main__":
    main()
