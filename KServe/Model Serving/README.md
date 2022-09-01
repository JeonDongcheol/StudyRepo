# Model Serving
> 다양한 Model을 Serving하고 이를 REST API Call 하는 작업들을 담았다.

# Tensorflow Serving (TFServing)
> Tensorflow 기반의 Model Serving 과정에서의 기록

Tensorflow Model을 Serving하면서 부딪혔던 문제들에 대해서 간단하게 기록으로 남기고자 한다. (Model, Logic 같은 부분은 모름) [Tensorflow 공식 홈페이지]() 에 나온 Tutorial을 기반으로 Serving을 한 것이므로, 복잡한 설정은 하지 않았으며, 어떤 부분들을 신경써야하는지도 가이드를 해본다.

Tensorflow Model Save 과정에서 _Keras_ 를 이용하는 방법이 있고, _Saved Model_ 을 이용하는 방법이 있다. 우선 테스트를 하면서 본 것은 Keras - Save는 동작이 되질 않았다. (Runtime Version의 문제일 수도 있고, Directory 구성이 잘못된 것일 수도 있음. 추가적인 Test가 필요함)

우선 Tensorflow의 경우에는 Directory를 Mount하는데, Directory는 다음과 같은 구조를 가져야 한다.

```
${MODEL_NAME}
--- ${NUMBER}
     --- aseets
     --- ${MODEL}.pb
     --- variables
         --- variables.index
         ...
```

가장 헷갈리기 쉬운 것은 ```${NUMBER}``` 부분인데, 그냥 모델을 만들고 나서 아무렇게나 저장하면 Model을 정상적으로 Serving하지 않는다. 모델이 떨어진 directory 안에는 반드시 __Number__ 가 지정된 디렉토리가 있어야하며, 해당 하위 디렉토리에 모델이 저장되어있어야 한다.


# Pytorch Serving (TorchServe)
> TorchServe 기반의 Model Serving 과정에서의 기록

Pytorch는 생각보다 번거로운 작업들이 필요했다. Model을 ```pt``` file 혹은 ```pth``` file로 만들었다고 해도, 그것을 그대로 올리면 되는 것이 아니었다. (Tensorflow는 규격만 잘 맞추면 잘 올라갔다...) Pytorch를 TorchServe 기반으로 Serving하는 과정은 다음과 같다.

1. Model Save (pt, pth...)
2. Torch Model Archive
3. config.properties
4. config / model-store directory

이 과저에서 가장 중요한건 Model을 만들고 Torch Model Archive를 통해 Model, Handler, Model File 등을 ```~.mar``` 로 압축을 해야한다는 점이었다. ```mar``` file만 있다고 model을 Serving할 수 있는 것도 아니었다. ```config.properties``` 를 통해 Model에 대한 설정을 해준다.

위의 작업이 끝났으면 Directory를 분할해주는데, ```config``` directory 안에는 ```config.properties``` 를 담아주고, ```model-store``` 에는 config.properties 에 설정해 두었던 ```Model MAR``` file을 담는다.

만약 ```Handler``` , ```Model``` Code file을 정상적으로 작업했다면, 정상적으로 Serving이 될 것이다.

TorchServe Github에 나와있는 __MNIST__ 를 기반으로 우선 Test를 해보았는데, GCS(Google Cloud Storage)에 있는 모델을 가져오는 것은 정상적으로 수행했으나, 해당 Model을 PVC(Persistent Volume Claim)에 올려서 Serving했을 때는 정상적으로 올라가지 않았다. 그 문제도 해결해보았다.
