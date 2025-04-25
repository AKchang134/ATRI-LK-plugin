import jmcomic, yaml, os
from PIL import Image


def img_to_pdf(path, c_path):
    zimulu = []
    image = []
    sources = []

    with os.scandir(path) as entries:
        for entry in entries:
            if entry.is_dir():
                zimulu.append(int(entry.name))
    # 对数字进行排序
    zimulu.sort()

    for i in zimulu:
        with os.scandir(path + "/" + str(i)) as entries:
            for entry in entries:
                if entry.is_dir():
                    print("这一级不应该有自录")
                if entry.is_file():
                    image.append(path + "/" + str(i) + "/" + entry.name)

    if "jpg" in image[0]:
        output = Image.open(image[0])
        image.pop(0)

    for file in image:
        if "jpg" in file:
            img_file = Image.open(file)
            if img_file.mode == "RGB":
                img_file = img_file.convert("RGB")
            sources.append(img_file)
    output.save(c_path, "pdf", save_all=True, append_images=sources)

def download(jm_album_id):
    from . import plugin

    b_path = plugin.get_path() / 'comic'
    b_path.mkdir(parents=True, exist_ok=True)
    py_config = {
        "download": {
            "image": {
                "suffix": ".jpg"
            },
        },
        "dir_rule": {
            "base_dir": str(b_path),
            "rule": 'Bd_Aid_Pindex'
        }
    }
    jm_config = jmcomic.create_option_by_str(yaml.dump(py_config))
    c_path = b_path / jm_album_id / f'{jm_album_id}.pdf'
    if not c_path.exists():
        if not os.path.exists(b_path / jm_album_id):
            jmcomic.download_album(jm_album_id, jm_config)
        img_to_pdf(str(b_path / jm_album_id), str(c_path))
    return c_path
