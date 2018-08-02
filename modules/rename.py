import re
import json
import os
import configparser


print(os.getcwd())
config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")
with open(config['json']['doll'], 'r', encoding="utf-8") as f:
    core = json.loads(f.read())
with open(config['json']['rename'], 'r', encoding='utf-8') as f:
    rename_data = json.loads(f.read())
    equip_cat = rename_data['equip_cat']
    equip_type = rename_data['equip_type']
    equip_etc = rename_data['equip_etc']
    doll_except = rename_data['doll_except']


def gfl_core_doll(name, sid=0) -> (int, int):
    """doll.json 에서 인형 id, 스킨 id 읽어오는 함수

    Args:
        name(str): 인형 이름
        sid(int): 스킨 번호(1904 등등)

    Return:
        doll_id(int): 인형 도감번호
        doll_skin_num(int): 인형 스킨순번. 오류시 0 반환
    """

    # 예외처리
    for i, j in doll_except.items():
        if name == j:
            name = i
    # 아이디/스킨아이디 찾기, 현재 비교시 소문자 변환 과정을 거침
    for doll in core:
        if doll["name"].lower() == name.lower():
            doll_id = doll["id"]
            doll_skins = [int(n) for n in doll["skins"].keys()]
            if sid in doll_skins:
                return doll_id, doll_skins.index(sid) + 1
            return doll_id, 0
    else:
        return None, None


class Equip():
    """중국어로 되어있는 장비이름을 한국어로 대응-변환

    Args:
        equip_name (str) : 원본 이미지 이름
        adv (bool) : 특수 장비 이름 변환 여부
    """
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
        if re.search('[^a-z0-9/_.-]+[._]', self.name):
            self.flag = "E"

    def get_name(self):
        """return name

        Return:
            name(str): 바뀐 장비 이름 반환
        """
        return self.name


class Doll():
    def __init__(self, name, name_to_id=True, skin_id_to_num=False, remove_n=False):
        """Rename Doll resource file

        Args:
            name(str): 'pic_(name)[_skin_id][_flag][_alpha]' 형식
            name_to_id(bool): 인형 이름 -> 인형 도감번호 변경 여부
            skin_id_to_num(bool): 스킨 아이디(_1302 모양)를 해당 인형의 n번째 스킨번호로 변경할지 여부
            remove_n(bool): _n flag를 지울지 말지 결정
        """
        self.ret = []
        self.flag = "N"
        re_name = re.search("pic_(.+?)(_[0-9]+)?(_[NnMmDd])?(_alpha)?$", name)
        if re_name:
            # 정규표현식 이용, groups 메소드로 분할
            doll_name, skin_id, flag, alpha = re_name.groups()
            skin_id = int(skin_id[1:]) if skin_id else 0
            self.flag = flag[-1].upper()

            # 이름/스킨번호 변경
            if name_to_id or skin_id_to_num:
                doll_id, skin_num = gfl_core_doll(doll_name.lower(), skin_id)

                # 이름 변경 여부 확인 후 self.ret 에 append
                if doll_id and name_to_id:
                    self.ret.append(str(doll_id))
                elif doll_id:
                    self.ret.append(doll_name)
                else:
                    self.ret.append(doll_name)
                    self.flag = 'E'

                # 스킨번호 변경 여부 확인 후 self.ret 에 append
                if skin_num and skin_id_to_num:
                    # skin_num 변경옵션 O + 스킨 정보 일치
                    self.ret.append(str(skin_num))
                elif skin_num:
                    # 스킨 정보만 일치
                    self.ret.append(str(skin_id))
                elif skin_id:
                    # 스킨 정보 불일치 + 스킨 id 존재
                    self.ret.append(str(skin_id))
                    self.flag = 'E'
                elif skin_id == 0:
                    # 스킨 정보 공란
                    pass
                else:
                    # 스킨 정보 불일치 + 스킨 id 미존재
                    self.flag = 'E'

            # remove_n 옵션 확인 후 True 인 경우 그냥 넘어감
            # 그렇지 않으면 기존 flag 도 append
            if self.flag == 'N' and remove_n:
                pass
            elif flag:
                self.ret.append(flag[-1].upper())

            # 기존 파일명에 _alpha 있었으면 append
            if alpha:
                self.ret.append("Alpha")
        else:
            # 정규표현식 오류날 경우 self.ret 에 변경되지 않은 이름 append
            # self.flag E(Error) 등록
            self.ret.append(name)
            self.flag = "E"

    def get_name(self):
        """Return changed name

        Return:
            name(str): 규칙에 맞게 변경된 이름. 오류가 날 경우 ""을 반환
        """
        return '_'.join(self.ret)


if __name__ == '__main__':
    print(os.getcwd())
    # print(gfl_core_doll("zastavam21", 1253))
    x = Doll("pic_zastavam21_1253_d")
    print(f"result: {x.get_name()}, {x.flag}")
