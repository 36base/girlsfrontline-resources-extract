# girlsfrontline-resources-extract

본 레포는 [girlsfrontline-resources](https://github.com/36base/girlsfrontline-resources) 에서 사용되는 게임 **소녀전선**의 리소스를 추출하는 법을 문서화하고, 이에 사용하는 스크립트를 공유하기 위해 만들어졌습니다.

건의사항 및 버그 제보는 GitHub Issue를 이용해주세요. 가능하면 24시간 이내로 답변드리겠습니다.

PR은 언제나 환영합니다. 주석도 많이 달았습니다. 주로 만드는 놈이 고3이라 도와주시면 감사하겠습니다.

## Requirements

`Python 3.6 (64-bit)` 또는 그 이상의 버전을 요구합니다. `32-bit`에서의 정상작동은 보장하지 못합니다.

실행을 위하여 아래 추가 패키지가 필요합니다. 오디오 추출을 위한 [hcapy](https://github.com/krepe-suZette/hcapy)와 이미지 추출을 위한 [pyetc](https://github.com/krepe-suZette/pyetc)는 pypi에 등록되지 않았기 떄문에 수동으로 설치하셔야 합니다.
* numpy
* opencv-python
* configparser
* requests
* [unitypack](https://github.com/HearthSim/UnityPack)
* [hcapy](https://github.com/krepe-suZette/hcapy)
* [pyetc](https://github.com/krepe-suZette/pyetc)

## Process
- [x] 레포 등록
- [x] AssetBundle 설명 작성
- [x] ab 파일 처리 기능 구현
- [x] acb 파일 처리 기능 구현
- [x] 아이콘 만들기 기능
- [x] 로깅
- [x] 코드를 건드리지 않는 파일 출력 경로 변경 기능
- [x] GitHub Wiki 에 설명 깔끔하게 올리기

## Wiki
[GitHub Wiki](/wiki)에 모든 가이드를 작성할 예정입니다. 참조해주세요.
