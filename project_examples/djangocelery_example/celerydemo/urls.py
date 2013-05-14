from django.conf.urls import patterns, url
from .views import task_start
from .views import task_status

urlpatterns = patterns('',

                       # example api
                       url(r'^start/(?P<task_name>[a-zA-Z._]*)/$', task_start),
                       url(r'^status/(?P<task_id>[\w\d\-\.]+)/$', task_status),
                       )


