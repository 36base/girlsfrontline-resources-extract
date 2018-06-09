import numpy as np
import cv2
import time
import glob
from multiprocessing import process, Pool
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


def main(name, mode="", slice_blank=False):
    '''소녀전선 이미지 리소스를 가공하는 함수입니다.

    Args:
        name(str) : 일반 이미지 파일 경로 입력
        mode(str) : 이미지 파일들의 종류. doll, equip 입력 가능
        slice_blank (bool) : 전신 일러 빈공간 제거 여부 (실험중)

    Return:
        True
    '''
    fdir = os.path.split(name)[0]
    if mode == "doll":  # 인형 이미지 모드
        output_name, flag = rename.doll(name, unuse_N=True, flag_filter="N")
        result_image = alpha(name)

        # Flag별 처리
        if flag == "N":  # 포트레이트(신), 스킨 분류
            output_name = "portraits/" + output_name if '_' not in output_name else "portraits/skin/" + output_name
        elif flag == "E":  # unusE file
            print()
            return True  # 건너뛰고 종료.
        elif flag == "Y":  # dummY file
            print(name)
            output_name = "dummy/" + name[len(fdir):]

        # 이미지의 빈공간 제거 여부(실험중). 64픽셀 단위로 제거.
        if slice_blank:
            result_image = imgcut.cutimg(result_image)
    elif mode == "equip":
        output_name = rename.equip(name)
        result_image = alpha(name)
    else:
        output_name = name[len(fdir):]
        result_image = alpha(name)

    # 이미지 확인용. 필요시 활성화
    # print(merged.shape)
    # show(merged)

    # 저장
    # cv2.imencode('.png', result_image)[1].tofile("charactor/output/%s.png"%output_name)
    print("Saved: {0}".format(output_name))
    return True


if __name__ == '__main__':
    # 시간 측정 시작
    start_time = time.time()

    # ===파일 경로 설정===
    # 일반/alpha 이미지 파일이 같이 있는 폴더를 입력해주세요.
    # 폴더의 끝에는 반드시 / 를 붙여주세요.
    fdir = "charactor/"

    # 파일 목록 불러오기, alpha 파일은 목록에서 제거
    allFileList = glob.glob(fdir + '*.png')
    alphaFileList = glob.glob(fdir + '*_Alpha.png')
    fileList = list(set(allFileList) - set(alphaFileList))
    fileList.sort()

    # 함수 실행
    for name in fileList:
        main(name, mode="doll", slice_blank=True)
    # pool = Pool(processes=12)
    # pool.map(main, fileList)

    # 시간측정 종료
    print("--- %s seconds ---" % (time.time() - start_time))
