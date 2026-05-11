import warnings
warnings.filterwarnings('ignore')
from ultralytics import YOLO

if __name__ == '__main__':
    model = YOLO('/home/dream/ws/ultralytics/ultralytics-main（复件）/run/train/exp1257/weights/best.pt')
    model.val(data='/home/dream/ws/ultralytics/ultralytics-main/dataset/KITTI/Kitti Dataset1/run/data.yaml',
              split='test',
              imgsz=640,
              batch=16,
              # iou=0.7,
              # rect=False,
              # save_json=True, # if you need to cal coco metrice
              project='runs/val',
              name='exp',
              )
