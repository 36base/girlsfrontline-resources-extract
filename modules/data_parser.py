import requests
import json


class ParsingError(Exception):
    def __init__(self, msg="Data Parsing Error"):
        self.msg = msg

    def __str__(self):
        return self.msg


def parser(url: str):
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.text
    else:
        raise ParsingError


class Info():
    def __init__(self):
        url_info = (
            "https://gist.githubusercontent.com/"
            "krepe-suZette/b10999a58c3c8187b4bab0fd1c8a6a0c/raw/"
            "195a216235ba274fa307cfb6d4390cdfd37a22d1/info.json"
        )
        try:
            self.info = json.loads(parser(url_info))
            self.status = True
        except ParsingError:
            self.status = False

    def __getitem__(self, item):
        return self.info[item]

    def dl(self, file_name):
        with open(file_name, 'w', encoding="utf-8") as f:
            f.write(parser(self.info[file_name]))


if __name__ == '__main__':
    pass
