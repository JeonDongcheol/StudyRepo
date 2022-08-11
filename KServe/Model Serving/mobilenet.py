import tensorflow as tf
from matplotlib import pyplot as plt
import numpy as np

# Tensorflow + MobileNet
# Directory 형태로 Model을 만드는데 '${Model Name}/${Nubmer}/' 안에 만들어진 Model을 저장
# Path : pvc://dc-test-volume/mobilenet_tf/mobilenet

# Load Data
file = tf.keras.utils.get_file(
    "grace_hopper.jpg",
    "https://storage.googleapis.com/download.tensorflow.org/example_images/grace_hopper.jpg"
)

# Data Preprocessing
img = tf.keras.preprocessing.image.load_img(file, target_size=[224, 224])
plt.imshow(img)
plt.axis('off')
x = tf.keras.preprocessing.image.img_to_array(img)
x = tf.keras.applications.mobilenet.preprocess_input(x[tf.newaxis,...])

# Label Setting
labels_path = tf.keras.utils.get_file('ImageNetLabels.txt','https://storage.googleapis.com/download.tensorflow.org/data/ImageNetLabels.txt')
imagenet_labels = np.array(open(labels_path).read().splitlines())

# Model Training
pretrained_model = tf.keras.applications.MobileNet()
result_before_save = pretrained_model(x)

decoded = imagenet_labels[np.argsort(result_before_save)[0,::-1][:5]+1]

print("저장 전 결과:\n", decoded)

# Model Save
tf.saved_model.save(pretrained_model, "mobilenet/1")
