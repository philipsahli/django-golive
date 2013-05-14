from json import dumps
import traceback
from celery.execute import send_task
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from djcelery.models import TaskState

__author__ = 'fatrix'


def JsonResponse(response):
    return HttpResponse(dumps(response), mimetype="application/json")

@csrf_exempt
def task_start(request, task_name):
    args = request.POST.dict().values()
    response = {}
    try:
        #ret = send_task(task_name, args=args, countdown=15)
        ret = send_task(task_name, (args[0], args[1]), countdown=15)
        response = ret.__dict__

        # remove uninteresting infos
        del response['app']
        del response['backend']
        del response['task_name']
        response['ok'] = True
    except Exception, e:
        response['ok'] = False
        tb = traceback.format_exc()
        response['error'] = str(tb)
    return JsonResponse(response)


def task_status(request, task_id):
    response = {}
    try:
        task = TaskState.objects.get(task_id=task_id)
        response['result'] = task.result
        response['traceback'] = task.traceback
        response['state'] = task.state
    except TaskState.DoesNotExist, e:
        print e
        response['state'] = "UNKNOWN"

    return JsonResponse(response)

