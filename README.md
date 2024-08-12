# DEPRECATED!!!

2024년 4월 업데이트 이후로 ab 파일의 구조가 변경되면서 기존 추출기를 뜯어고쳐도 더 이상 동작하지 않게 되었습니다.

[여기](https://github.com/36base/resource-manager)에서 새 버전을 볼 수 있습니다!

## girlsfrontline-resources-extract

본 레포는 [girlsfrontline-resources](https://github.com/36base/girlsfrontline-resources) 에서 사용되는 게임 **소녀전선**의 리소스를 추출하는 법을 문서화하고, 이에 사용하는 스크립트를 공유하기 위해 만들어졌습니다.

### Requirements

`Python 3.6 (64-bit)` 또는 그 이상의 버전을 요구합니다. `32-bit`에서의 정상작동은 보장하지 못합니다.

실행을 위하여 아래 추가 패키지가 필요합니다. 오디오 추출을 위한 [hcapy](https://github.com/krepe-suZette/hcapy)와 이미지 추출을 위한 [pyetc](https://github.com/krepe-suZette/pyetc)는 pypi에 등록되지 않았기 떄문에 수동으로 설치하셔야 합니다.
* numpy
* opencv-python
* configparser
* requests
* [unitypack](https://github.com/HearthSim/UnityPack)
* [hcapy](https://github.com/krepe-suZette/hcapy)
* [pyetc](https://github.com/krepe-suZette/pyetc)
