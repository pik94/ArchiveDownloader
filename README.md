# Microservice for downloading files

This microservice helps to work a main web size, and serves requests to download 
archives with files. This microservice does nothing excepting packing files into an archive. 
These files can be uploaded on the server via FTP or CMS admin panel.

An archive is created in runtime when a client requests. An archive is not saved on a disk. 
Instead, it's being sent by chunks to the client.

The archive is protected from unauthorized access by a hash in the download link address, 
for example, `http://host.ru/archive/3bea29ccabbbf64bdebcc055319c5745/`. 
Hash is set by a name of directory with files. Below, you can see an example of 
a directory structure:

```
- photos
    - 3bea29ccabbbf64bdebcc055319c5745
      - 1.jpg
      - 2.jpg
      - 3.jpg
    - af1ad8c76fda2e48ea9aed2937e972ea
      - 1.jpg
      - 2.jpg
```

## Usage
After install and run, you can redirect requests starting with '/archive/' 
to your microservice. For example:
```
GET http://host.ru/archive/3bea29ccabbbf64bdebcc055319c5745/
GET http://host.ru/archive/af1ad8c76fda2e48ea9aed2937e972ea/
```

## Install and run
### Docker
#### Install
Build an image:
```bash
docker build -t archive .
```

#### Run
```bash
docker container run -d --name archive \
--mount type=bind,source=/your_photo_storage,target=/app/storage \
--mount type=bind,source=/tmp/logs,target=/app/logs \
-p 8080:8080 \
archive
```
You may pass several environment variables from a list below:
| Key | Default | Description |
| ------ | ------ | ------ |
| DEBUG | -d | Activate a debug mode. Only empty string and "-d" are possible. In this mode, index page is available. |
| HOST | 0.0.0.0 | A host where a service is deployed. |
| PORT | 8080 | A port which a service listens. |
| STORAGE_PATH | /app/storage | A directory with all photos. |
| LOG_FILE | /app/logs/archive.log | A path to a log file. |
| CHUNK_SIZE | 100 | A chunk size (in kilobytes) for chunks which are sent to a client. |
| DELAY | 0.5 | Delay (in seconds) between sending chunk to a client. |


### Manual
#### Install
You must have Python's version at least 3.6.
1. (Optional but recommended) create a virtual environment:
    ```bash
    python3.6 -m venv venv && source ./venv/bin/activate
    ```
2. Install required packages:
    ```bash
    pip install -r requirements.txt
    ```

#### Run
Just time in a terminal:
```bash
python server.py
```
You can pass additional arguments to a script:
| Key | Require | Default | Description |
| ------ | ------ | ------ | ----------|
| -d / --debug | no | - | Activate a debug mode. In this mode, index page is available. |
| -H / --host | no | localhost | A host where a service is deployed. |
| -P / --port | no | 8080 | A port which a service listens. |
| -S / --storage_path | no | photos | A directory with all photos. |
| -L / --log_file | no | archive.log | A path to a log file. |
| -C / --chunk_size | no | 100 | A chunk size (in kilobytes) for chunks which are sent to a client. |
| -D / --delay | no | 0.5 | Delay (in seconds) between sending chunk to a client. |

# Project's targets
This is a task of a [Devman](https://dvmn.org) course dedicated to asynchronous Python.