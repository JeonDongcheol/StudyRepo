import tensorflow as tf
import pickle
import argparse
import numpy as np

# Tensorflow + DNN Image Classification (Fashion MNIST)
# Tensorflow : Saved_Model을 사용해서 Model을 저장 -> 그래야 KServe에 올라감

# Training을 위한 Data Load
def load_data(data_path):
    with open(data_path, 'rb') as f:
        data = pickle.load(f)

    images = []
    labels = []
    for i, item in enumerate(data['image']) :
        images.append(item)
        labels.append(data['label'][i])
    images = np.array(images)
    labels = np.array(labels)

    return images, labels

# Model 생성 : Model 반환
def model_generation():
    model = tf.keras.Sequential([
        tf.keras.layers.Flatten(input_shape=(28, 28)),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(10)
    ])
    
    return model

def main():
    # Model Training 과정에서 필요한 Argument 값 정의
    parser = argparse.ArgumentParser()
    parser.add_argument('--train_data_path', type=str, default =None, help='input_dir')
    parser.add_argument('--epoch', type=int, default=10)
    parser.add_argument('--optimizer', type=str, default='adam')
    args = parser.parse_args()

    # Argument에서 Training Data Path로 받은 Model 경로의 Training Data input
    images, labels = load_data(args.train_data_path)
    
    # Model 생성
    model = model_generation()
    
    #Model Setting
    model.compile(optimizer=args.optimizer,
                  loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                  metrics=['accuracy'])
    
    #Model Training
    model.fit(images, labels, epochs=args.epoch)
    
    # Tensorflow Saved_Model 형태로 저장
    tf.saved_model.save(model, "dnn_img_classify/1")

if __name__ == '__main__':
    main()
