import time
import re
import os
import sys
import logging

import change_dir

import abunpack
import acb2wav


def main(file_list: list):
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

    # sys.argv 로 받은 파일 목록이 1(자기 자신) 이면 오류처리
    if len(file_list) == 1:
        logger.error("가공할 파일을 실행파일에 드래그 & 드롭하거나, 커맨드창에서 순서대로 입력해주세요.")
        return

    # 추출 시작 메시지
    logger.info(f"Start Extracting : {time.strftime('%Y-%m-%d %I:%M:%S')}")

    # 받은 파일 목록으로 반복 구문 실행
    for file_dir in file_list[1:]:
        # 지원가능한 파일인지 정규표현식으로 판단하기 위한 정규식 컴파일
        re_ab = re.compile(".+[.]ab")
        re_acb = re.compile(".+[.]acb[.]bytes")

        # AssetBunle 파일 (*.ab) 인 경우
        if re_ab.match(file_dir):
            logger.info(f"\n=== AssetBundle File: {os.path.split(file_dir)[1]} ===")
            abunpack.abunpack(file_dir)
        # ACB 파일 (*.acb.bytes) 인 경우
        elif re_acb.match(file_dir):
            logger.info(f"=== ACB File: {os.path.split(file_dir)[1]} ===")
            acb2wav.acb2wav(file_dir)
        # 둘다 아닌 경우 로거에 경고 반환
        else:
            logger.warning(f"=== Unknown file: {os.path.split(file_dir)[1]}===")
    else:
        # 반복문 종료 이후
        logger.info(f"Finish Extracting : {time.strftime('%Y-%m-%d %I:%M:%S')}\n\n")
        return


if __name__ == "__main__":
    # 시간측정용
    start_time = time.time()

    # 메인 함수, 인자로 파일 목록 전달
    main(sys.argv)

    # 시간측정 종료
    print("=== 소모시간 : %s초 ===" % (time.time() - start_time))
    os.system('pause')
