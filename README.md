django-golive
=============

[![Build Status](https://travis-ci.org/fatrix/django-golive.png?branch=master)](https://travis-ci.org/fatrix/django-golive)

> ... is not yet production ready. If you are interested in any updates on it:

> - follow [me] on Twitter
> - join the [Mailinglist]
> - visit [http://sahli.net/django-golive](sahli-golive)

django-golive is focusing on the tasks executed on servers to deploy and operate a Django-powered site.
For the most common configurations you have to create a virtualenv, setup a database, install python-modules from pip
and configure a webserver in front of a WSGI-process.

All these steps does django-golive for you. All you have to do is to prepare your project, which takes less
than 5 minutes. Then you are ready to enjoy django-golive and repeat yourself even less!

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

    python manage.py init ENV                         # change ENV to your ENV_ID

Set your secrets

    python manage.py set_var ENV MYVAR 'VALUE'        # Set variables which you can use in your
                                                              #    settings file, e.g.:
                                                              #
                                                              #    import os
                                                              #    os.environ['GOLIVE_MYVAR']

In your settings module you can access the secrets like in the following example:

    from golive.utils import get_var
    DATABASES['default']['PASSWORD'] = get_var('DB_PASSWORD')

Create settings file for environment

> This step is needed only if different settings applies on the remote environment. e.g. `DEBUG = False`

    echo "from settings import *" > settings_ENV.py   # change ENV to your ENV_ID
    echo "DEBUG = False" >> settings_ENV.py           # change ENV to your ENV_ID

Deploy the rest

    python manage.py deploy ENV                       # change ENV to your ENV_ID

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
        INIT_USER: root                 # For the user creation step
        PROJECT_NAME: exampleproject
        USER: exampleuser               # If not specified: {{PROJECT_NAME}}_{{ENV}}
        PUBKEY: $HOME/.ssh/id_dsa.pub   # Is copied to /home/$USER/.ssh/authorized_keys2

      TESTING:
          USER: exampleuser             # If not specified: {{PROJECT_NAME}}_{{ENV}}
          SERVERNAME: golivetesting     # Used as virtualhost name in webserver configuration
          ROLES:                        # All of the hosts must be resolvable (DNS, hostfile)
             APP_HOST:
               - testserver
             DB_HOST:
               - testserver             # At the moment only one `DB_HOST` is allowed
             WEB_HOST:
               - testserver             # At the moment only one `WEB_HOST` is allowed


Deployment
----------
### Initialization

    python manage.py init ENV       # ENV can be e.g. testing, integration, production
    python manage.py deploy ENV     # ENV can be e.g. testing, integration, production

### Update the project
    python manage.py update ENV                         # Tasks in all roles

    python manage.py update ENV \
               --role APP_HOST                          # Tasks in specified role

    python manage.py update ENV \
               --task golive.layers.app.DjangoSetup     # Specified task only

    python manage.py update ENV \
               --host testserver2                       # Tasks on target host

With the option `--fast` time intensiv tasks (for deploy and update) are not executed. The option is usefull if you only update your code and static files should not be collected and not any required python module from `requirements.txt` should not be installed/upgraded.

    python manage.py update ENV --fast

### Check
    python manage.py status ENV


### Logs

Executes a `tail -f` on all logfiles located in the directory `log` on the targets.

    python manage.py logs ENV


Target Platforms
----------------

At the moment only deployments to a set of installed [Debian] hosts is supported (`PLATFORM: DEDICATED`).

Recovery
--------------

### Backup

Creates a backup of your database and downloads a gzipped tar file to your current working directory.

    python manage.py backup ENV

### Restore

Let you choose a previously taken backup of an environment.

    python manage.py restore ENV

### Restore from a different environment

This feature is useful to restore your production database into the integration environment.

    python manage.py restore ENV --source_env=ENV

After restoring the database django-golive executes sql commands specified in a list specified in your settings
as `GOLIVE_CLEANUP_RESTORE`.

For example for a mezzanine project:

    GOLIVE_CLEANUP_RESTORE = [
        'SELECT * FROM conf_setting;',
        'UPDATE conf_setting SET value=\'\' WHERE name=\'GOOGLE_ANALYTICS_ID\'',
        'UPDATE conf_setting SET value=\'\' WHERE name=\'BITLY_ACCESS_TOKEN\'',
        'UPDATE conf_setting SET value=\'\' WHERE name=\'COMMENTS_DISQUS_API_PUBLIC_KEY\'',
        'UPDATE conf_setting SET value=\'\' WHERE name=\'COMMENTS_DISQUS_API_SECRET_KEY\'',
        'UPDATE conf_setting SET value=\'\' WHERE name=\'COMMENTS_DISQUS_SHORTNAME\'',
        'UPDATE conf_setting SET value=\'\' WHERE name=\'COMMENTS_DISQUS_SHORTNAME\'',
        'UPDATE conf_setting SET value=\'\' WHERE name=\'TWITTER_CONSUMER_SECRET\'',
        'UPDATE conf_setting SET value=\'\' WHERE name=\'TWITTER_CONSUMER_KEY\'',
        'UPDATE conf_setting SET value=\'\' WHERE name=\'TWITTER_ACCESS_TOKEN_KEY\'',
        'UPDATE conf_setting SET value=\'\' WHERE name=\'TWITTER_ACCESS_TOKEN_SECRET\'',
        'UPDATE blog_blogpost SET short_url=NULL;',
    ]



Built-In Components
----------
### golive.layers.base.BaseSetup
* OS Packages

    Installs basic required and handy packages like:

    `rsync, git, gcc, python-dev, postgresql-client, htop, curl, lsof, sysstat`

* Host file

    Adds entries for every host in environment to the file `/etc/hosts`.

* Security

    Sets `PasswordAuthentication` for sshd to no.

* IPTables

    Accept by default only connection to port tcp/22 from all hosts in the internet. All other services are denied.
    Per service (for example public or communication within application (i.e. to database, caching service) rules are generated in the specific task.

***

### golive.layers.base.UserSetup

* User creation

    Creates the user with the name `USER` specified in `golive.yml` of if not specified as `PROJECT_NAME`_`ENV`.
    For the first login an existant user `INIT_USER` with key-authentication is required to be able to perform these steps.

* SSH Pubkey

    Copies a pubkey `PUBKEY` to the `authorized_keys2` file on the servers to be able to login with key-authentication.

***

### golive.layers.base.CrontabSetup
* Configure crontab per role

    You can create a crontab `templates/golive/cron/ROLE.crontab` in your template folder.
    It must extend the base template in golive and define a block `crontab` in it.

    Example `db_host.crontab`:

        {% extends "golive/cron/base_db_host.crontab" %}
        {% block crontab %}
        0 3 * * * {{ USER }} script.sh >> {{ LOGDIR }}/script.log
        {% endblock %}

    Golive creates the file in `/etc/cron.d`.

***

### golive.layers.web.NginxSetup
* Configure Frontend-Webserver

    Installs the package nginx and then creates out of `templates/golive/nginx.conf` a configuration file.
    The file is uploaded to the directory `/etc/nginx/sites-enabled/app.conf`.

* IPTables

    Accept connections to port tcp/80 from the internet.

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

* IPTables

    Accept connections from all hosts within environment to port tcp/5432.

***

### golive.layers.app.DjangoSetup
* Directories

    Creates directories: `$HOME/code, $HOME/log, $HOME/static`

* Start/stop process configuration

    Configures a process for supervisor. Therefor `templates/golive/supervisor_django.conf`
    is uploaded to `/etc/supervisor/conf.d/app.conf`.

    Supervisord has some limitiations in handling the process execution and the resulting environment.
    To access the environment variables set with the command `set_var` supervisor is
    executing a bash script `supervisor_django.run`, which exports all variables
    from `$HOME/.golive.rc`.

* Send Djangoproject

    At this stept your project root is sent to the servers `$HOME/code` directory.

* Install python packages with pip

    Installation of the required python packages listed in `requirements.txt` in your project root.

* Prepare Database

    - Create user (role) `USER` on `DB_HOST`.
    - Create database `PROJECT_NAME`_`ENV` on `DB_HOST` with owner `USER`.

* Synchronize Databaseschema

    Executes `syncdb` django command. If south is installed, additionally `migratedb`.

* Collect staticfiles

    Collects the staticfiles with the standard django-admin command to `$HOME/static/`.
    If you have more than one host as role `APP_HOST`, then like in any other deployment procedure
    use [django-storages] to collect your static and upload files to [Amazon S3].

* Start django process

    The process for django is started with `supervisorctl`:

        sudo supervisorctl start app

* IPTables

    All connections to the tcp port are denied unless their initiated by any server in the `WEB_HOST` role.

***

### golive.layers.app.RabbitMqSetup

TODO

***

### golive.layers.app.WorkerSetup

* Before installation

    Set the environment variable `BROKER_URL`, i.e.:

        python manage.py set_var ENV BROKER_URL amqp://USERNAME:PASSWORD@HOST:5672/

* Setting

    Add following to your `settings.py`:

        BROKER_URL = os.environ['GOLIVE_BROKER_URL']


Built-In Stacks
-------------

### Classic

The very basic Django-Stack installed on your self-hosted platform ([Ubuntu] or [Debian], [Redhat] or [CentOS]):

- Role `WEB_HOST` (Frontend Webserver)

   - golive.layers.web.NginxSetup

- One or many `APP_HOST`'s (Python-Procs for Django with builtin's server)

   - golive.layers.web.NginxSetup

- One `DB_HOST` (database server with Postgresql)

**See Stack-File [here][example-stackfile]**

### ClassicGunicorned

This Stack is inherited from `Classic`, but uses [Gunicorn] to run the project behind Nginx.
The Components list difference:

- `APP_HOST` (Python-Procs for Django with Gunicorn)
   - golive.layers.app.DjangoSetupGunicorn

- `WEB_HOST` (Proxing to Gunicorn)
   - golive.layers.web.NginxProxySetup


### Gunicelery

If you need asynchronous work done with celery, this stack is the right one for you.
In addition to `Classicgunicorned` it needs to more roles:

- Role `QUEUE_HOST` (Rabbitmq server)

  - golive.layers.queue.RabbitMqSetup

- Role `WORKER_HOST` (Doing the asynchronous work)

  - golive.layers.app.WorkerSetup
  - golive.layers.app.WorkerCamSetup

Add-ons
-------------

### New Relic Python Agent / New Relic Server Agent

Add following to the `CONFIG` section:

     CONFIG:
         ADDONS:
              - NEW_RELIC_PYTHON
              - NEW_RELIC_SERVERAGENT

Set the variable `NEWRELIC_LICENSE_KEY`. Execute the commands init and deploy. Your app and server now report metrics to [New Relic][newrelic].


For Developers
--------------
### Contribute

   Forks and pull requests are welcome!

### Tasks

   To document

### Stacks

   To document

### Addons

   To document

Features in the future
----------------------
- New stacks
  - Django and Websockets
  - Django and Celery
- Testing
  - Test on Debian 7
- Deploy to dedicated Redhat servers
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
[me]: https://twitter.com/philipsahli
[Mailinglist]: https://groups.google.com/forum/?fromgroups#!forum/django-golive
[django-storages]: https://pypi.python.org/pypi/django-storages
[Amazon S3]: http://aws.amazon.com/s3/
[Gunicorn]: http://gunicorn.org/#docs
[sahli-golive]: http://sahli.net/django-golive
