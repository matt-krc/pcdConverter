import sys
from io import BytesIO
import pycdlib
import os


def extract_images(input_name, output_dir, extension):
    output_img_dir = f"{output_dir}/{extension}"
    if not os.path.isdir(output_img_dir):
        os.makedirs(output_img_dir)

    iso = pycdlib.PyCdlib()
    iso.open(f'./files/{input_name}.iso')

    for dirname, dirlist, filelist in iso.walk(iso_path='/'):
        # print("Dirname:", dirname, ", Dirlist:", dirlist, ", Filelist:", filelist)
        for file in filelist:
            fn = file.split(";")[0]
            ext = fn.split(".")[-1]
            if ext == 'PCD' and not os.path.exists(f"{output_img_dir}/{fn}"):
                extracted = BytesIO()
                path = f"{dirname}/{file}"
                print(f"Extracting file: {path}")
                iso.get_file_from_iso_fp(extracted, iso_path=path)
                with open(f"{output_img_dir}/{fn}", "wb") as f:
                    f.write(extracted.getbuffer())

    iso.close()