import os
import json
import numpy as np
import cv2
import unitypack
import configparser
import logging

import etcpy

from modules import rename


config = configparser.ConfigParser()
try:
    config.read("config.ini", encoding="utf-8")
except configparser.MissingSectionHeaderError:
    config.read("config.ini", encoding="utf-8-sig")

save_alpha_image = config.getboolean('abunpack', 'save_alpha_image')
image_compression = config.getint('abunpack', 'image_compression')
use_object_name = config.getboolean('abunpack', 'use_object_name')
force_alpha_channel_remove = config.getboolean('abunpack', 'force_alpha_channel_remove')
make_doll_icon = config.getboolean('abunpack', 'make_doll_icon')

rn_doll = config.getboolean("abunpack", "rename_doll")
rn_doll_id = config.getboolean('abunpack', 'rename_doll_id')
rn_doll_skin_id = config.getboolean('abunpack', 'rename_doll_skin_id')
rn_remove_n = config.getboolean('abunpack', 'rename_remove_n')
split_dummy_image_folder = config.getboolean('abunpack', 'split_dummy_image_folder')

rn_equip = config.getboolean("abunpack", "rename_equip")

sp_remove_type_ext = config.getboolean("abunpack", "spine_remove_type_ext")
sp_folder_skin_id_remove = config.getboolean("abunpack", "spine_folder_skin_id_remove")
sp_folder_original_name = config.getboolean("abunpack", "spine_folder_original_name")

logger = logging.getLogger("AssetBundle")


class ImageResource():
    icon_rate2 = cv2.imread(config['data']['icon_rate2'], -1)
    icon_rate3 = cv2.imread(config['data']['icon_rate3'], -1)
    icon_rate4 = cv2.imread(config['data']['icon_rate4'], -1)
    icon_rate5 = cv2.imread(config['data']['icon_rate5'], -1)


def make_container(assetbundle_data):
    """Asset 인스턴스 받아서 id: container (파일의 경로) 로 저장
    AssetStudio 에서 실제 이름 표시 옵션 키면 나오는 그 이름이 나옴
    """
    container = {}
    get_list = ["TextAsset", "Texture2D"]
    data = assetbundle_data.read()["m_Container"]
    for n in data:
        if n[1]['asset'].object.type not in get_list:
            continue
        container[n[1]['asset'].path_id] = n[0]
    return container


