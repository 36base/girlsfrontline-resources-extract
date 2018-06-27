import glob
import re
import time
import json
import os

# 장비 카테고리 목록
equip_cat = {
    "人形装备": "doll",
    "弹匣": "ammo",
    "配件": "accessory"
}

# 장비 타입 목록
equip_type = {
    "光学瞄准镜": "scope",
    "全息瞄准镜": "holo",
    "ACOG瞄准镜": "reddot",
    "红外夜视仪": "nightvision",
    "穿甲弹": "apBullet",
    "状态弹_空尖弹": "hpBullet",
    "空尖弹": "hpBullet",
    "马格南弹": "hpBullet_mag",
    "霰弹": "sgBullet",
    "高速弹": "hvBullet",
    "战术核芯片": "chip",
    "外骨骼": "skeleton",
    "防弹插板": "armor",
    "特殊": "special",
    "消音器": "silencer",
    "弹链箱": "ammoBox",
    "伪装披风": "suit"
}

# 전용장비의 이름 등을 수정해야 할때 사용해주세요.
equip_etc = {
    "-": "_",
    "_N.": ".",
    "_N1": "_1",
    "_N2": "_2",
    "_N3": "_3",
    "_S.": "_lab.",
    "_X.": "_x.",
    "独头弹": "s",
    "鹿弹": "b",
    "PTRD": "ptrd",
    "MP5": "mp5",
    "UMP": "ump",
    "MG3": "mg3",
    "IDW": "idw",
    "M1918": "m1918",
    "莫辛纳甘": "m1891",
    "HK416": "hk416",
    "阿梅利": "ameli",
    "M4A1": "m4a1",
    "M16A1": "m16a1",
    "M1911": "m1911",
    "Springfield": "m1903",
    "AR15": "ar15",
    "AK": "ak",
    "Kar98k": "98k",
    "64式": "64type",
    "纳甘左轮": "m1895",
    "FN49": "fn49",
    "MP446": "mp446",
    "9A91": "9a91",
    "FAMAS": "famas",
}

# 인형 이름중 정규표현식이 오류가 나는 경우 사용합니다.
doll_except = {
    "GG_elfeldt": "GG-elfeldt",
    "BB_Noel": "BB-Noel"
}

with open("data/dollSkin.json", 'r', encoding="utf-8") as f:
    core = json.loads(f.read())


def gfl_core_doll(name, sid=0):
    '''coreLite.json에서 인형 id, 스킨 id 읽어오는 함수

    Args:
        name(str): 인형 이름
        sid(int): 스킨 번호(1904 등등)

    Return:
        doll_id(): 인형 도감번호
        doll_skinid(): 인형 스킨순번
    '''

    # 예외처리
    for i, j in doll_except.items():
        if name == j:
            name = i
    # 아이디/스킨아이디 찾기, 현재 비교시 소문자 변환 과정을 거침
    for doll in core:
        if doll["name"].lower() == name.lower():
            doll_id = doll["id"]
            doll_skins = doll["skinId"]
            doll_skinid = None
            if not sid:
                return doll_id, ""
            try:
                doll_skinid = doll_skins.index(int(sid)) + 1
            except:
                pass
            return doll_id, doll_skinid
    return None, None


class Equip():
    '''중국어로 되어있는 장비이름을 한국어로 변환

    Args:
        name (str) : 원본 이미지 이름
        adv (bool) : 특수 장비 이름 변환 여부
    '''
    def __init__(self, equip_name, adv=True):
        self.name = equip_name
        self.flag = "N"
        for i, j in equip_cat.items():
            if i in self.name:
                self.name = self.name.replace(i, j)
                break
        for i, j in equip_type.items():
            if i in self.name:
                self.name = self.name.replace(i, j)
                break
        if adv:
            for i, j in equip_etc.items():
                if i in self.name:
                    self.name = self.name.replace(i, j)
                    break
        if re.search("[^a-z0-9/\\_.-]+[._]", self.name):
            self.flag = "E"

    def get_name(self):
        '''return name

        Return:
            name(str): 바뀐 장비 이름 반환
        '''
        return self.name

    def get_flag(self):
        '''Flag 값 리턴(정상, 오류 등등)

        Return:
            flag(str): 정상은 N, 오류나면 E
        '''
        return self.flag


