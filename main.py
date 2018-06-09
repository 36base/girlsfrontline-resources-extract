import sys
import os
import glob
import re
import cv2

from modules import alpha, rename


def image(path, output_path, flags):
    '''이미지 폴더에서 이미지를 불러와 알파 채널 이미지와 병합

    Args:
        path(str): 이미지 폴더 경로
        output_path(str): 결과 이미지 저장 경로
        flags(list): 플래그

    Return:
        None
    '''
    # 선택 경로에서 모든 이미지 파일 불러옴
    file_list = glob.glob(os.path.join(path, "*.png"))
    # 정규식 컴파일
    re_alpha = re.compile("_[Aa]lpha.png")
    re_doll = re.compile("[Pp]ic_.*.png")
    re_equip = re.compile("[^a-z0-9/\\_.-]*")
    # 출력 폴더 + 더미 폴더 생성
    os.makedirs(os.path.join(output_path, "dummy"), exist_ok=True)
    # 플래그 처리
    f_unuse_n = True if "-n" in flags else False
    f_split_by_type = True if "-s" in flags else False

    # 목록에 있는 이미지 불러오기
    for file_path in file_list:
        # 출력경로 초기화
        output_dir = output_path

        # alpha 파일이 아니면 실행
        if not re_alpha.search(file_path):
            # 이미지 로딩 (후 합침)
            img = alpha.alpha(file_path)
            # 이미지 이름 변환 과정, 정규식으로 인형/장비 판단
            if re_doll.search(file_path):
                rn = rename.Doll(file_path)
                name = rn.get_name(f_unuse_n) + ".png"
                flag = rn.get_flag()
            elif re_equip.search(file_path):
                rn = rename.Equip(os.path.split(file_path)[1])
                name = rn.get_name()
                flag = rn.get_flag()
            else:
                name = os.path.split(file_path)[1]
                flag = "N"
            # 플래그별로 폴더 나누기 옵션 활성화
            output_dir = os.path.join(output_dir, flag) if f_split_by_type else output_dir
            # 이름 오류 처리 => 넌 Dummy 폴더로
            if flag == "E":
                output_dir = os.path.join(output_path, "dummy")
                name = os.path.split(file_path)[1]
            # 이미지 저장
            cv2.imencode('.png', img)[1].tofile(os.path.join(output_dir, name))
            print(os.path.join(output_dir, name))
        else:
            continue


def main(argv):
    '''메인 함수

    Args:
        argv(list): sys.argv
    '''
    # args = re.match("(.+.py) *(-[it]*) *([^-.]*)", ' '.join(argv))
    args = re.match("(.+.py) (.+) (.+)", ' '.join(argv))
    if not args:
        print("main.py [dir] [output dir] (flags)")
        return
    path, output_path, *flags = argv[1:]

    if os.path.isdir(path):
        image(path, output_path, flags)
    else:
        print("Except occured")
        return


if __name__ == "__main__":
    # python main.py [original dir] [output dir] (flags)
    main(sys.argv)
