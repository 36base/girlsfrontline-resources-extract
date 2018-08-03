import os
import json
import numpy as np
import cv2
import unitypack
import configparser

import etcpy

from modules import rename


config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")

save_alpha_image = config.getboolean('abunpack', 'save_alpha_image')
use_object_name = config.getboolean('abunpack', 'use_object_name')

rn_doll = config.getboolean("abunpack", "rename_doll")
rn_doll_id = config.getboolean('abunpack', 'rename_doll_id')
rn_doll_skin_id = config.getboolean('abunpack', 'rename_doll_skin_id')
rn_remove_n = config.getboolean('abunpack', 'rename_remove_n')

rn_equip = config.getboolean("abunpack", "rename_equip")

sp_remove_type_ext = config.getboolean("abunpack", "spine_remove_type_ext")
sp_folder_skin_id_remove = config.getboolean("abunpack", "spine_folder_skin_id_remove")
sp_folder_original_name = config.getboolean("abunpack", "spine_folder_original_name")


def make_container(assetbundle_data):
    container = {}
    get_list = ["TextAsset", "Texture2D"]
    data = assetbundle_data.read()["m_Container"]
    for n in data:
        if n[1]['asset'].object.type not in get_list:
            continue
        container[n[1]['asset'].path_id] = n[0]
    return container


def eq_path(value1: str, value2: str) -> bool:
    # ori: 비교대상
    # con: 패턴
    ori = value1.split("/")
    con = value2.split("/")
    if len(ori) != len(con):
        return False
    for n, i in enumerate(con):
        if i == "":
            continue
        elif i != ori[n]:
            return False
        else:
            continue
    else:
        return True


class Resource:
    def __init__(self, obj_name=''):
        self.data = None
        self.type = ''
        self.ext = ''
        self.path = ""
        self.name = ""
        self.obj_name = obj_name

    def set_path(self, path: str, name: str):
        self.path = path
        self.name = name

    def save(self):
        if self.data is None:
            return
        path = os.path.join(self.path, f"{self.name}.{self.ext}")
        os.makedirs(self.path, exist_ok=True)
        mode = {'mode': 'w', 'encoding': 'utf-8'} if self.type == 'text' else {'mode': 'wb'}
        with open(path, **mode) as f:
            f.write(self.data)


class ResImage(Resource):
    def __init__(self, data: np.ndarray, obj_name=''):
        self.type = 'image'
        self.image = data
        self.shape = data.shape
        self.ext = "png"
        self.obj_name = obj_name

    def save(self, compression=5):
        path = os.path.join(self.path, f"{self.name}.{self.ext}")
        if "_Alpha" in self.name and not save_alpha_image:
            return
        os.makedirs(self.path, exist_ok=True)
        if len(self.shape) == 2:
            self.image = cv2.merge(((self.image, ) * 3))
        self.data = cv2.imencode('.png', self.image, [16, 5])[1]
        with open(path, 'wb') as f:
            f.write(self.data)


class ResText(Resource):
    def __init__(self, data: str, obj_name=''):
        self.type = 'text'
        self.text = data
        self.data = data
        self.ext = "txt"
        self.obj_name = obj_name

    def table(self):
        table = {}
        for line in self.text.splitlines():
            if not line:
                continue
            n, m = line.split(",", 1)
            table[n] = m.replace("//c", ",")
        self.data = json.dumps(table, indent=2, ensure_ascii=False)
        self.ext = "json"

    def profilesconfig(self, mode="default"):
        ret = {}
        if mode in ["charactervoice", "newcharactervoice"]:
            for line in self.text.splitlines():
                if line[:2] == "//":
                    continue
                doll_name, char_voice_type, char_voice = line.split("|")
                char_voice.replace("\\n", "\n")
                char_voice_type = char_voice_type.lower()
                ret[doll_name] = dict(ret.get(doll_name, {}), **{char_voice_type: char_voice.split('<>')})
        elif mode == "kalinalevelvoice":
            for line in self.text.splitlines():
                if line[:2] == "//":
                    continue
                voice_type, etc = line.split("|", 1)
                if voice_type == "level":
                    level, voice_id, voice = etc.split("|")
                    ret[voice_type + level] = dict(ret.get(voice_type + level, {}), **{voice_id: voice})
                else:
                    voice_id, voice = etc.split("|")
                    ret[voice_type] = dict(ret.get(voice_type, {}), **{voice_id: voice})
        else:
            return
        self.data = json.dumps(ret, indent=2, ensure_ascii=False)
        self.ext = "json"
        return


