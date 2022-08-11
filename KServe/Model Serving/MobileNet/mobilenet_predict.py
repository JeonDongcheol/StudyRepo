import numpy
import requests
import json
import os

# Preprocess Code Load
from data_preprocessing import data_preprocess

# MobileNet Model Prediction Test

# ID Token Setting
TOKEN = "" # Token

# Header Setting (ID Token)
HEADER = {"Cookie" : "authservice_sessoin=" + TOKEN}

# Cluster IP & PORT / Model Name Setting
CLUSTER_IP = "" # Cluster IP
CLUSTER_PORT = "" # Cluster Port
MODEL_NAME = "" # Model Name

# Sample Image & Data Preprocessing
image_path = os.getcwd() + "/sample_img.png" # Sample Image
preprocessed_data = data_preprocess(image_path).tolist()

# Make Input Shape
data = json.dumps({"instances" : preprocessed_data})

# URL
url = "http://" + CLUSTER_IP + ":" + CLUSTER_PORT + "/v1/models/" + MODEL_NAME + ":predict"

# Request & Response
response = requests.post(url, data=data, headers=HEADER)

# Numpy Convert & Show Result
predict_result = numpy.array(response.json())

print(predict_result)
