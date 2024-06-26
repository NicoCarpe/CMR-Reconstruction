#!/usr/bin/env python3

import os
import numpy as np
import h5py
import torch
import imageio
import utils

def center_crop(data, shape):
    if shape[0] <= data.shape[-2]:
        w_from = (data.shape[-2] - shape[0]) // 2
        w_to = w_from + shape[0]
        data = data[..., w_from:w_to, :]
    else:
        w_before = (shape[0] - data.shape[-2]) // 2
        w_after = shape[0] - data.shape[-2] - w_before
        pad = [(0, 0)] * data.ndim
        pad[-2] = (w_before, w_after)
        data = np.pad(data, pad_width=pad, mode='constant', constant_values=0)
    if shape[1] <= data.shape[-1]:
        h_from = (data.shape[-1] - shape[1]) // 2
        h_to = h_from + shape[1]
        data = data[..., :, h_from:h_to]
    else:
        h_before = (shape[1] - data.shape[-1]) // 2
        h_after = shape[1] - data.shape[-1] - h_before
        pad = [(0, 0)] * data.ndim
        pad[-1] = (h_before, h_after)
        data = np.pad(data, pad_width=pad, mode='constant', constant_values=0)
    return data



"""
VolumeDataset: 
	Loads individual MRI volumes, processes the data, and ensures it's in a suitable format for further processing.

DummyVolumeDataset: 
	Provides placeholder data for missing volumes to maintain alignment.

AlignedVolumesDataset: 
	Aligns and manages multiple MRI volumes, ensuring they are processed together correctly.

tiffPaired: 
	Specifically handles paired TIFF images, processing them into a format compatible with the rest of the pipeline.

"""

class VolumeDataset(torch.utils.data.Dataset):
    def __init__(self, volume, crop=None, q=0, flatten_channels=False):
        super().__init__()
        assert q < 0.5
        self.volume = volume
        self.flatten_channels = flatten_channels
        self.crop = crop
        h5 = h5py.File(volume, 'r')
        if 'image' in h5:
            data = h5['image']
        elif 'kspace' in h5:
            data = h5['kspace']
        if len(data.shape) == 3:
            assert flatten_channels==False
            length, self.channels = data.shape[0], 1
        elif len(data.shape) == 4:
            length, self.channels = data.shape[0:2]
        else:
            assert False
        self.protocal = h5.attrs['acquisition']
        h5.close()
        self.start = round(length * q) # inclusive
        self.stop = length - self.start # exclusive

    def __len__(self):
        length = self.stop - self.start
        return length*self.channels if self.flatten_channels else length

    def __getitem__(self, index):
        h5 = h5py.File(self.volume, 'r')
        if 'image' in h5:
            data = h5['image']
        elif 'kspace' in h5:
            data = h5['kspace']
            data = utils.fftshift2(torch.from_numpy(np.array(data))) # make them at corners since mask is defined so.
            data = utils.ifft2(data) # image at corners
            data = utils.ifftshift2(data) # image centered for following normalization and crop
            data = data.numpy()
        if self.flatten_channels:
            i = data[index//self.channels + self.start]
            i = i[index%self.channels][()][None, ...]
        else:
            i = data[index + self.start][()]
            # extend channel for single-coiled data
            i = i if len(i.shape) == 3 else i[None, ...]
        #minVal = h5.attrs['minVal']
        minVal = 0
        maxVal = h5.attrs['max']
        h5.close()
        i = (i - minVal) / (maxVal - minVal)
        if self.crop is not None: i = center_crop(i, (self.crop, self.crop))
        # add dim for channel
        if len(i.shape) == 2: i = i[None, :, :]
        return i.astype(np.complex64)


class DummyVolumeDataset(torch.utils.data.Dataset):
    def __init__(self, ref):
        super().__init__()
        sample = ref[0]
        self.shape = sample.shape
        self.dtype = sample.dtype
        self.len = len(ref)

    def __len__(self):
        return self.len

    def __getitem__(self, index):
        return np.zeros(self.shape, dtype=self.dtype)


class AlignedVolumesDataset(torch.utils.data.Dataset):
    def __init__(self, *volumes, protocals, \
            crop=None, q=0, flatten_channels=False, exchange_Modal=False):
        super().__init__()
        volumes = [VolumeDataset(x, \
                crop, q=q, flatten_channels=flatten_channels) for x in volumes]
        assert len({len(x) for x in volumes}) == 1
        assert len({x[0].shape for x in volumes}) == 1
        self.crop = crop
        volumes = {volume.protocal:volume for volume in volumes}
        volumes['None'] = DummyVolumeDataset(next(iter(volumes.values())))

        if exchange_Modal == True:
            p=torch.rand(1)
            if p>0.5:
                protocals.reverse()

        for x in protocals:
            assert x in volumes.keys(), x+' not found in '+str(volumes.keys())
        volumes = [volumes[protocal] for protocal in protocals]
        
        self.volumes = volumes

    def __len__(self):
        return len(self.volumes[0])

    def __getitem__(self, index):
        images = [volume[index] for volume in self.volumes]
        return images


def get_paired_volume_datasets(csv_path, protocals=None, crop=None, q=0, flatten_channels=False, basepath=None, exchange_Modal =False):
    datasets = []
    for line in open(csv_path, 'r').readlines():
        basepath = basepath
        dataset = [os.path.join(basepath, filepath) \
                for filepath in line.strip().split(',')]
        dataset = AlignedVolumesDataset(*dataset, \
                protocals=protocals, crop=crop, q=q, \
                flatten_channels=flatten_channels, exchange_Modal=exchange_Modal)
        datasets.append(dataset)
    return datasets 


class tiffPaired(torch.utils.data.Dataset):
        def __init__(self, tiffs, crop = None):
            super().__init__()
            self.tiffs = tiffs
            self.crop = crop
        
        def __len__(self):
            return len(self.tiffs)

        def __getitem__(self, ind):
            img = imageio.imread(self.tiffs[ind])
            assert len(img.shape) == 2
            t1, t2 = np.split(img, 2, axis=-1)
            t1, t2 = map(lambda x: np.stack([x, np.zeros_like(x)], axis=0), \
                    (t1, t2))
            if self.crop is not None:
                t1, t2 = map(lambda x: center_crop(x, [self.crop]*2), \
                        (t1, t2))
            return t1, t2


if __name__ == '__main__':
    # test get_paired_volume_datasets
    datasets = get_paired_volume_datasets( \
            '/home/sunkg/Desktop/T1Flair_T2Flair_T2_train.csv',
            protocals=['T1Flair', 'T2'],
            flatten_channels=True)
    print(sum([len(dataset) for dataset in datasets]))
