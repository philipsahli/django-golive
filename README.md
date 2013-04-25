django-golive
=============

django-golive is focusing on the tasks executed on your hosts to deploy and operate a Django-powered site.

What brings django-golive?
--------------------------

- Golive-Stacks (Configuration-Templates ready to use)
- Django Management Commands
- Multiple environments handling (i.e. testing, production)

Commands
--------
### Install the project
 python manage.py init test

### Update your project
 python manage.py update test

### Options

   Run only on specified role or host

      --role / -r ROLE
      --host / -h

   Force execution

      --force / -f

   Very silent output

      --silent / -s


Built-In Stack's
-------------

### Classic
The very basic Django-Stack installed on your self-hosted platform ([Ubuntu] or [Debian], [Redhat] or [CentOS]):

- Webhost (Nginx Frontent-Webserver)
- One or many Apphosts (Python-Procs for Django with WSGI)
- Cachehost (Redis Key/Value-Store for Caching)
- DBhost (Database-Server with Postgresql)

**See Stack-File [here][example-stackfile]**

### Faster

    # TODO


For Developers
--------------
### API

   # TODO


### Contribute

   # TODO


### Send stacks

[example-stackfile]: golive/stacks/ "Example Stackfile"

[ubuntu]: http://ubuntu.com "Ubuntu"
[debian]: http://debian.org "Debian"
[redhat]: http://redhat.org "Redhat"
[centos]: http://debian.org "Centos"
