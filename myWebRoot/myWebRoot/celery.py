import os
from celery import Celery

# Establecer la variable de entorno por defecto para settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myWebRoot.settings')

app = Celery('myWebRoot')

# Usar configuración de Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Cargar tareas automáticamente
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')