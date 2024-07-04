# Django APScheduler

> Django에서 Batch Job을 수행하기 위한 Django APScheduler Libraray

# Setting

## PyPi Install Django APScheduler

```bash
# Django APScheduler (ver. 0.6.2) 설치
pip3 install django-apscheduler
```

## Installed App 추가

- Installed Apps에 추가할 때는 Django APScheduler와 Batch 작업을 수행 할 App Name을 추가

```python
# ...
INSTALLED_APPS = [
# ...
	'django_apscheduler',
	'batch_app_name',
]
```

## Migration

```bash
# Migrate를 하기 전 미리 Makemigrations를 선수행
python3 manage.py makemigrations django_apscheduler --settings=${SETTINGS_PATH}
python3 manage.py migrate django_apscheduler --settings=${SETTINGS_PATH}
```

# Sample Code

> Batch 작업을 위한 App이 추가되었다는 가정 하에 진행, Model 객체 Count를 주기적으로 수집하는 작업

- batch_tasks.py : Batch 작업에서 어떤 Method를 호출할지 설정하는 Method로, 다른 부분의 코드를 Batch 작업에 추가해주어도 상관 없음

```python
from datetime import date
import logging

from .models import ObjectLogs

from notebook.models import Notebook
from inference.models import Inference
from hyperparameter.models import HyperParameter
from pipeline.models import Pipeline

def create_objects_log():
    # 해당 날짜의 로그가 존재하지 않는다면,
    if not ObjectLogs.objects.filter(collected_at=date.today()).exists():
        # 모든 Objects Count 가져와서 저장
        try:
            ObjectLogs.objects.create(
                notebook = Notebook.objects.count(),
                model_serving = Inference.objects.count(),
                hyperparameter = HyperParameter.objects.count(),
                pipeline = Pipeline.objects.filter(is_template = False).count()
            )

            logging.info("Objects Count Log is Saved Successfully!")
        except Exception as e:
            logging.exception("Saving Objects Count Log is Failed!")
    else:
        logging.info("Today's Count Log is already Created!")
```

- views.py : Batch Schedule 설정 부분으로, Cron 식을 이용한 Batch Job을 추가

```python
# Setting Import
from mlopsapi.settings.base import TIME_ZONE

# Django Background Scheduler를 위한 모듈 Import
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import register_events

# 실행 할 메소드 Import
from .batch_tasks import create_objects_log

def start():
    # Time Zone에 맞추어 Background 환경에서 Batch Job을 실행하기 위한 설정 진행
    scheduler = BackgroundScheduler(timezone=TIME_ZONE)
    # Scheduler 등록
    register_events(scheduler)

    """
    @func : Scheduler에서 수행 할 작업
    @trigger : Cron 식 기반으로 Schedule이 실행되는 시점
    @max_instances : 최대 생성 할 Job의 수
    @name : Job 이름
    """
    scheduler.add_job(
        func = create_objects_log,
        trigger = CronTrigger(hour='*/1', minute='0'),
        max_instances=1,
        name="create_objects_count_log"
    )

    # Schedule 실행
    scheduler.start()
```

- apps.py

```python
from django.apps import AppConfig
from mlopsapi.settings.base import SCHEDULER_DEFAULT

class BatchTasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'batch_tasks'

    # ready Method를 Override하여 Schedule 수행하도록 구성
    def ready(self):
        # Scheduler_default : schedule 활성화 여부(Boolean)
        if SCHEDULER_DEFAULT:
            from . import views as batch_task
            # 선언해 주었던 Schedule 실행
            batch_task.start()
```

# Issue

## 1. Schedule이 동시에 2-3회 호출되는 Issue

Django에서는 기본적으로 2회 AppConfig(apps.py)가 호출되는데, 이를 방지하기 위해 Run Server 과정에서 noreload 옵션을 넣어 1회만 실행되도록 설정

→ 더 나은 Solution을 찾을 수 있는지 모색

```python
python3 manage.py runserver ${IP_ADDRESS}:${PORT} --settings=${SETTINGS_PATH} --noreload
```

## 2. Backend Server Pod가 여러 개 생성되는 경우

Backend Server가 실행되는 Pod가 여러 개가 실행되고 있는 경우 각각 Batch Job이 수행되는데, 동시에 Schedule을 수행하여 중복 작업이 발생. 해당 부분에 있어서 어떻게 해결할 것인지 Solution 탐색 필요
