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

    formatter = logging.Formatter('%(levelname)s | %(message)s')

    stream_hander = logging.StreamHandler()
    stream_hander.setFormatter(formatter)
    logger.addHandler(stream_hander)

    # 파일 핸들러
    if change_dir.config.getboolean("logger", "logger_save"):
        file_handler = logging.FileHandler('log.txt', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if len(file_list) == 1:
        logger.warning("가공할 파일을 실행파일에 드래그 & 드롭하거나, 커맨드창에서 순서대로 입력해주세요.")
        return

    logger.info(f"Start Extracting : {time.strftime('%Y-%m-%d %I:%M:%S')}")
    for file_dir in file_list[1:]:
        re_ab = re.compile(".+[.]ab")
        re_acb = re.compile(".+[.]acb[.]bytes")
        if re_ab.match(file_dir):
            logger.info(f"=== AssetBundle File: {os.path.split(file_dir)[1]} ===")
            abunpack.abunpack(file_dir)
        elif re_acb.match(file_dir):
            logger.info(f"=== ACB File: {os.path.split(file_dir)[1]} ===")
            acb2wav.acb2wav(file_dir)
        else:
            logger.warning(f"=== Unknown file: {os.path.split(file_dir)[1]}===")
    else:
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
