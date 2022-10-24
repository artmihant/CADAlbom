from model import Model
from celery import Celery
import scripts
from billiard.exceptions import TimeLimitExceeded

app = Celery('cubit')
app.config_from_object('config')

@app.task
def do(script, path):
    try:
        with Model(path) as model:
            res = getattr(scripts, script)(model)
    except TimeLimitExceeded:
        res = False
        model = Model(path)
        model['timeout'] == True
    return res