class Doll():
    def __init__(self, path):
        file_name = os.path.split(path)[1][:-4]
        for except_name in doll_except.keys():
            if except_name in file_name:
                file_name = file_name.replace(except_name, doll_except[except_name])

        re_name = re.search("[Pp]ic_([0-9A-Za-z- ]*)_*([0-9]*)_*([NMDF]*)", file_name)
        if re_name:
            # 정규표현식 이용, groups로 분할
            self.doll_name, self.skin_id, self.flag = re_name.groups()
            # DB에서 전술인형 도감번호와 스킨순서 검색
            self.doll_id, self.skin_num = gfl_core_doll(self.doll_name, self.skin_id)
            if self.skin_num is None:
                self.flag = "E"
        else:
            self.flag = "E"

    def get_all(self):
        '''Return all data

        Returns:
            doll_id(str): 전술인형의 DB 내 이름
            skin_id(str): 스킨 번호를 해당 인형의 n번째 스킨인지로 변환
            flag(str): 출력값의 상태
        '''
        if self.flag != "E":
            return (self.doll_id, self.skin_num, self.flag)
        else:
            return None

    def get_name(self, unuse_N=False, use_skin_id=False):
        '''Return changed name

        Arg:
            unuse_N(Bool): _N 을 제거할지 여부

        Returns:
            name(str): 규칙에 맞게 변경된 이름. 오류가 날 경우 ""을 반환
        '''
        oflag = "" if unuse_N and self.flag == "N" else self.flag
        if self.flag == "E":
            return ""
        elif use_skin_id:
            return '_'.join([str(name) for name in [self.doll_id, self.skin_id, oflag] if name])
        else:
            return '_'.join([str(name) for name in [self.doll_id, self.skin_num, oflag] if name])

    def get_flag(self):
        return self.flag


# def _make_doll_lite():
#     with open("data/doll.json", 'r', encoding="utf-8") as f:
#         core = json.loads(f.read())

#     coreLite = []
#     for doll in core:
#         dollLite = {}
#         dollLite["id"] = doll["id"]
#         dollLite["name"] = doll["name"]
#         if not doll.get("skins"):
#             dollLite["skins"] = []
#         else:
#             dollLite["skins"] = doll["skins"]
#         dollLite["skinId"] = []
#         coreLite.append(dollLite)

#     with open("data/dollLite.json", "w", encoding="utf-8") as f:
#         f.write(json.dumps(coreLite, indent=4, ensure_ascii=False))
#     return coreLite


# def _add_doll_lite(sid, did):
#     for doll in core:
#         if doll["id"] == did and sid:
#             skinList = set(doll["skinId"])
#             skinList.add(int(sid))
#             skinList = list(skinList)
#             skinList.sort()
#             core[core.index(doll)]["skinId"] = skinList
#             break
#     return core


# def _write_doll_lite():
#     # dollLite.json 에 skinId 정보를 추가합니다.
#     # 일반적으로는 쓰지 않습니다.
#     allFileList = glob.glob("charactor/Texture2D/*.png")
#     alphaFileList = glob.glob("charactor/Texture2D/*_alpha.png")
#     fileList = list(set(allFileList) - set(alphaFileList))
#     for fileName in fileList:
#         info = doll(fileName[20:])
#         if info:
#             did, sid = info[:2]
#         else:
#             continue
#         corex = _add_doll_lite(sid, did)
#     with open("data/dollLite.json", "w", encoding="utf-8") as f:
#         f.write(json.dumps(corex, indent=4, ensure_ascii=False))


if __name__ == '__main__':
    # # 시간 측정 시작
    # start_time = time.time()

    # allFileList = glob.glob("charactor/Texture2D/*.png")
    # alphaFileList = glob.glob("charactor/Texture2D/*_alpha.png")
    # fileList = list(set(allFileList) - set(alphaFileList))
    # # fileList = [name for name in allFileList if name not in alphaFileList] 느려서 안씀
    # '''
    # for fileName in fileList:
    #     info = doll(fileName[20:],False)

    #     if not info:
    #         continue

    #     #print("{0}\t{1}\t{2}\t{3}".format(did,sid,flag,dname))
    #     print(info)
    # '''
    # print(doll("pic_BB_Noel_1.png"))
    # print(doll("pic_64type.png"))

    # # 시간측정 종료
    # print("--- %s seconds ---" % (time.time() - start_time))
    print(Doll("res/char/pic_BB_Noel_1.png").get_all())
