import os

import cv2
import numpy as np


def show(image, title=''):
    cv2.imshow('Image Preview : %s' % title, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def load_image(path: str, flag=cv2.IMREAD_COLOR):
    with open(path, "rb") as f:
        data = np.frombuffer(f.read(), dtype="uint8")
    return cv2.imdecode(data, flag)


def save_image(img: np.ndarray, path: str):
    data = cv2.imencode('.png', img, [16, 5])[1]
    with open(path, "wb") as f:
        f.write(data)


def join_alpha(img: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    if alpha.shape[2] != 4:
        raise Exception("대충 알파 이미지 대충넣었냐는 오류")

    img_height, img_width = img.shape[:2]
    a_height, a_width = alpha.shape[:2]

    # 알파 이미지 크기 맞추기 겸 채널 분리
    if (img_width, img_height) != (a_width, a_height):
        alp = cv2.resize(alpha, None, fx=img_width / a_width, fy=img_height / a_height)
    else:
        alp = alpha.copy()

    # RGB 채널 분리
    b, g, r = cv2.split(img)
    # 알파 채널 threshold
    _, a = cv2.threshold(alp[:, :, 3], 5, 255, cv2.THRESH_TOZERO)
    return cv2.merge((b, g, r, a))


def merge_all(file_list: list, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    for file_path in file_list:
        path, name_ext = os.path.split(file_path)
        name, ext = os.path.splitext(name_ext)
        if os.path.isfile(os.path.join(path, f"{name}_Alpha{ext}")):
            print(f"Find alpha image: {name}_Alpha{ext}")
            img = load_image(file_path)
            alpha = load_image(os.path.join(path, f"{name}_Alpha{ext}"), -1)
            result = join_alpha(img, alpha)
            save_image(result, os.path.join(output_dir, name_ext))
            print(f"File saved at {os.path.join(output_dir, name_ext)}")
        else:
            print(f"Cannot find alpha file {name}_Alpha{ext}")
    return


if __name__ == '__main__':
    import argparse
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-o", "--output_dir", help="Master output dir", type=str, default="./output")
    arg_parser.add_argument("target", help="RGB images' path", type=str, nargs="+")
    args = arg_parser.parse_args()
    merge_all(args.target, args.output_dir)
