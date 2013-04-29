django-golive
=============

django-golive is focusing on the tasks executed on your hosts to deploy and operate a Django-powered site.
For the most common Django-sites you have to create a virtualenv, setup a database, install python-modules from pip
and setup a webserver in front of a WSGI-process.

All these steps is doing django-golive for you. All you have to do is to prepare your project, which takes less
than 5 minutes. Then you are ready to enjoy django-golive and won't repeat yourself anymore!

What brings django-golive?
--------------------------

- Django-admin commands to deploy your project to a remote server(s)
- Preconfigured stacks (configuration templates ready to use)
- Multiple environments handling (i.e. testing, production)


Getting started
---------------

Install django-golive

    pip install django-golive

Add django-golive to settings.INSTALLED_APPS

    vi settings.py

Create initial configuration file golive.yml

    python manage.py create_config

Customize golive.yml

    vi golive.yml

Deploy the basics

> Install a [Debian][debian] server on your own platform or choose a hosting provider (e.g. [IntoVPS][intovps]).
> Don't forget to create the `INITIAL_USER` on the server with public key authentication.

    python manage.py init ENVIRONMENT                         # change ENVIRONMENT to your ENVIRONMENT_ID

Set your secrets

    python manage.py set_var ENVIRONMENT MYVAR 'VALUE'        # Set variables which you can use in your
                                                              #    settings file, e.g.:
                                                              #
                                                              #    import os
                                                              #    os.environ['GOLIVE_MYVAR']

Create settings file for environment

    echo "from settings import *" > settings_ENVIRONMENT.py   # change ENVIRONMENT to your ENVIRONMENT_ID

Deploy the rest

    python manage.py deploy ENVIRONMENT                       # change ENVIRONMENT to your ENVIRONMENT_ID

Visit your page with curl:

    curl http://SERVERNAME:80                                 # you configured SERVERNAME in golive.yml

Configuration
--------

You can create with the following command a starting configuration file `golive.yml` in the root of your Django-project:

    python manage.py create_config

The configuration file contains the desired stack, default and configurations per environment:

    CONFIG:
      PLATFORM: DEDICATED
      STACK: CLASSIC

    ENVIRONMENTS:
      DEFAULTS:
        INIT_USER: myuser               # For the user creation step
        PROJECT_NAME: exampleproject
        USER: exampleuser               # If not specified: {{PROJECT_NAME}}_{{ENVIRONMENT}}
        PUBKEY: $HOME/.ssh/id_dsa.pub   # Is copied to /home/$USER/.ssh/authorized_keys2

      TESTING:
          USER: exampleuser             # If not specified: {{PROJECT_NAME}}_{{ENVIRONMENT}}
          SERVERNAME: golivetesting     # Used as virtualhost name in webservers configuration
          ROLES:                        # All of the hosts must be resolvable (DNS, hostfile)
             APP_HOST:
               - golivehost1
               - golivehost2
             DB_HOST:
               - golivedb
             WEB_HOST:
               - goliveweb


Deployment
----------
### Initial

    python manage.py init ENVIRONMENT       # YOURENV can be e.g. testing, integration, production
    python manage.py deploy ENVIRONMENT     # YOURENV can be e.g. testing, integration, production

### Update the project
    python manage.py update YOURENV                     # Tasks in all roles

    python manage.py update YOURENV \
               --role APP_HOST                          # Tasks in specified role

    python manage.py update YOURENV \
               --task golive.layers.app.DjangoSetup     # Specified task only

    python manage.py update YOURENV \
               --host goliveweb                         # Tasks on specified host

Target Platforms
----------------

At the moment only deployments to a set of installed [Debian] hosts is supported (`PLATFORM: DEDICATED`).


Builtin Components
----------
### golive.layers.base.BaseSetup
* OS Packages

    Installs basic required and handy packages like:

    `rsync, git, gcc, python-dev, postgresql-client, htop, curl, lsof, sysstat`

