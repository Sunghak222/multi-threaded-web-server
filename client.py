# Implements a simple HTTP client
import socket
import threading
from email.utils import formatdate
import os

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8000

def send_request(request):
    """
    Send request to the server.
    Receive and print the response from the server.

    Parameters:
        request : request to be sent to the server
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))

    # Send request
    print(f"\nSending: {request}")
    client_socket.send(request.encode())

    # Receive response
    response = client_socket.recv(1024)

    # CRLF = \r\n
    header_pos = response.find(b'\r\n\r\n')
    header = response[:header_pos].decode()
    status = header.split('\r\n')[0]

    # +4 is to skip two CRLF, which divides the head and body of the response
    body = response[header_pos+4:] 
    
    # Check Content-Type
    content_type = ''
    for line in header.split('\r\n'):
        if line.lower().startswith('content-type'):
            content_type = line.split(':')[1].strip()

    # If the content is image
    if content_type.startswith('image/'):
        filename = 'output_image.' + content_type.split('/')[1]
        with open(filename, 'wb') as f: # Image should be opened by write byte
            f.write(body)

            # Receive the whole image. It can be over 1024
            while True:
                bunch = client_socket.recv(1024)
                if not bunch:
                    break
                f.write(bunch)
        print("Server response:")
        print(f"Image saved as {filename}\n")
    # If the content is text.
    else:
        # Receive the whole text response.
        while True:
            bunch = client_socket.recv(1024)
            if not bunch:
                break
            body += bunch

        print("Server response:")
        print(f"Status: {status}")
        if body:
            print(body.decode())
        else:
            print("Response body is empty\n")

    # Close socket
    client_socket.close()

    print()

def set_requests():
    """
    Create sample requests.
    Create threads for each request.
    """

    last_modified = formatdate(os.path.getmtime('htdocs/index.html'), usegmt=True)

    requests = [
        'GET /index.html HTTP/1.1',
        'GET /image.png HTTP/1.1',
        'HEAD /helloworld.html HTTP/1.1',
        'GET /nonexistentfile.html HTTP/1.1',
        'GET /forbidden/forbiddenfile.txt HTTP/1.1',
        'GET /index.html.zip HTTP/1.1',
        f'GET /index.html HTTP/1.1\r\nIf-Modified-Since: {last_modified}\r\n'
    ]

    
    threads = []
    for req in requests:
        thread = threading.Thread(target=send_request,args=(req,))
        threads.append(thread)
        thread.start()

    for th in threads:
        th.join()

set_requests()
