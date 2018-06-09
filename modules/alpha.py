import numpy as np
import cv2
import time
import glob
import os

from . import imgcut, rename


def show(image, title=''):
    cv2.imshow('Image Preview : %s' % title, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def alpha(image_dir):
    '''ETC1 포맷으로 인해 분리된 Alpha 이미지 파일을 합칩니다.

    Args:
        image_dir (str): 이미지 파일 경로, 알파 파일 경로도 동일한 위치에 있어야 합니다.

    Returns:
        image (numpy.ndarray): 해당 이미지의 numpy 배열을 반환
    '''
    # 알파 이미지 검색
    if os.path.exists(image_dir.replace('.png', '_alpha.png')):
        alpha_dir = image_dir.replace('.png', '_alpha.png')
    elif image_dir[-6:] == "_N.png":
        return cv2.imdecode(np.fromfile(image_dir, dtype=np.uint8), 1)
    else:
        for alpha_path in ['_1_Alpha.png', '_2_Alpha.png']:
            if os.path.exists(image_dir.replace('.png', alpha_path)):
                alpha_dir = image_dir.replace('.png', alpha_path)
        return cv2.imdecode(np.fromfile(image_dir, dtype=np.uint8), 1)

    # 이미지 로딩
    image = cv2.imdecode(np.fromfile(image_dir, dtype=np.uint8), 1)
    alpha = cv2.imdecode(np.fromfile(alpha_dir, dtype=np.uint8), -1)
    # 이미지 크기가 다른경우 alpha이미지 크기를 늘림
    if alpha.shape[:2] != image.shape[:2]:
        alpha = cv2.resize(alpha, None, fx=2, fy=2)

    # 색깔별 채널 분리
    b, g, r = cv2.split(image)
    a = cv2.split(alpha)[-1]

    # 알파 채널의 특정 값 미만 픽셀을 0으로 버림. 필요한 경우에만 활성화 (권장하지 않음)
    # if a.shape[:2] == (512,512):
    # a = cv2.threshold(a, 3, 255, cv2.THRESH_TOZERO)[1]

    # RGBA 채널 전부 합쳐서 return
    return cv2.merge((b, g, r, a))


if __name__ == '__main__':
    # 시간 측정 시작
    start_time = time.time()

    # 시간측정 종료
    print("--- %s seconds ---" % (time.time() - start_time))