def eq_path(value1: str, value2: str) -> bool:
    """경로 두가지를 받아서 비교. 반드시 / 만 사용.
    패턴 사이에 빈공간이 있으면 모든 값이 있어도 되는것으로 판단

    Args:
        value1(str): 비교대상
        value2(str): 패턴(즉 value1이 value2에 맞는지 순차적으로 실험)

    Return:
        ret(bool): 참/거짓
    """
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

    def remove_alpha_channel(self):
        if self.shape[2] == 4:
            self.image = self.image[:, :, :3]
        else:
            pass

    def make_icon(self, rank, path, name):
        if self.shape == (512, 512, 3):
            if rank == 2:
                data = ImageResource.icon_rate2[:, :, :]
            elif rank == 3:
                data = ImageResource.icon_rate3[:, :, :]
            elif rank == 4:
                data = ImageResource.icon_rate4[:, :, :]
            elif rank == 5:
                data = ImageResource.icon_rate5[:, :, :]
            else:
                return
            data[31:227, 31:227, :3] = self.image[16:212, 31:227]
            icon = ResImage(data)
            icon.set_path(path, name)
            icon.save()
        else:
            return

    def save(self, compression=image_compression):
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
        """Unitypack 을 이용해 로드한 AssetBundle 내 개별 Asset 을 받아서 처리하는 클래스

        Arg:
            asset(unitypack.asset.Asset): Unitypack 으로 로드한 AssetBundle 중 asset
        """
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
            if len(data.data) == 0:
                logger.warning("Data doesn't exist")
                return Resource()
            if data.format.name == 'ETC_RGB4':
                # 이미지 포맷: ETC1 -> RGB(A)
                # Alpha 채널도 나오긴 하는데 의미 없어서 자름
                im_r, im_g, im_b = cv2.split(np.fromstring(
                    etcpy.decode_etc1(data.data, data.width, data.height), np.uint8
                ).reshape(data.width, data.height, 4))[:3]
                # 알파 이미지 위치를 찾기 위한 변수.
                # 예시: assets/character/m1918/pic/pic_m1918, png
                im_a_dir, im_a_ext = self.container[path_id].split('.')
                # 예시: assets/character/m1918/pic/pic_m1918_alpha.png
                im_a_path = im_a_dir + "_alpha." + im_a_ext
                # 위에서 만든 im_a_path 가 처음에 만든 파일 목록에 있는지 확인
                if im_a_path in self.container.values():
                    # 재귀적으로 알파 채널 이미지 찾아옴
                    im_a = self.get_resource(self.find_path_id(im_a_path)).image
                    # 알파 채널 이미지가 원래 이미지와 크기가 다른 경우가 있는 경우를 위한 리사이징
                    if im_a.shape[:2] != (data.width, data.height):
                        im_a = cv2.resize(im_a, None, fx=2, fy=2)
                    return ResImage(cv2.merge((im_b, im_g, im_r, im_a)), data.name)
                else:
                    return ResImage(cv2.merge((im_b, im_g, im_r)), data.name)
            elif data.format.name == 'RGBA32':
                # 이미지 포맷: RGBA32 -> RGBA
                im = np.fromstring(data.data, 'uint8').reshape(data.height, data.width, 4)
                # cv2에서는 BGRA 색역을 쓰기 때문에 변한
                im = cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA)
                # 소전은 뒤집힌거 쓰니까 이미지 뒤집기
                im = cv2.flip(im, 0)
                return ResImage(im, data.name)
            elif data.format.name == 'RGBA4444':
                shape = (data.height, data.width)
                # numpy array로 변환 (아직 1차원 배열)
                im_array = np.fromstring(data.data, dtype=np.uint8)
                # 비트 시프트 + 값 곱하기 후 3차원 배열로 만든 후 채널별로 분리
                # 0x0 -> 0x00, 0x1 -> 0x11, ... , 0xF -> 0xFF
                im_b, im_r = cv2.split((np.bitwise_and(im_array >> 4, 0x0f) * 17).reshape(*shape, 2))
                im_a, im_g = cv2.split((np.bitwise_and(im_array, 0x0f) * 17).reshape(*shape, 2))
                # 합쳐서 Return
                return ResImage(cv2.flip(cv2.merge((im_b, im_g, im_r, im_a)), 0), data.name)
            elif data.format.name == 'ARGB32':
                # 이미지 포맷: ARGB32 -> RGBA
                # 채널별로 분리 후 다시 합침
                # 이상하게 원래 크기 이상으로 뭔가 데이터가 있는데 딱히 필요는 없어서 모양으로 계산해서 필요한 부분만 슬라이싱
                data_size = data.height * data.width * 4
                im_array = np.fromstring(data.data[:data_size], dtype=np.uint8).reshape(data.height, data.width, 4)
                im_a, im_r, im_g, im_b = cv2.split(cv2.flip(im_array, 0))
                return ResImage(cv2.merge((im_b, im_g, im_r, im_a)), data.name)
            elif data.format.name == 'Alpha8':
                # 알파 이미지
                shape = (data.height, data.width)
                return ResImage(cv2.flip(np.fromstring(data.data, "uint8").reshape(shape), 0), data.name)
            elif data.format.name == 'RGB24':
                # 이미지 포맷: RGB24 -> RGB
                # 간단하게 처리
                data_size = data.height * data.width * 3
                im_array = np.fromstring(data.data[:data_size], dtype=np.uint8).reshape(data.height, data.width, 3)
                return ResImage(cv2.flip(cv2.cvtColor(im_array, cv2.COLOR_RGB2BGR), 0), data.name)
            else:
                # 모르는 포맷은 그냥 건너뜀
                return Resource(data.name)
        elif obj.type == 'TextAsset':
            data = obj.read()
            if isinstance(data.script, str):
                # 데이터가 일반 텍스트(txt)인경우 str 로 리턴
                return ResText(data.script, data.name)
            else:
                # 아니면 Bytes 형태로 리턴
                return ResBytes(data.bytes, data.name)
        else:
            return Resource()

    def save_original_resources(self):
        """어셋번들 내 파일들을 경로 그대로 저장.
        모든 이미지와 텍스트류 파일을 저장하지만 특수 처리는 하지 않습니다.
        """
        for path_id, cnt in self.container.items():
            res = self.get_resource(path_id)
            res.set_path(*os.path.split(cnt))
            res.save()
        return

    def save_processed_resources(self):
        """리소스를 처리한 후 저장. 모든 옵션(이름 바꾸기 등) 사용 가능
        """
        for path_id, cnt in self.container.items():
            # split path
            path, name = os.path.split(cnt)
            name, ext = os.path.splitext(name)
            logger.info(f"{path}/{name}")
            # resource get
            res = self.get_resource(path_id)

            if use_object_name:
                name = res.obj_name

            # Resources::Text::table
            if eq_path(path, "assets/resources/dabao/table"):
                if name == "tableconfig":
                    res.set_path("text/table", "tableconfig")
                else:
                    res.table()
                    res.set_path("text/table", name)
                logger.info("-> Text::table")

            # Resources::Text::profilesconfig (인형 대사 등등)
            elif eq_path(path, "assets/resources/dabao/profilesconfig"):
                res.profilesconfig(name)
                res.set_path("text/profilesconfig", name)
                logger.info("-> Text::profilesconfig")

            # Resources::Text::avgtxt (일반 전역 대사)
            elif eq_path(path, "assets/resources/dabao/avgtxt"):
                res.set_path("text/avgtxt", name)
                logger.info("-> Text::avgtxt")

            # Resources::Text::avgtxt (전투중 전역 대사?)
            elif eq_path(path, "assets/resources/dabao/avgtxt/battleavg"):
                res.set_path("text/avgtxt/battleavg", name)
                logger.info("-> Text::avgtxt::battleavg")

            # Resources::Text::avgtxt (개조 스토리)
            elif eq_path(path, "assets/resources/dabao/avgtxt/memoir"):
                res.set_path("text/avgtxt/memoir", name)
                logger.info("-> Text::avgtxt::memoir")

            # Resources::Text::avgtxt (스킨 스토리)
            elif eq_path(path, "assets/resources/dabao/avgtxt/skin"):
                res.set_path("text/avgtxt/skin", name)
                logger.info("-> Text::avgtxt::skin")

            # Resources::Text::avglang (스토리 언어별 텍스트)
            elif eq_path(path, "assets/resources/dabao/avglanguage"):
                res.set_path("text/avglang", name)
                logger.info("-> Text::avglang")

            # Resources::Text::avgtxt (튜토리얼?)
            elif eq_path(path, "assets/resources/dabao/avgtxt/startavg"):
                res.set_path("text/avgtxt/startavg", name)
                logger.info("-> Text::avgtxt::startavg")

            # Resources::fairy (요정 대형)
            elif eq_path(path, "assets/resources/dabao/pics/fairy"):
                res.set_path("fairy", name)
                logger.info("-> Resources::fairy")

            # Resources::fairy::battle (요정 소형)
            elif eq_path(path, "assets/resources/dabao/pics/fairy/battle"):
                res.set_path("fairy/battle", name)
                logger.info("-> Resources::fairy::battle")

            # Resources::icon::equip (장비 아이콘)
            elif eq_path(path, "assets/resources/dabao/pics/icons/equip"):
                new_path = "icon/equip"
                if rn_equip:
                    # 장비 이름 변경
                    rn = rename.Equip(name)
                    name = rn.get_name()
                    # 이름 변경 오류시(한자 포함 등등) 더미폴더로 이동
                    if rn.flag == 'E':
                        new_path = "icon/equip/dummy"
                res.set_path(new_path, name)
                logger.info("-> Resources::icon::equip")

            # Resources::pic::squads (지원소대)
            elif eq_path(path, "assets/resources/dabao/pics/squads"):
                res.set_path("res/pic/squads", name)
                logger.info("-> Resources::pic::squads")

            # Character::pic (인형 일러스트)
            elif eq_path(path, "assets/characters//pic"):
                new_path = "pic"
                char_name = path.split('/')[2]
                if rn_doll:
                    # 인형 이름 바꾸기 + 옵션 전달
                    rn = rename.Doll(name, rn_doll_id, rn_doll_skin_id, rn_remove_n)
                    name = rn.get_name()
                    if rn.flag == 'E':
                        # Flag가 E(오류)면 더미 폴더 이동. 필요에 따라 인형별 폴더 분리
                        new_path = f"pic/dummy/{char_name}" if split_dummy_image_folder else "pic/dummy"
                    if rn.flag == 'N' and rn_remove_n:
                        # 옵션에 따라 _N이 붙은 이미지들의 _N을 지우고 별도 폴더 이동
                        new_path = "pic/portraits"
                    if rn.flag == 'N' and make_doll_icon:
                        # 옵션값 참이면 _N 이미지 기반으로 아이콘 생섣
                        res.make_icon(rn.rank, "icon/doll", name)
                res.set_path(new_path, name)
                logger.info("-> Character::pic")
            elif eq_path(path, "assets/characters//pic_he"):
                res.set_path("pic_he", name)

            # Character::spine (인형 SD)
            elif eq_path(path, "assets/characters//spine"):
                new_path = path.split('/')[2]
                if sp_remove_type_ext and res.ext in ["bytes", "txt"]:
                    # 필요없는 확장자 제거 옵션
                    res.ext = ""
                if sp_folder_skin_id_remove:
                    # 폴더 이름에 (찾을 수 있으면) 대문자 포함된 이름 사용
                    new_path = rename.path_rename(path, original_name=sp_folder_original_name)
                res.set_path(f"spine/{new_path}", name)
                logger.info("-> Character::spine")

            # Sprites::skilicon (스킬 아이콘)
            elif eq_path(path, "assets/sprites/ui/icon/skillicon"):
                if force_alpha_channel_remove and isinstance(res, ResImage):
                    # 알파 채널 이미지 강제 제거 여부에 따른 결과
                    res.remove_alpha_channel()
                res.set_path("icon/skilicon", name)
                logger.info("-> Sprites::skilicon")

            # 예외처리
            else:
                logger.info("-> Pass")
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
    abunpack("dist/resource_squads.ab")
    print("stop")
