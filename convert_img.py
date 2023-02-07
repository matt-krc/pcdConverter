from PIL import Image
import PIL
import ffmpeg

def convert_pcd(pic, outfn):
    try:
        image = Image.open(pic)
        # image = image.rotate(90)
        image.save(outfn)
    except:
        return False

    return True


def convert_other(pic, outfn):
    try:
        image = Image.open(pic)
        image.save(outfn)
    except:
        return False
    return True


def convert_pic(pic, outfn):
    try:
        stream = ffmpeg.input(pic)
        stream = ffmpeg.output(stream, outfn)
        ffmpeg.run(stream)
    except:
        return False
    return True