class ResBytes(Resource):
    def __init__(self, data: bytes, obj_name=''):
        self.type = 'binary'
        self.data = data
        self.ext = "bytes"
        self.obj_name = obj_name


class Asset():
    def __init__(self, asset):
        self.asset = asset
        self.container = make_container(asset.objects[1])

    def get_object(self, path_id=0, res_cont=""):
        if path_id:
            return self.asset.objects[path_id].read()
        elif res_cont:
            for i, j in self.container.items():
                if res_cont == j:
                    return i
        else:
            raise TypeError()

    def find_path_id(self, container: dict):
        for i, j in self.container.items():
            if container == j:
                return i
        else:
            return None

    def get_resource(self, path_id: int):
        obj = self.asset.objects[path_id]
        if obj.type == 'Texture2D':
            data = obj.read()
            if data.format.name == 'ETC_RGB4':
                im_r, im_g, im_b = cv2.split(np.fromstring(
                    etcpy.decode_etc1(data.data, data.width, data.height), np.uint8
                ).reshape(data.width, data.height, 4))[:3]
                im_a_dir, im_a_ext = self.container[path_id].split('.')
                im_a_path = im_a_dir + "_alpha." + im_a_ext
                if im_a_path in self.container.values():
                    im_a = self.get_resource(self.find_path_id(im_a_path)).image
                    if im_a.shape[:2] != (data.width, data.height):
                        im_a = cv2.resize(im_a, None, fx=2, fy=2)
                    return ResImage(cv2.merge((im_b, im_g, im_r, im_a)), data.name)
                else:
                    return ResImage(cv2.merge((im_b, im_g, im_r)), data.name)
            elif data.format.name == 'RGBA32':
                im = np.fromstring(data.data, 'uint8').reshape(data.width, data.height, 4)
                im = cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA)
                im = cv2.flip(im, 0)
                return ResImage(im, data.name)
            elif data.format.name == 'RGBA4444':
                shape = (data.height, data.width)
                im_array = np.fromstring(data.data, dtype=np.uint8)
                im_b, im_r = cv2.split((np.bitwise_and(im_array >> 4, 0x0f) * 17).reshape(*shape, 2))
                im_a, im_g = cv2.split((np.bitwise_and(im_array, 0x0f) * 17).reshape(*shape, 2))
                return ResImage(cv2.flip(cv2.merge((im_b, im_g, im_r, im_a)), 0), data.name)
            elif data.format.name == 'ARGB32':
                data_size = data.height * data.width * 4
                im_array = np.fromstring(data.data[:data_size], dtype=np.uint8).reshape(data.height, data.width, 4)
                im_a, im_r, im_g, im_b = cv2.split(cv2.flip(im_array, 0))
                return ResImage(cv2.merge((im_b, im_g, im_r, im_a)), data.name)
            elif data.format.name == 'Alpha8':
                shape = (data.height, data.width)
                return ResImage(cv2.flip(np.fromstring(data.data, "uint8").reshape(shape), 0), data.name)
            elif data.format.name == 'RGB24':
                data_size = data.height * data.width * 3
                im_array = np.fromstring(data.data[:data_size], dtype=np.uint8).reshape(data.height, data.width, 3)
                return ResImage(cv2.flip(cv2.cvtColor(im_array, cv2.COLOR_RGB2BGR), 0), data.name)
            else:
                return Resource(data.name)
        elif obj.type == 'TextAsset':
            data = obj.read()
            if isinstance(data.script, str):
                return ResText(data.script, data.name)
            else:
                return ResBytes(data.bytes, data.name)
        else:
            return Resource()

    def save_original_resources(self):
        """어셋번들 내 파일들을 그대로 저장
        """
        for path_id, cnt in self.container.items():
            res = self.get_resource(path_id)
            res.set_path(*os.path.split(cnt))
            res.save()
        return

    def save_processed_resources(self):
        """36베이스용으로 처리된 리소스'만'저장
        """
        for path_id, cnt in self.container.items():
            res = self.get_resource(path_id)
            # split path
            path, name = os.path.split(cnt)
            name, ext = os.path.splitext(name)
            print(f"{path}/{name}")

            if use_object_name:
                name = res.obj_name

            # Resources::Text::table
            if eq_path(path, "assets/resources/dabao/table"):
                if name == "tableconfig":
                    res.set_path("text/table", "tableconfig")
                else:
                    res.table()
                    res.set_path("text/table", name)
                print("\tText::table")

            # Resources::Text::profilesconfig (인형 대사 등등)
            elif eq_path(path, "assets/resources/dabao/profilesconfig"):
                res.profilesconfig(name)
                res.set_path("text/profilesconfig", name)
                print("\tText::profilesconfig")

            # Resources::Text::avgtxt (일반 전역 대사)
            elif eq_path(path, "assets/resources/dabao/avgtxt"):
                res.set_path("text/avgtxt", name)
                print("\tText::avgtxt")

            # Resources::Text::avgtxt (전투중 전역 대사?)
            elif eq_path(path, "assets/resources/dabao/avgtxt/battleavg"):
                res.set_path("text/avgtxt/battleavg", name)
                print("\tText::avgtxt::battleavg")

            # Resources::Text::avgtxt (개조 스토리)
            elif eq_path(path, "assets/resources/dabao/avgtxt/memoir"):
                res.set_path("text/avgtxt/memoir", name)
                print("\tText::avgtxt::memoir")

            # Resources::Text::avgtxt (스킨 스토리)
            elif eq_path(path, "assets/resources/dabao/avgtxt/skin"):
                res.set_path("text/avgtxt/skin", name)
                print("\tText::avgtxt::skin")

            # Resources::Text::avgtxt (튜토리얼?)
            elif eq_path(path, "assets/resources/dabao/avgtxt/startavg"):
                res.set_path("text/avgtxt/startavg", name)
                print("\tText::avgtxt::startavg")

            # Resources::fairy (요정 대형)
            elif eq_path(path, "assets/resources/dabao/pics/fairy"):
                res.set_path("fairy", name)
                print("\tResources::fairy")

            # Resources::fairy::battle (요정 소형)
            elif eq_path(path, "assets/resources/dabao/pics/fairy/battle"):
                res.set_path("fairy/battle", name)
                print("\tResources::fairy::battle")

            # Resources::icon::equip (장비 아이콘)
            elif eq_path(path, "assets/resources/dabao/pics/icons/equip"):
                new_path = "icon/equip"
                if rn_equip:
                    rn = rename.Equip(name)
                    name = rn.get_name()
                    if rn.flag == 'E':
                        new_path = "icon/equip/dummy"
                res.set_path(new_path, name)
                print("\tResources::icon::equip")

            # Character::pic (인형 일러스트)
            elif eq_path(path, "assets/characters//pic"):
                new_path = "pic"
                if rn_doll:
                    rn = rename.Doll(name, rn_doll_id, rn_doll_skin_id, rn_remove_n)
                    name = rn.get_name()
                    if rn.flag == 'E':
                        new_path = "pic/dummy"
                    if rn.flag == 'N' and rn_remove_n:
                        new_path = "pic/portraits"
                res.set_path(new_path, name)
                print("\tCharacter::pic")
            elif eq_path(path, "assets/characters//pic_he"):
                res.set_path("pic_he", name)

            # Character::spine (인형 SD)
            elif eq_path(path, "assets/characters//spine"):
                new_path = path.split('/')[2]
                if sp_remove_type_ext and res.ext in ["bytes", "txt"]:
                    res.ext = ""
                if sp_folder_skin_id_remove:
                    new_path = rename.path_rename(path, original_name=sp_folder_original_name)
                res.set_path(f"spine/{new_path}", name)
                print("\tCharacter::spine")

            # Sprites::skilicon (스킬 아이콘)
            elif eq_path(path, "assets/sprites/ui/icon/skillicon"):
                res.set_path("icon/skilicon", name)
                print("\tSprites::skilicon")

            # 예외처리
            else:
                print("\tPass")
                continue

            # 저장
            res.save()


def abunpack(file_dir: str):
    f = open(file_dir, "rb")
    bundle = unitypack.load(f)
    for asset in bundle.assets:
        a = Asset(asset)
        if config['abunpack']['extract_mode'] == "processed":
            a.save_processed_resources()
        else:
            a.save_original_resources()
    return


if __name__ == "__main__":
    # abunpack("character_m1014.ab")
    # abunpack("dist/sprites_ui.ab")
    abunpack("dist/character_sv98_502.ab")
    print("stop")
