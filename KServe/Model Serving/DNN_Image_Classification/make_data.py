import tensorflow as tf
import pandas as pd
import pickle

# Preprocessing Module Import
from dnn_data_preprocessing import normalization

# Data Load 후 Label에 맞게 Data 저장
# Training Data & Test Data로 분리

def data_load(datas, labels, name) :
    df = pd.DataFrame(columns=['image', 'label'])
    for i, item in enumerate(datas) :
        image = normalization(item)
        df.loc[i] = ({'image': image, 'label': labels[i]})

    with open(name + '_data.pickle', 'wb') as f:
        pickle.dump(df, f, pickle.HIGHEST_PROTOCOL)

def main():
    # 데이터 셋 로드
    fashion_mnist = tf.keras.datasets.fashion_mnist
    (train_images, train_labels), (test_images, test_labels) = fashion_mnist.load_data()
    data_load(train_images, train_labels, 'train')
    data_load(test_images, test_labels, 'test')

if __name__ == '__main__':
    main()
