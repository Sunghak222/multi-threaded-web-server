# Multithreaded Web Server in Python

## Description

COMP2322 Project
This project implements multi-threaded HTTP web server in Python for COMP2322 course (Computer Networking).

## Features
- Supports GET and HEAD requests
- Persistent and non-persistent connections
- Status codes:
    - 200 OK
    - 304 Not Modified : If-Modified-Since is implemented
    - 400 Bad Request
    - 403 Forbidden
    - 404 Not Found
    - 415 Unsupported Media Type
- Log audits for every request
- Type detection for text and image files

## Structure

'''
Project/ 
├── htdocs/ # Directory containing files to test
│    ├── index.html          
│    ├── image.png                   # for testing image file
│    ├── helloworld.html           
│    └── forbidden/forbiddenfile.txt # for testing 403 Forbidden
├── server.py 
├── client.py # for testing
├── logs.txt  # log file
└── README.md # documentation
'''

## How To Run
1. python server.py
2. Open http://localhost:8000/{filepath} or run python client.py

## Log Format
[Time] | IP address | Requested file path | status code
[YYYY-MM-DD HH:MM:SS] IP requested_path status_code
Example: [2025-04-21 22:23:10] 127.0.0.1 /index.html 200 OK

## Notes
Only files under the htdocs/ directory are served.
Requests targeting paths containing /forbidden return a 403 Forbidden response.
Files not in the supported MIME types, such as .zip, return a 415 Unsupported Media Type

## Author
HEO Sunghak
COMP2322: Computer Networking
