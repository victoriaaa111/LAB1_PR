import sys, socket, os
from urllib.parse import quote


def save_file(filename: str, data: bytes):
    os.makedirs("downloads", exist_ok=True)
    out_path = os.path.join("downloads", os.path.basename(filename))
    with open(out_path, "wb") as f:
        f.write(data)
    print(f"Saved to {out_path}")


def main():
    if len(sys.argv) != 4:
        print("Usage: python client.py <server_host> <server_port> <filename>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    filename = sys.argv[3]

    request_path = "/" + quote(filename.lstrip("/"))

    # open TCP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))

    request = f"GET {request_path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
    s.sendall(request.encode("utf-8"))

    response = b""
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        response += chunk
    s.close()

    # split headers and body
    header_bytes, _, body = response.partition(b"\r\n\r\n")
    headers = header_bytes.decode(errors="replace").split("\r\n")
    status_line = headers[0]
    header_dict = {}
    for h in headers[1:]:
        if ":" in h:
            k, v = h.split(":", 1)
            header_dict[k.strip().lower()] = v.strip()

    print(status_line)
    if "content-type" not in header_dict:
        print("No Content-Type in response")
        return

    content_type = header_dict["content-type"]

    if content_type.startswith("text/html"):
        # print HTML as text
        print(body.decode("utf-8", errors="replace"))
    elif content_type in ("application/pdf", "image/png"):
        save_file(filename, body)
    else:
        print(f"Unhandled Content-Type: {content_type}")


if __name__ == "__main__":
    main()
