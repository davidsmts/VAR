import scipy.io
import torch
import h5py
from torch.utils.data import Dataset
import numpy as np
import torchvision
from torchvision import models, transforms
from torchvision.transforms import ToTensor, Compose, Normalize, ToPILImage, CenterCrop, Resize
from tqdm import tqdm
from model import ResNet9


#data_in = h5py.File('./IDcat.mat', 'r')
#b = np.array(data_in['ans'],dtype='int').reshape(300)
datapath = './data'
s = 1
color_jitter = transforms.ColorJitter(
        0.9 * s, 0.9 * s, 0.9 * s, 0.1 * s)
flip = transforms.RandomHorizontalFlip()
Aug = transforms.Compose(
    [
    transforms.RandomResizedCrop(size=32),
    transforms.RandomVerticalFlip(p=0.5),
    transforms.RandomApply([transforms.ColorJitter], p=0.9),
    transforms.RandomGrayscale(p=0.1)
    ])
data_transforms = transforms.Compose(
            [
                ToTensor(),
                Normalize(0.5, 0.5)
            ])
CIFAR_10_Dataset = torchvision.datasets.CIFAR10(datapath, train=True, download=False,
                                                 transform=data_transforms)
sublist = list(range(0, 2, 1))
subset = torch.utils.data.Subset(CIFAR_10_Dataset, sublist)
dataloader = torch.utils.data.DataLoader(subset, 1, shuffle=False, num_workers=2)

model = ResNet9(3, 10)
model.load_state_dict(torch.load('./var_d16.pth'))
new_m = torchvision.models._utils.IntermediateLayerGetter(model,{'layer3_residual2': 'feat1'})
final1 = []
if __name__ == '__main__':
    for img, label in tqdm(iter(dataloader)):
        final = []
        for j in range(10):
            out = new_m(Aug(img))
            for k, v in out.items():
                my = np.mean(v.reshape(256, 4).cpu().detach().numpy(), axis=1)
                final.append(my)
        out1 = np.mean(np.array(final), axis=0)
        final1.append(out1)

    finalout = np.array(final1)
    maxout = np.max(finalout, axis=0)
    medianout = np.median(np.sort(finalout, axis=0)[0:-1], axis=0)
    selectivity = (maxout - medianout)/(maxout + medianout)
    scipy.io.savemat('./data/selectivity_unit.mat', {'selectivity': selectivity})
    
    # Top 10% der Neuronen mit höchster Selectivity finden
    num_neurons = selectivity.shape[0]
    top_k = int(np.ceil(num_neurons * 0.1))
    top_indices = np.argsort(selectivity)[-top_k:][::-1]  # absteigend sortiert
    print(f"Top 10% Neuronen-Indizes: {top_indices}")
    # Optional: als .mat speichern
    scipy.io.savemat('./data/top10percent_unit_indices.mat', {'top10percent_indices': top_indices})
