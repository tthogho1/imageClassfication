from ultralytics import YOLO

# モデルのロード（例: YOLOv8の軽量モデル）
model = YOLO("yolov8n.pt")

# 画像ファイルのパス
img_path = "1605270897.jpg"

# 物体検出の実行
results = model.predict(img_path, save=True, imgsz=320, conf=0.5)

json_data = results[0].to_json()

print("検出結果:", json_data)

# 結果画像は自動的に保存されます
