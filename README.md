# LAB 1 PR: HTTP file server with TCP sockets
During this laboratory work I developed a simple HTTP file server in Python, where I can browse the directory for nested directories or files.

## Contents of Directory
* I have multiple directories in the root. *Downloads* directory is where files are saved using the client. *Public* contains other nested directories, as well as some html, png and pdf files for testing. The other nested directories(*books, docs*) also feature png, html and pdf files for testing. *Report_pics* directory contains images used in this report. 
* In this project, the *Dockerfile* defines how the server and client environments are built, including the necessary dependencies and instructions to run the Python applications inside containers. The *docker-compose.yml* file is used to coordinate these containers, starting both the server and client, linking them together, mapping the appropriate ports, and managing shared volumes.
* The *server.py* file handles incoming HTTP requests, retrieves the requested files from the specified directory, and sends them back to the client.
* The *client.py* connects to the server, sends file requests, and displays or saves in the *downnloads* folder the received content based on the file type.

    ![contents.png](public/report_pics/contents.png)

## Dockerfile
The *Dockerfile* makes sure to set a lightweight Python 3.12 environment, copies the server and client scripts into the container’s /app directory, sets it as the working directory, and exposes port 8000 so server.py/client.py can use it.
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY server.py client.py ./
EXPOSE 8000
```

## Docker compose
This *docker-compose.yml* file defines two services: a server that runs server.py on port 8000 to host files, and a client that runs client.py to connect to the server,while managing their shared volumes and ensuring the server starts before the client.

```dockerfile
services:
  server:
    build: .
    container_name: pr-web-server
    environment:
      PORT: 8000
    ports:
      - "8000:8000"
    volumes:
      - ./:/app:ro
    command: ["python", "server.py", "/app"]
  client:
      build: .
      entrypoint: [ "python", "client.py" ]
      volumes:
        - ./downloads:/app/downloads
      depends_on:
        - server
```

## Running the project
We can run the project locally using the command:
```python
python3 server.py <path_to_directory>
```
In the following picture you can see an example of how i can run the project locally with the *root* directory of the project as an argument:

![run_python.png](public%2Freport_pics%2Frun_python.png)

We can also run it using docker with the following command:
```
docker compose up server
```

## Content of served directory
If we serve the root we will see the following files and directories in the browser. We can see all types of files, but can access only png, html, pdf files.
![listing.png](public/report_pics/listing.png)

We can also choose to serve another directory, like *public* (as seen in the following picture). We can do this locally by running a command similar to this: ```python3 server.py public```, or with docker by changing the command line in *docker-compose.yml*.

![public_dir.png](public%2Freport_pics%2Fpublic_dir.png)
## Requesting files
* We can request a **png** file in the browser by accessing its path or by navigating to it through the folders in the listings.

  ![png_request.png](public%2Freport_pics%2Fpng_request.png)
  We can observe using Inspect in the Network tab that the response for the png request was successful (200 OK).
  ![success_response.png](public%2Freport_pics%2Fsuccess_response.png)
* To request a **pdf** file we do the same as for the png file.
![housemaid.png](public%2Freport_pics%2Fhousemaid.png)

* We can also request a  **html** and we will see the html page in the browser.
![html_request.png](public%2Freport_pics%2Fhtml_request.png)

* If we request an inexistent file or a file with an extension  that is not permitted, we will get the 404 page. We can also click on the *homepage* button to go back to the root directory list.
![404.png](public%2Freport_pics%2F404.png)

## Client
We can run the client both locally:
```python
 python3 client.py 0.0.0.0 8000 The_Housemaid.pdf
```
or using docker:
```
docker compose run --rm client server 8000 The_Housemaid.pdf
```
And we will get the file saved in the *downloads* folder.

![download.png](public%2Freport_pics%2Fdownload.png)

## Browse a friend's server
For this part I browsed a colleague's (Daria Rațeeva) server. First we connected to the same hotspot, then she started her server and then she ran ```ifconfig``` on her laptop and gave it to me. After that, I entered in my browser: ```172.20.10.10:8000``` (her ip addres : port) an got the following result:

![img.png](public/report_pics/img.png)
I was also able to browse through nested directories:

![img_1.png](public/report_pics/img_1.png)
When clicking a pdf file it opened in the browser:

![img_2.png](public/report_pics/img_2.png)

I also tried to use my client to download a file to the *downloads* folder and got a success response:

![img_3.png](public/report_pics/img_3.png)
The document was saved to the downloads folder:

![img_4.png](public/report_pics/img_4.png)

I did the same with a png and it was saved to downloads as well and I got a success response:

![img_5.png](public/report_pics/img_5.png)

![img_6.png](public/report_pics/img_6.png)

I also tried to request a html file and I got a success message and the html file was printed in the terminal:
![img_7.png](public/report_pics/img_7.png)
![img_8.png](public/report_pics/img_8.png)
