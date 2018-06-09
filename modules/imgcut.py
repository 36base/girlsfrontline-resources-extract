import numpy as np
import cv2
import glob
from multiprocessing import Pool


def show(image, title=''):
    cv2.imshow('Image Preview : %s' % title, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def cutimg(imgData):
    '''
    cv2에서 사용하는 이미지 데이터를 넣어주시면 됩니다.\n
    (x,y,ch) 의 3차원 uint8 배열
    '''
    if imgData.shape != (1024, 1024, 4):
        return imgData
    ux, uy, dx, dy = 0, 0, 0, 0
    for i in range(0, 16):
        if np.sum(imgData[i * 64:(i + 1) * 64, :, 3]) == 0:
            uy += 1
        else:
            break
    for i in range(0, 16):
        if np.sum(imgData[:, i * 64:(i + 1) * 64, 3]) == 0:
            ux += 1
        else:
            break
    for i in reversed(range(0, 16)):
        if np.sum(imgData[i * 64:(i + 1) * 64, :, 3]) == 0:
            dy += 1
        else:
            break
    for i in reversed(range(0, 16)):
        if np.sum(imgData[:, i * 64:(i + 1) * 64, 3]) == 0:
            dx += 1
        else:
            break

    # print(ux,uy,16-dx,16-dy)
    ly, lx = (16 - dy - uy) * 64, (16 - dx - ux) * 64
    # 세로 길이가 더 긴경우
    if lx <= ly:
        l = ly / 2
    else:
        l = lx / 2

    sx = int(((16 + ux - dx) / 2 * 64) - l)
    sy = int(((16 + uy - dy) / 2 * 64) - l)
    ex = int(((16 + ux - dx) / 2 * 64) + l)
    ey = int(((16 + uy - dy) / 2 * 64) + l)

    # print('x좌표 : %d,%d\ny좌표 : %d,%d'%(sx,ex,sy,ey))

    if sx < 0:
        ex = ex - sx
        sx = 0
    if sy < 0:
        ey = ey - sy
        sy = 0
    if ex > 1024:
        sx = sx - (ex - 1024)
    if ey > 1024:
        sy = sy - (ey - 1024)

    crop = imgData[sy:ey, sx:ex]
    return crop


def main(imgName):
    img = cv2.imread(imgName, -1)
    crop = cutimg(img)
    show(crop)
    if crop.shape == (1024, 1024, 4):
        print(imgName)
    # cv2.imwrite(imgName,crop,[16,5])


if __name__ == '__main__':
    fileList = glob.glob("output\\*.png")
    print(fileList)
    pool = Pool(processes=12)
    pool.map(main, fileList)
    print('end')
