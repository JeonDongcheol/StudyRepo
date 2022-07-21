from sklearn import svm # sklearn에서 Support Vector Machine module import
from sklearn import datasets # Iris data를 이용하기 위한 dataset import
from joblib import dump # Model 생성 과정에서 필요한 Module

# Data Set Load 및 data, label 선언
iris = datasets.load_iris()
X, y = iris.data, iris.target

clf = svm.SVC(gamma='scale')
clf.fit(X, y)

# iris-model.joblib으로 Model을 떨군다.
dump(clf, 'iris-model.joblib')
