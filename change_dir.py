import os
import sys
import configparser

from modules import data_parser


def check_files_exist():
    config = configparser.ConfigParser()
    info = data_parser.Info()

    # config.ini 파일 확인 & 읽기
    if os.path.exists("config.ini"):
        config.read("config.ini", encoding="utf-8")
    else:
        # 파일 없으면 다운로드
        info.dl("config.ini")
        config.read("config.ini", encoding="utf-8")

    force_update = config.getboolean("main", "force_data_update")
    # config.ini 내 json 색션에 있는 내용들이 있는지 확인
    # 없으면 다운로드 후 저장
    os.makedirs("data", exist_ok=True)
    for key, value in config['json'].items():
        if force_update:
            info.dl(value)
        elif os.path.exists(value):
            continue
        else:
            info.dl(value)


if os.getcwd() != os.path.split(sys.argv[0])[0]:
    os.chdir(os.path.split(sys.argv[0])[0])

check_files_exist()