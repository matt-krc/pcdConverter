from glob import glob
import os
import shutil
import docker
import argparse
import tarfile
import time
from extractISO import extract_images
import convert_img

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument('input')
parser.add_argument('-i', '--image_name', default='my-ubuntu')
parser.add_argument('-c', '--container_name', default='pic-converter')
parser.add_argument('-o', '--image_output', default='png')
parser.add_argument('-e', '--input_extension', default='PCD')
args = parser.parse_args()


def create_iso():
    client = docker.from_env()
    IMAGE_NAME = args.image_name
    CONTAINER_NAME = args.container_name
    FILE_DIR = './files'

    def docker_cp(container, files):
        src = FILE_DIR
        tar = tarfile.open(f'{src}/{args.input}.tar', mode='w')
        for _, fn in files.items():
            tar.add(f'{src}/{fn}')
        tar.close()

        data = open(f'{src}/{args.input}.tar', 'rb').read()
        container.put_archive('/var/tmp/', data)

    try:
        image = client.images.get(IMAGE_NAME)
        print("Image already built")
    except docker.errors.ImageNotFound as e:
        print("Image not found: building image...")
        client.images.build(path='./', tag=IMAGE_NAME, quiet=False)

    # Run container if it doesn't exist
    try:
        container = client.containers.get(CONTAINER_NAME)
    except docker.errors.NotFound as e:
        print("Container not found, running it...")
        client.containers.run(IMAGE_NAME, name=CONTAINER_NAME, tty=True, detach=True, command="/bin/bash")
        container = client.containers.get(CONTAINER_NAME)

    input_extensions = ['BIN', 'CUE', 'TOC']
    files = {}

    # Generally extensions are capitalized but
    for ext in input_extensions:
        if os.path.exists(f"{FILE_DIR}/{args.input}.{ext}"):
            files[ext] = f"{args.input}.{ext}"
        elif os.path.exists(f"{FILE_DIR}/{args.input}.{ext.lower()}"):
            files[ext] = f"{args.input}.{ext.lower()}"
        else:
            raise Exception(f"No {ext} file found.")



    while not container.attrs['State']['Running']:
        print("Waiting for container to start...")
        print(f"CURRENT STATE: {container.attrs['State']}")
        time.sleep(2)

    print("Copying files to Docker container...")
    docker_cp(container, files)

    print("Creating disk image from BIN using poweriso...")
    _, stream = container.exec_run(f"bash -c 'cd /var/tmp/files; poweriso-x64 convert {files['BIN']} -o {args.input}.iso;'", stream=True)
    for data in stream:
        print(data.decode())

    print("Copying file from container to host directory...")
    f = open(f'./files/{args.input}_out.tar', 'wb')
    bits, stat = container.get_archive(f'/var/tmp/files/{args.input}.iso')
    for chunk in bits:
        f.write(chunk)
    f.close()

    print("Extracting tarfile...")
    tar = tarfile.open(f'./files/{args.input}_out.tar')
    tar.extractall('./files/')
    tar.close()

    print("Stopping container...")
    container.stop()
    client.containers.prune()

    print("Cleaning up...")
    for _, file in files.items():
        os.remove(f"{FILE_DIR}/{file}")
    os.remove(f"{FILE_DIR}/{args.input}.tar")
    os.remove(f"{FILE_DIR}/{args.input}_out.tar")

def convert_imgs():
    out_ext = args.image_output
    IMAGE_DIR = f"./files/{args.input}"
    IMAGE_OUT_DIR = f"./files/{args.input}/{out_ext}"
    EXT = "PCD"

    print("Extracting image files from ISO")
    extract_images(args.input, IMAGE_DIR, EXT)

    pics = glob(f"{IMAGE_DIR}/{EXT}/*.{EXT}")

    if len(pics) == 0:
        raise Exception("No files found at path")
    print(f"Total files: {len(pics)}")

    pic_exts = ['jpg', 'jpeg', 'gif', 'png', 'bmp', EXT.lower()]

    skipped_files = []
    for pic in pics:
        pic_ext = pic.split(".")[-1].lower()
        if pic_ext not in pic_exts:
            continue
        if not os.path.isdir(IMAGE_OUT_DIR):
            os.mkdir(IMAGE_OUT_DIR)

        fn = pic.split("/")[-1].split("\\")[-1]
        outfn = f"{IMAGE_OUT_DIR}/"+fn.replace(f".{EXT}", f".{out_ext}")
        if os.path.exists(outfn):
            continue

        if EXT == 'PCD':
            out = convert_img.convert_pcd(pic, outfn)
        elif EXT.lower() == 'gif':
            out = True
            shutil.copy(pic, outfn)
        elif EXT == 'PIC':
            out = convert_img.convert_pic(pic, outfn)
        else:
            out = convert_img.convert_other(pic, outfn)

        if not out:
            skipped_files.append(outfn)

    print("Skipped files:")
    for f in skipped_files:
        print(f)


if __name__ == "__main__":
    if not os.path.exists(f"./files/{args.input}.iso"):
        print("No ISO found for input string. Creating ISO disk image...")
        create_iso()
    convert_imgs()
