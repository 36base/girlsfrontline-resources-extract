import re
import json
import os
import configparser


config = configparser.ConfigParser()
try:
    config.read("config.ini", encoding="utf-8")
except configparser.MissingSectionHeaderError:
    config.read("config.ini", encoding="utf-8-sig")

core_version = config.getfloat("main", "core_version")
name_key = "name" if core_version < 2 else "codename"


class GFLCore():
    with open(config['json']['doll'], 'r', encoding="utf-8") as f:
        core = json.loads(f.read())
    with open(config['json']['rename'], 'r', encoding='utf-8') as f:
        rename_data = json.loads(f.read())
        equip_cat = rename_data['equip_cat']
        equip_type = rename_data['equip_type']
        equip_etc = rename_data['equip_etc']

    def __init__(self, codename='', doll_id=0):
        if codename or doll_id:
            for doll in GFLCore.core:
                if doll[name_key].lower() == codename.lower():
                    self.filtered = doll
                    break
                elif doll['id'] == doll_id:
                    self.filtered = doll
                    break
            else:
                self.filtered = {}

    def __getitem__(self, item):
        return self.filtered.get(item, 0)

    def skin_num(self, skin_id: int) -> int:
        if self.filtered:
            if core_version < 2:
                skins = [int(n) for n in self.filtered.get("skins", {}).keys()]
            else:
                skins = [int(n) for n in self.filtered.get("skins", [])]
            if skin_id in skins:
                return skins.index(skin_id) + 1
            else:
                return 0
        else:
            return 0


def path_rename(path: str, remove_name=False, remove_skin=True, original_name=True) -> str:
    """Container 경로에 포함된 인형 이름을 규칙에 따라 변환

    Args:
        path(str): Container (assets/characters/<name>/spine)
        remove_name(bool): 이름을 지움
        remove_skin(bool): 스킨 부분을 지움
        original_name(bool): 대문자를 사용하는 원래 이름을 찾아서 그걸 사용

    Return:
        renamed(str): Processed by option
    """
    ret = ''
    ori_name = path.split("/")[2]
    re_name = re.match("(.*?)(_[0-9]*)?$", ori_name)
    if re_name:
        name, skin = re_name.groups('')
        core = GFLCore(name)
        if remove_name:
            pass
        else:
            if original_name and core.filtered:
                name = core[name_key]
            ret = ret + name

        if remove_skin or not skin:
            pass
        else:
            ret = ret + skin
    return ret


def normalize(name: str) -> str:
    """일러 이름 정규화

    Arg:
        name(str): 일러 이름. 경로와 확장자 없어야함
    Return:
        name(str): 깔끔하게 바뀐 일러이름.
    """
    return re.sub("^Pic_", "pic_", name)


class Equip():
    """중국어로 되어있는 장비이름을 한국어로 대응-변환

    Args:
        equip_name (str) : 원본 이미지 이름
        adv (bool) : 특수 장비 이름 변환 여부
    """
    def __init__(self, equip_name: str, adv=True):
        self.name = equip_name
        self.flag = "N"
        for i, j in GFLCore.equip_cat.items():
            if i in self.name:
                self.name = self.name.replace(i, j)
                break
        for i, j in GFLCore.equip_type.items():
            if i in self.name:
                self.name = self.name.replace(i, j)
                break
        if adv:
            for i, j in GFLCore.equip_etc.items():
                if i in self.name:
                    self.name = self.name.replace(i, j)
                    break
        if re.search('[^a-z0-9/_.-]+$', self.name):
            self.flag = "E"

    def get_name(self) -> str:
        """return name

        Return:
            name(str): 바뀐 장비 이름 반환
        """
        return self.name


class Doll():
    def __init__(self, name: str, name_to_id=True, skin_id_to_num=False, remove_n=False):
        """Rename Doll resource file

        Args:
            name(str): 'pic_(name)[_skin_id][_flag][_alpha]' 형식
            name_to_id(bool): 인형 이름 -> 인형 도감번호 변경 여부
            skin_id_to_num(bool): 스킨 아이디(_1302 모양)를 해당 인형의 n번째 스킨번호로 변경할지 여부
            remove_n(bool): _n flag를 지울지 말지 결정
        """
        self.ret = []
        self.rank = 1
        re_name = re.search("pic_(.+?)(_[0-9]+)?(_[NnMmDd])?(_mod)?(_[Aa]lpha)?$", name)
        if re_name:
            # 정규표현식 이용, groups 메소드로 분할
            doll_name, skin_id, flag, mod, alpha = re_name.groups()
            skin_id = int(skin_id[1:]) if skin_id else 0
            # 기본(플래그 없음): S, 중상: D, 포트레이트: N
            self.flag = flag[-1].upper() if flag else "S"

            # 이름/스킨번호 변경
            if name_to_id or skin_id_to_num:
                core = GFLCore(doll_name)
                doll_id = core['id']
                skin_num = core.skin_num(skin_id)
                self.rank = core['rank']

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

            # 개장 + 포트레이트인 경우?
            if mod:
                core = GFLCore(doll_id=(20000 + doll_id))
                self.rank = core['rank']
                self.ret.append("mod")

            # 기존 파일명에 _alpha 있었으면 append
            if alpha:
                self.ret.append("Alpha")
        else:
            # 정규표현식 오류날 경우 self.ret 에 변경되지 않은 이름 append
            # self.flag E(Error) 등록
            self.ret.append(name)
            self.flag = "E"

    def get_name(self) -> str:
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
