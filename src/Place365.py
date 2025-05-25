import torch
from torchvision import transforms
from torchvision.models import resnet18, ResNet18_Weights
from torchvision import models
from collections import OrderedDict

model = models.resnet18(num_classes=365)
from PIL import Image

checkpoint = torch.load("C:/temp/resnet18_places365.pth.tar", map_location="cpu")

state_dict = checkpoint["state_dict"] if "state_dict" in checkpoint else checkpoint

new_state_dict = OrderedDict()
for k, v in state_dict.items():
    name = k.replace("module.", "")
    new_state_dict[name] = v

model.load_state_dict(new_state_dict)
model.eval()


with open("c:/temp/categories_places365.txt") as f:
    categories = [line.strip().split(" ")[0][3:] for line in f.readlines()]


# 画像前処理
transform = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)

img = Image.open("1605270897.jpg").convert("RGB")  #
input_tensor = transform(img).unsqueeze(0)
with torch.no_grad():
    output = model(input_tensor)
    probabilities = torch.nn.functional.softmax(output[0], dim=0)


top_probs, top_idxs = probabilities.topk(5)
for i in range(top_probs.size(0)):
    print(f"Class: {categories[top_idxs[i]]}, Score: {top_probs[i].item():.4f}")
