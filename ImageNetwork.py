import os

import torch
import torch.nn as nn
from torchinfo import summary


class CompressedBlock(torch.nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.depth_conv = nn.Conv2d(in_channels, in_channels, kernel_size=4, padding=1, groups=in_channels)
        self.point_conv = nn.Conv2d(in_channels, out_channels, kernel_size=1)
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU()
        self.maxpooling = nn.MaxPool2d(kernel_size=2, stride=2)

    def forward(self, x):
        x = self.depth_conv(x)
        x = self.point_conv(x)
        x = self.bn(x)
        x = self.relu(x)
        x = self.maxpooling(x)
        return x


class FullyConnectedBlock(torch.nn.Module):
    def __init__(self, in_features, out_features):
        super().__init__()
        self.fc = nn.Linear(in_features, out_features)
        self.bn = nn.BatchNorm1d(out_features)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(p=0.5)

    def forward(self, x):
        x = self.fc(x)
        x = self.bn(x)
        x = self.relu(x)
        x = self.dropout(x)
        return x


class ImageNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(
            # input: N, 3, 224, 224
            CompressedBlock(3, 32),  # (N, 64, 112, 112)
            CompressedBlock(32, 64),  # (N, 64, 56, 56)
            CompressedBlock(64, 128),  # (N, 128, 28, 28)
            CompressedBlock(128, 256),  # (N, 256, 14, 14)
            nn.AdaptiveAvgPool2d((1,1)),  # (N, 256, 1, 1)
            nn.Flatten(),
            FullyConnectedBlock(256, 32),  # (N, 1024),
            FullyConnectedBlock(32, 11)  # (N, 11)
        )

    def forward(self, x):
        return self.network(x)


def get_teacher_network():
    teacher_network = torch.hub.load('pytorch/vision:v0.10.0', 'resnet18', pretrained=False, num_classes=11)
    teacher_network.load_state_dict(torch.load(os.path.join(r"D:\ML_Dataset\HW13\Food-11", "resnet18_teacher.ckpt"),
                                               map_location='cpu'))
    return teacher_network.cuda()


if __name__ == "__main__":
    student_network = ImageNetwork()
    summary(student_network, (4, 3, 224, 224))
