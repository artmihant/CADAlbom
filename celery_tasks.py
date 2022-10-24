from model import Model
from celery import Celery
import scripts

app = Celery('cubit')
app.config_from_object('config')

@app.task
def do(script, path):
    with Model(path) as model:
        getattr(scripts, script)(model)