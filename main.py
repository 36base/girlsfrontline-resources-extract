import time
import re
import os
import sys

import change_dir

import abunpack
import acb2wav


def main(file_list: list):
    if len(file_list) == 1:
        print("가공할 파일을 실행파일에 드래그 & 드롭하거나, 커맨드창에서 순서대로 입력해주세요.")
        return
    for file_dir in file_list:
        re_ab = re.compile(".+[.]ab")
        re_acb = re.compile(".+[.]acb[.]bytes")
        if re_ab.match(file_dir):
            print(f"=== AssetBundle File: {os.path.split(file_dir)[1]} ===")
            abunpack.abunpack(file_dir)
        elif re_acb.match(file_dir):
            print(f"=== ACB File: {os.path.split(file_dir)[1]} ===")
            acb2wav.acb2wav(file_dir)
        else:
            continue
    else:
        return


if __name__ == "__main__":
    # 시간측정용
    start_time = time.time()

    # 메인 함수, 인자로 파일 목록 전달
    main(sys.argv)

    # 시간측정 종료
    print("=== 소모시간 : %s초 ===" % (time.time() - start_time))
    os.system('pause')
