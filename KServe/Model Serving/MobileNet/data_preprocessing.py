import tensorflow as tf
import os

# Data Preprocessing Method
def data_preprocess(image_path):
    # Image Resizing(224, 224)
    img = tf.keras.preprocessing.image.load_img(image_path, target_size=[224, 224])

    # Image Preprocessing -> Image to Array
    output = tf.keras.preprocessing.image.img_to_array(img)
    output = tf.keras.applications.mobilenet.preprocess_input(output[tf.newaxis,...])
    
    
    return output
