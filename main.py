import time
import re
import os
import logging
import glob
import argparse

import change_dir

import abunpack
import acb2wav


__version__ = "2.2.1"


def main():
    # argparse 설정
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-o", "--output_dir", help="Master output dir", type=str, default="./")
    arg_parser.add_argument("target", help="*.ab or *.acb.bytes file or folder's path", type=str, nargs="+")
    args = arg_parser.parse_args()
    output_dir = args.output_dir
    file_list = args.target

    # Logging 모듈 설정
    logger = logging.getLogger("")
    logger.setLevel(logging.INFO)

    # 로거 포맷 설정
    formatter = logging.Formatter('%(levelname)s | %(message)s')

    # 핸들러 설정 + 추가
    stream_hander = logging.StreamHandler()
    stream_hander.setFormatter(formatter)
    logger.addHandler(stream_hander)

    # 파일 핸들러
    if change_dir.config.getboolean("logger", "logger_save"):
        file_handler = logging.FileHandler('log.txt', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # 추출 시작 메시지
    logger.info(f"girlsfrontline-resources-extractor: {__version__}")
    logger.info(f"Start Extracting: {time.strftime('%Y-%m-%d %I:%M:%S')}")
    # 지원가능한 파일인지 정규표현식으로 판단하기 위한 정규식 컴파일
    re_ab = re.compile(".+[.]ab")
    re_acb = re.compile(".+[.]acb[.]bytes")

    # 받은 파일 목록으로 반복 구문 실행
    for file_dir in file_list:
        # 폴더를 넣으면 폴더 내 ab, acb.bytes 파일들을 추출
        if os.path.isdir(file_dir):
            file_dirs = glob.glob(f"{file_dir}/*.ab") + glob.glob(f"{file_dir}/*.acb.bytes")
        else:
            file_dirs = [file_dir]

        for fd in file_dirs:
            # AssetBunle 파일 (*.ab) 인 경우
            if re_ab.match(fd):
                logger.info(f"\n=== AssetBundle File: {os.path.split(fd)[1]} ===")
                abunpack.abunpack(fd, output_dir)
            # ACB 파일 (*.acb.bytes) 인 경우
            elif re_acb.match(fd):
                logger.info(f"=== ACB File: {os.path.split(fd)[1]} ===")
                acb2wav.acb2wav(fd, output_dir)
            # 둘다 아닌 경우 로거에 경고 반환
            else:
                logger.warning(f"=== Unknown file: {os.path.split(fd)[1]}===")
    else:
        # 반복문 종료 이후
        logger.info(f"Finish Extracting : {time.strftime('%Y-%m-%d %I:%M:%S')}\n\n")
        return


if __name__ == "__main__":
    # 시간측정용
    start_time = time.time()

    # 메인 함수
    main()

    # 시간측정 종료
    print("=== 소모시간 : %s초 ===" % (time.time() - start_time))
    os.system('pause')
