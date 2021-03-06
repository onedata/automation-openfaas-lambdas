from collections.abc import Callable
import json
import os.path
import tarfile
from typing import IO
import time
import zipfile

import requests

HEARTBEAT_INTERVAL_SEC: int = 150
LAST_HEARTBEAT_TIME: int = 0
HEARTBEAT_URL: str = ""


def handle(req: bytes) -> str:
    """Iterates over fetch.txt file (if exists) and collects data about files to be fetched later.

    Args Structure:
        heartbeatUrl (str): url where heartbeats are posted to, automatically added to lambda
        destination (dir-file): destination where all files will be downloaded to
        archive (regular-file): archive to process

    Return:
        filesToFetch (batch/list of objects): collected data about files to be fetched later,
            using format:{"url": <str>, "size": <int>, "path": <str>}
    """
    global HEARTBEAT_URL

    args = json.loads(req)

    HEARTBEAT_URL = args["heartbeatUrl"]
    heartbeat()

    try:
        return json.dumps({"filesToFetch": get_files_to_fetch(args)})
    except:
        return json.dumps("FAILED")


def get_files_to_fetch(args: dict) -> list:
    archive_filename = args["archive"]["name"]
    archive_name, archive_type = os.path.splitext(archive_filename)
    archive_path = f'/mnt/onedata/.__onedata__file_id__{args["archive"]["file_id"]}'
    destination_dir_id = args["destination"]["file_id"]

    if archive_type == '.tar':
        with tarfile.TarFile(archive_path) as archive:
            return get_files_to_fetch_from_archive(destination_dir_id, archive.getnames, archive.extractfile)
    elif archive_type == '.zip':
        with zipfile.ZipFile(archive_path) as archive:
            return get_files_to_fetch_from_archive(destination_dir_id, archive.namelist, archive.open)
    elif archive_type == '.tgz' or archive_type == ".gz":
        with tarfile.open(archive_path, "r:gz") as archive:
            return get_files_to_fetch_from_archive(destination_dir_id, archive.getnames, archive.extractfile)


def get_files_to_fetch_from_archive(
        destination_dir_id: str,
        list_archive_files: Callable[[], list],
        open_archive_file: Callable[[str], IO[bytes]]
) -> list:
    archive_files = list_archive_files()

    bagit_dir = find_bagit_dir(archive_files)
    fetch_file = f'{bagit_dir}/fetch.txt'

    if fetch_file in archive_files:
        files_to_download = []
        for line in open_archive_file(fetch_file):
            url, size, dst_path = line.decode('utf-8').strip().split()
            files_to_download.append({
                "url": url,
                "size": int(size),
                "path": f'.__onedata__file_id__{destination_dir_id}/{dst_path[len("data/"):]}'
            })
            heartbeat()
        return files_to_download
    else:
        return []


def find_bagit_dir(archive_files: list) -> str:
    for file_path in archive_files:
        dir_path, file_name = os.path.split(file_path)
        if file_name == 'bagit.txt':
            return dir_path


def heartbeat():
    global LAST_HEARTBEAT_TIME
    current_time = int(time.time())
    if current_time - LAST_HEARTBEAT_TIME > HEARTBEAT_INTERVAL_SEC:
        r = requests.post(url=HEARTBEAT_URL, data={})
        if r.ok:
            LAST_HEARTBEAT_TIME = current_time