* Host file

    Adds entries for every host in environment to the file `/etc/hosts`.

***

### golive.layers.base.UserSetup
* User creation

    Creates the user with the name `USER` specified in `golive.yml` of if not specified as `PROJECT_NAME`_`ENVIRONMENT`.
    For the first login an existant user `INIT_USER` with key-authentication is required to be able to perform these steps.

* SSH Pubkey

    Copies a pubkey `PUBKEY` to the `authorized_keys2` file on the servers to be able to login with key-authentication.

***

### golive.layers.web.NginxSetup
* Configure Frontend-Webserver

    Installs the package nginx and then creates out of `templates/golive/nginx.conf` a configuration file.
    The file is uploaded to the directory `/etc/nginx/sites-enabled/app.conf`.

<!-- TODO: ### golive.layers.cache.RedisSetup
- Cachehost (Redis Key/Value-Store for Caching)
-->

***

### golive.layers.app.PythonSetup
* Virtualenv Environment

    Creates a virtualenv in `$HOME/.virtualenvs` with the name of the project (`PROJECT_NAME`).

***

### golive.layers.db.PostgresSetup
* Postgresql installation

    Installs the packages `postgresql`.

* Configure Postgresql

    - Allow access from every host in the role `WEB_HOST`.
    - Listen on all network interfaces (`0.0.0.0`).

***

### golive.layers.app.DjangoSetup
* Directories

    Creates directories: `$HOME/code, $HOME/log, $HOME/static`

* Start/stop process configuration

    Configures a process for supervisor. Thatfor `templates/golive/supervisor_django.conf`
    is uploaded to `/etc/supervisor/conf.d/app.conf`.

* Send Djangoproject

    At this stept your project root is sent to the servers `$HOME/code` directory.

* Install python packages with pip

    Installation of the required python packages listed in `requirements.txt` in your project root.

* Prepare Database

    - Create user (role) `USER` on `DB_HOST`.
    - Create database `PROJECT_NAME`_`ENVIRONMENT` on `DB_HOST` with owner `USER`.

* Synchronize Databaseschema

    Executes `syncdb` django command. If south is installed, `migratedb` in addition.

* Collect staticfiles

    Collects the staticfiles with the standard django-admin command to $HOME/static/

* Start django process

    The process for django is started with `supervisorctl`:

        sudo supervisorctl start app


Built-In Stack's
-------------

### Classic
The very basic Django-Stack installed on your self-hosted platform ([Ubuntu] or [Debian], [Redhat] or [CentOS]):

- Role 'WEB_HOST' (Nginx Frontent-Webserver)

golive.layers.web.NginxSetup

- One or many Apphosts (Python-Procs for Django with builtin's server)

golive.layers.web.NginxSetup

- DBhost (Database-Server with Postgresql)

**See Stack-File [here][example-stackfile]**

### ClassicGunicorned

This Stack is inherited from 'Classic', but uses Gunicorn to start the Django-Proc.
The Components list difference:

- One or many Apphosts (Python-Procs for Django with Gunicorn)


For Developers
--------------
### API

   # TODO


### Contribute

   # TODO


### Send stacks

Features in the future
----------------------
- Install [newrelic] Server Monitoring Agent
- New stacks
  - Gunicorn
  - Django and Websockets
- Deploy to Dedicated Redhat servers
- Deploy to IaaS platforms
  - Amazon EC2
  - Openstack
- Deploy to PaaS platforms
  - Dotcloud
  - Openshift

[example-stackfile]: golive/stacks/ "Example Stackfile"

[ubuntu]: http://ubuntu.com "Ubuntu"
[debian]: http://debian.org "Debian"
[redhat]: http://redhat.org "Redhat"
[centos]: http://debian.org "Centos"
[intovps]: http://www.intovps.com/plans.html "IntoVPS"
[nginxsetup]: http://www.bla.com
[newrelic]: http://www.newrelic.com "New Relic"
