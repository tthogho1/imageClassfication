import torch
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../ssd")))
from ssd import build_ssd
from PIL import Image
from torchvision import transforms

# モデルの構築と重みの読み込み
net = build_ssd("test")  # SSDネットワークをtestモードで構築
net.load_weights("weights/ssd300_mAP_77.43_v2.pth")  # 学習済み重み

# 画像の読み込みと前処理
image = Image.open("1605270897.jpg")
transform = transforms.Compose(
    [
        transforms.Resize((300, 300)),
        transforms.ToTensor(),
    ]
)
x = transform(image).unsqueeze(0)  # バッチ次元追加

# 推論
with torch.no_grad():
    detections = net(x)
# detectionsからバウンディングボックスやクラスを抽出
