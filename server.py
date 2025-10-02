import os, socket
PORT = int(os.environ.get("PORT", "8000"))


def main():
    # creates new tcp socket with IPv4 and TCP
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # allows restart without "Address already in use"
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", PORT))
    # handles one client at a time
    s.listen(1)
    print(f"Listening on http://0.0.0.0: {PORT}")


    while True:
        # returns a conn socket and client's address
        conn, addr = s.accept()
        try:
            _ = conn.recv(4096)
            # ignore request for now
            body = b"VICTORIA's first PR LAB"
            headers = [
                b"HTTP/1.1 200 OK",
                b"Content-Type: text/plain; charset=utf-8",
                f"Content-Length: {len(body)}".encode(),
                b"Connection: close",
                b"",
                b""
            ]
            conn.sendall(b"\r\n".join(headers)+body)
        finally:
            conn.close()

if __name__ == "__main__":
    main()
