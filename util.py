import os
import numpy as np
from scipy.stats import poisson
from skimage.transform import rescale, resize

import torch
import torch.nn as nn

## 네트워크 저장하기
def save(ckpt_dir, net, optim, epoch):
    if not os.path.exists(ckpt_dir):
        os.makedirs(ckpt_dir)

    torch.save({'net': net.state_dict(), 'optim': optim.state_dict()},
               '%s/model_epoch%d.pth' % (ckpt_dir, epoch))

## 네트워크 불러오기
def load(ckpt_dir, net, optim):
    if not os.path.exists(ckpt_dir):
        epoch = 0
        return net, optim, epoch

    ckpt_lst = os.listdir(ckpt_dir)
    ckpt_lst.sort(key=lambda f: int(''.join(filter(str.isdigit, f))))

    dict_model = torch.load('%s/%s' % (ckpt_dir, ckpt_lst[-1]))

    net.load_state_dict(dict_model['net'])
    optim.load_state_dict(dict_model['optim'])
    epoch = int(ckpt_lst[-1].split('epoch')[1].split('.pth')[0])

    return net, optim, epoch

## sampling 하기
def add_sampling(img, type="random", opts=None):
    sz = img.shape

    if type == "uniform":
        ds_y = opts[0].astype(np.int)
        ds_x = opts[1].astype(np.int)

        msk = np.zeros(sz)
        msk[::ds_y, ::ds_x, :] = 1

        dst = img * msk
    elif type == "random":
        prob = opts[0]
        rnd = np.random.rand(sz[0], sz[1], sz[2])
        msk = (rnd > prob).astype(np.float)
        dst = img * msk

        ### if, RGB color를 동일한 sampling mask 가지고 싶다면
        # rnd = np.random.rand(sz[0], sz[1], 1)  # single channel로 된 mask를
        # prob = 0.5
        # msk = (rnd > prob).astype(np.float)
        # msk = np.tile(msk, (1, 1, sz[2]))  # channel 방향으로 3번 복사
        # dst = img * msk

    elif type == "gaussian":
        x0 = opts[0]  # center position of x
        y0 = opts[1]  # center position of y
        sgmx = opts[2]  # sigma x
        sgmy = opts[3]  # sigma y
        a = opts[4]  # amplitude

        ly = np.linspace(-1, 1, sz[0])
        lx = np.linspace(-1, 1, sz[1])

        x, y = np.meshgrid(lx, ly)

        ## command + /
        gauss = a * np.exp(-((x - x0)**2/(2*sgmx**2) + (y - y0)**2/(2*sgmy**2)))
        #plt.imshow(gauss)
        gauss = np.tile(gauss[:, :, np.newaxis], (1, 1, sz[2])) # tile은 복붙의 의미
        rnd = np.random.rand(sz[0], sz[1], sz[2])
        msk = (rnd < gauss).astype(np.float)
        dst = img * msk
        #
        # # channel 방향으로 동일한 sampling
        # gauss = a * np.exp(-((x - x0) ** 2 / (2 * sgmx ** 2) + (y - y0) ** 2 / (2 * sgmy ** 2)))
        # # plt.imshow(gauss)
        # gauss = np.tile(gauss[:, :, np.newaxis], (1, 1, 1))  # tile은 복붙의 의미
        # rnd = np.random.rand(sz[0], sz[1], 1)
        # msk = (rnd < gauss).astype(np.float)
        # msk = np.tile(msk, (1, 1, sz[2]))
        #
        # dst = img * msk
    return dst

## Noise 추가하기
def add_noise(img, type="random", opts=None):
    sz = img.shape

    if type == "random":
        sgm = opts[0]
        noise = sgm / 255.0 * np.random.randn(sz[0], sz[1], sz[2])  # img가 normalized 되어 있기 때문에 꼭 sgm를 normalize 하기!
        dst = img + noise

    elif type == "poisson":
        dst = poisson.rvs(255.0 * img) / 255.0  # 포아송은 int scale로 값이 추가됨 -> 0~255로 discretization되어 있는 이미지를 가지고
        #                               noise 추가한 뒤, 다시 Normalization 해줌.
        noise = dst - img
    return dst

## Blurring 추가하기
def add_blur(img, type ="bilinear", opts=None):
    if type == "nearest":
        order = 0
    elif type == "bilinear":
        order = 1
    elif type == "biquadratic":
        order = 2
    elif type == "bicubic":
        order = 3
    elif type == "biquartic":
        order = 4
    elif type == "biquintic":
        order = 5

    sz = img.shape

    dw = opts[0]

    if len(opts) == 1:
        keepdim = True
    else:
        keepdim = opts[1]

    #dst = rescale(img, scale=(dw, dw, 1), order=order)

    dst = resize(img, output_shape=(sz[0] // dw, sz[1] // dw, sz[2]), order=order) # output size 고정해서 사용 가능.

    if keepdim:
        dst = resize(dst, output_shape=(sz[0], sz[1], sz[2]), order=order)

    return dst









