import requests
import json
import os
import matplotlib.pyplot as plt
import tensorflow as tf

# Preprocess Module
from dnn_data_preprocessing import normalization

# MobileNet Model Prediction Test

# ID Token Setting
TOKEN = "" # ID Token

# Header Setting (ID Token)
HEADER = {"Cookie" : "authservice_sessoin=" + TOKEN}

# Cluster IP & PORT / Model Name Setting
CLUSTER_IP = "" # Cluster IP 
CLUSTER_PORT = "" # Cluster Port
MODEL_NAME = "" # Inference Service Name

# Prediction Input Shape
input_shape = {"instances" : []}

# Image 1부터 10까지 Classification
for i in range(1, 11):
    # Sample Image & Data Preprocessing
    image_path = os.getcwd() + "/dnn_test_image/test_img" + str(i) + ".jpg" # Image Path
    test_image = plt.imread(image_path) # 해당 경로의 파일을 Image로 읽는 작업
    
    preprocess_data = normalization(test_image) # Image Preprocessing

    instances = preprocess_data[tf.newaxis,...].tolist() # Re-formatting to Input Shape
    input_shape["instances"].append(instances) # Input Shape Instances에 data 추가
    
data = json.dumps(input_shape) # JSON 형태로 변환 : POST Method의 Body에 들어가야 함

# URL
url = "http://" + CLUSTER_IP + ":" + CLUSTER_PORT + "/v1/models/" + MODEL_NAME + ":predict"

# Request & Response
response = requests.post(url, data=data, headers=HEADER)

# Classification Label
class_names = ['T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat', 'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot']

# Image 1~10까지의 Prediction Result에 대해 Classification 후 출력
print("=============== Classification Result ===============")
for i in range(0, len(response.json()["predictions"])):
    # Softmax로 Predict Value 변환
    predict_value = tf.math.argmax(tf.nn.softmax(response.json()["predictions"][i]))
    
    # Classification Result 배열에 저장
    print("Image [" + str(i+1) + "] Classification Result : " + class_names[predict_value])
