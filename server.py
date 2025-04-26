# server.py
import socket
import threading
import os
import mimetypes
from pathlib import Path
from contextlib import closing
from datetime import datetime, timezone
import email.utils

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8000
SUPPORTED_TYPES = ['text/html', 'text/plain', 'image/png', 'image/jpeg']

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None
        self.threads = []
        self.log_manager = None

    # ex) [2025-04-19 17:45:32] 127.0.0.1 "/index.html" 200 OK
    def store_log(self, address, filename, status_code):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] {address[0]} {filename} {status_code}\n"
        with open("logs.txt", "a") as f:
            f.write(log_line)


    def run(self):
        try:
            # Create socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((SERVER_HOST, SERVER_PORT))
            self.server_socket.listen(10)
            print('Listening on port %s ...' % SERVER_PORT)

            while True:
                client_connection, client_address = self.server_socket.accept()
                print(f'Connected with {client_address}')

                thread = threading.Thread(target=self.handle_request,args=(client_connection,client_address))
                thread.start()
                self.threads.append(thread)

        except KeyboardInterrupt:
            print("Closing the server")
            self.server_socket.close()
        finally:
            self.server_socket.close()

    def handle_request(self, connection, address):
        while True:
            # Get the client request
            request = connection.recv(1024).decode()
            if not request:
                print("Client sent an empty request")
                connection.close()
                break
            print(f"Received request:\n{request}")

            # Parse HTTP headers 
            # ex)'GET /index.html HTTP/1.1',
            # Get header
            headers = request.split('\r\n')
            fields = headers[0].split()

            # Get request type. ex) GET
            request_type = fields[0]

            # Get filename. ex) /index.html
            filename = fields[1]

            
            # Check if keep-alive
            keep_alive = False
            if_modified_since = None
            for line in headers[1:]:
                lowered_line = line.lower()
                if lowered_line.startswith('connection:'):
                    if 'keep-alive' in lowered_line:
                        keep_alive = True
                elif lowered_line.startswith('if-modified-since:'):
                    if_modified_since = line[len("If-Modified-Since: "):].strip()

            if filename == '/':
                filename = '/index.html'
            filepath = 'htdocs' + filename

            # Read file
            try:
                # If the requested file is in forbidden area,
                # the server sends 403 Forbidden to the client.
                if '/forbidden' in filename:
                    response = 'HTTP/1.1 403 Forbidden\r\n'
                    response += 'Content-Length: 9\r\n'
                    response += 'Content-Type: text/plain\r\n'
                    response += f'Connection: {"keep-alive" if keep_alive else "close"}\r\n'
                    response += '\r\n'
                    response += 'Forbidden'
                    connection.sendall(response.encode())

                    self.store_log(address, filename, "403 Forbidden")

                    if not keep_alive:
                        print("Connection closed")
                        connection.close()
                    break

                modified_time = os.path.getmtime(filepath)
                last_modified = email.utils.formatdate(modified_time, usegmt=True)

                # basic function to get file type
                file_type = mimetypes.guess_type(filepath)[0] or 'application/octet-stream'

                if file_type.startswith('text/'):
                    with open(filepath, 'r') as fin:
                        content = fin.read()
                    body = content.encode()
                else:
                    # Image file should be opened with read binary mode
                    with open(filepath, 'rb') as fin:
                        body = fin.read()
            except FileNotFoundError:
                # When the requested file is not found, send 404 Not Found
                response = 'HTTP/1.1 404 Not Found\r\n'
                response += 'Content-Length: 14\r\n'
                response += 'Content-Type: text/plain\r\n'
                response += f'Connection: {"keep-alive" if keep_alive else "close"}\r\n'
                response += '\r\n'
                response += 'File Not Found'
                connection.sendall(response.encode())

                self.store_log(address, filename, "404 Not Found")

                if not keep_alive:
                    print("Connection closed")
                    connection.close()
                break
            
            # If unsupported types of file is requested,
            # the server sends 415 Unsupported Media Type to the client.
            if file_type not in SUPPORTED_TYPES:
                    response = 'HTTP/1.1 415 Unsupported Media Type\r\n'
                    response += 'Content-Length: 24\r\n'
                    response += 'Content-Type: text/plain\r\n'
                    response += f'Connection: {"keep-alive" if keep_alive else "close"}\r\n'
                    response += '\r\n'
                    response += 'Unsupported Media Type'
                    connection.sendall(response.encode())
                    
                    self.store_log(address, filename, "415 Unsupported Media Type")

                    if not keep_alive:
                        print("Connection closed")
                        connection.close()
                    break
            
            # Parse the request type
            if request_type == 'GET':
                if if_modified_since: # Identify if the response should be 304 Not Modified
                    client_time = email.utils.parsedate_to_datetime(if_modified_since)
                    server_time = datetime.fromtimestamp(modified_time,timezone.utc)

                    client_time = client_time.replace(microsecond=0)
                    server_time = server_time.replace(microsecond=0)

                    if server_time <= client_time:
                        response = 'HTTP/1.1 304 Not Modified\r\n'
                        response += f'Last-Modified: {last_modified}\r\n'
                        response += f'Connection: {"keep-alive" if keep_alive else "close"}\r\n'
                        response += '\r\n'
                        connection.sendall(response.encode())

                        self.store_log(address, filename, "304 Not Modified")

                        if not keep_alive:
                            print("Connection closed")
                            connection.close()
                        break
                
                # Form response of 200 OK when request is GET
                response = 'HTTP/1.1 200 OK\r\n'
                response += f'Last-Modified: {last_modified}\r\n'
                response += f'Content-Length: {len(body)}\r\n'
                response += f'Content-Type: {file_type}\r\n'
                response += f'Connection: {"keep-alive" if keep_alive else "close"}\r\n'
                response += '\r\n'
                
                connection.sendall(response.encode() + body)

                self.store_log(address, filename, "200 OK")
                
            elif request_type == 'HEAD': 
                # Form response of 200 OK when request is HEAD         
                response = 'HTTP/1.1 200 OK\r\n'
                response += f'Last-Modified: {last_modified}\r\n'
                response += f'Content-Length: 0\r\n'
                response += f'Content-Type: {file_type}\r\n'
                response += f'Connection: {"keep-alive" if keep_alive else "close"}\r\n'
                response += '\r\n'

                connection.sendall(response.encode())

                self.store_log(address, filename, "200 OK")

            else:
                # Form response of 400 Bad Request
                response = 'HTTP/1.1 400 Bad Request\r\n'
                response += 'Content-Length: 23\r\n'
                response += 'Content-Type: text/plain\r\n'
                response += f'Connection: {"keep-alive" if keep_alive else "close"}\r\n'
                response += '\r\n'
                response += 'Request Not Supported'

                connection.sendall(response.encode())

                self.store_log(address, filename, "400 Bad Request")

            if not keep_alive:
                connection.close()
                print("Connection closed")
                break

        print()
    
if __name__ == "__main__":
    server = Server(SERVER_HOST,SERVER_PORT)
    server.run()
