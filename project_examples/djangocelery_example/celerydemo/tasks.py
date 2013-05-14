from celery import task

@task()
def add(val1, val2):
    print val1, val2
    return val1, val2
