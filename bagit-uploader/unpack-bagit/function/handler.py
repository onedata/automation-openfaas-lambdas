import json
import os.path
import tarfile
import zipfile


def handle(req: bytes):
    """handle a request to the function
    Args:
        req (str): request body
    """
    args = json.loads(req)

    try:
        return json.dumps({"uploaded_files": unpack_data_dir(args)})
    except:
        return json.dumps("FAILED")


def unpack_data_dir(args):
    archive_filename = args["bagit"]["name"]
    archive_name, archive_type = os.path.splitext(archive_filename)

    if archive_type == '.tar':
        return unpack_tar_bagit_archive(args)
    elif archive_type == '.zip':
        return unpack_zip_bagit_archive(args)
    elif archive_type == '.tgz' or archive_type == ".gz":
        return unpack_tgz_bagit_archive(args)


def unpack_tar_bagit_archive(args):
    archive_path = f'/mnt/onedata/.__onedata__file_id__{args["bagit"]["file_id"]}'
    dst_id = args["destination"]["file_id"]
    dst_dir = f'/mnt/onedata/.__onedata__file_id__{dst_id}'
    extracted_files = []

    with tarfile.TarFile(archive_path) as archive:
        archive_files = archive.getnames()

        bagit_dir = find_bagit_dir(archive_files)
        data_dir = f'{bagit_dir}/data/'

        for file_path in archive_files:
            if file_path.startswith(data_dir):
                try:
                    subpath = file_path[len(data_dir):]

                    file_tarinfo = archive.getmember(file_path)
                    # replace name so that file will be extracted without data/ dir
                    file_tarinfo.name = subpath
                    archive.extract(file_tarinfo, dst_dir)

                    extracted_files.append(f'/mnt/onedata/.__onedata__file_id__{dst_id}/{subpath}')
                except:
                    pass
    return extracted_files


def unpack_zip_bagit_archive(args):
    archive_path = f'/mnt/onedata/.__onedata__file_id__{args["bagit"]["file_id"]}'
    dst_id = args["destination"]["file_id"]
    dst_dir = f'/mnt/onedata/.__onedata__file_id__{dst_id}'
    extracted_files = []

    with zipfile.ZipFile(archive_path) as archive:
        archive_files = archive.namelist()

        bagit_dir = find_bagit_dir(archive_files)
        data_dir = f'{bagit_dir}/data/'

        for file_path in archive_files:
            if file_path.startswith(data_dir):
                try:
                    subpath = file_path[len(data_dir):]

                    file_tarinfo = archive.getinfo(file_path)
                    # replace name so that file will be extracted without data/ dir
                    file_tarinfo.filename = subpath
                    archive.extract(file_tarinfo, dst_dir)

                    extracted_files.append(f'/mnt/onedata/.__onedata__file_id__{dst_id}/{subpath}')
                except:
                    pass
    return extracted_files


def unpack_tgz_bagit_archive(args):
    archive_path = f'/mnt/onedata/.__onedata__file_id__{args["bagit"]["file_id"]}'
    dst_id = args["destination"]["file_id"]
    dst_dir = f'/mnt/onedata/.__onedata__file_id__{dst_id}'
    extracted_files = []

    with tarfile.open(archive_path, "r:gz") as archive:
        archive_files = archive.getnames()

        bagit_dir = find_bagit_dir(archive_files)
        data_dir = f'{bagit_dir}/data/'

        for file_path in archive_files:
            if file_path.startswith(data_dir):
                try:
                    subpath = file_path[len(data_dir):]

                    file_tarinfo = archive.getmember(file_path)
                    # replace name so that file will be extracted without data/ dir
                    file_tarinfo.name = subpath
                    archive.extract(file_tarinfo, dst_dir)

                    extracted_files.append(f'/mnt/onedata/.__onedata__file_id__{dst_id}/{subpath}')
                except:
                    pass
    return extracted_files


def find_bagit_dir(archive_files):
    for file_path in archive_files:
        dir_path, file_name = os.path.split(file_path)
        if file_name == 'bagit.txt':
            return dir_path
