import os
import sys
import configparser

from modules import data_parser


# 프로그램 위치와 실행 위치가 다르면 전자로 변경
if os.getcwd() != os.path.split(sys.argv[0])[0]:
    os.chdir(os.path.split(sys.argv[0])[0])

config = configparser.ConfigParser()
info = data_parser.Info()

# config.ini 파일 확인 & 읽기
if os.path.exists("config.ini"):
    try:
        config.read("config.ini", encoding="utf-8")
    except configparser.MissingSectionHeaderError:
        config.read("config.ini", encoding="utf-8-sig")
else:
    # 인터넷 연결이 되어있지 않았던 경우 오류 발생
    if not info.ststus:
        raise data_parser.ParsingError("인터넷에 연결이 되어있지 않습니다")
    # config.ini 파일이 없으면 다운로드
    info.dl("config.ini")
    config.read("config.ini", encoding="utf-8")

# 데이터 강제 업데이트 여부 불러오기 (Bool)
force_update = config.getboolean("main", "force_data_update")

# config.ini 내 json 색션에 있는 내용들이 있는지 확인
# 강제 업데이트가 참이거나 파일이 없으면 다운로드 후 저장
os.makedirs("data", exist_ok=True)
for key, value in config['json'].items():
    if force_update:
        info.dl(value)
    elif os.path.exists(value):
        continue
    else:
        info.dl(value)
