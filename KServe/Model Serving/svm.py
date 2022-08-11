from sklearn import svm
from sklearn import datasets
from joblib import dump

# Scikit Learn + Support Vector Classification(Support Vector Machine)
# joblib 파일로 모델을 만들고 이를 Seldon Scikit Learn Server Engine으로 KServe (Protocol Version : 2)
# Path : pvc://dc-test-volume/svm_sklearn/model.joblib

# Load Data
iris = datasets.load_iris()
X, y = iris.data, iris.target

# Model Training
clf = svm.SVC(gamma='scale')
clf.fit(X, y)

# Model Save (~.joblib)
dump(clf, 'model.joblib')
