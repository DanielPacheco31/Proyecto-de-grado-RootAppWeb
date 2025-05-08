
try:
    from celery import shared_task
    print("Celery está instalado correctamente.")
except ImportError:
    print("Error: No se pudo importar 'shared_task' desde 'celery'.")
    print("Celery podría no estar instalado. Intenta ejecutar: pip install celery")
