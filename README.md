django-golive
=============

django-golive is focusing on the tasks executed on your hosts to deploy and operate a Django-powered site.

What brings django-golive?
--------------------------

- Golive-Stacks (Configuration-Templates ready to use)
- Django Management Commands
- Multiple environments handling (i.e. testing, production)

Getting started
---------------

1. Install django-golive
2. Add django-golive to settings.INSTALLED_APPS
3. Create initial configuration file golive.yml
4. Deploy the basics
5. Set your secrets
5. Deploy the rest
6. Visit your page

Usage
--------
### Configuration

Create a golive.yml in the root of your Django-project. In the configuration file you define the target platform and
the desired stack.

    CONFIG:
      PLATFORM: DEDICATED
      STACK: CLASSIC

    ENVIRONMENTS:
      DEFAULTS:
        INIT_USER: myuser
        PROJECT_NAME: exampleproject
        USER: exampleuser
        PUBKEY: $HOME/.ssh/id_dsa.pub

      TESTING:
          SERVERNAME: golivetestin
          ROLES:
             APP_HOST:
               - golivehost1
               - golivehost2
             DB_HOST:
               - golivedb
             WEB_HOST:
               - goliveweb

### Install the project
    python manage.py init YOURENV     # YOURENV can be e.g. testing, integration, production

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

### Future of the platform dedicated

- Redhat (CentOS)

### Future of supported IaaS platforms

- OpenVZ
- OpenStack
- Amazon EC2

### Future of supported PaaS platforms

- Dotcloud
- Openshift


Builtin Components
----------
### golive.layers.base.BaseSetup
* OS Packages

    Installs basic required and handy packages like:

    `rsync, git, gcc, python-dev, postgresql-client, htop, curl, lsof, sysstat`

* Host file

    Adds entries for every host in environment to the file `/etc/hosts`.

### golive.layers.base.UserSetup
* User creation

    Creates the user with the name `USER`specified in `golive.yml`. For the first login
    a existant user `INIT_USER` with key-authentication is required to be able to perform these steps.

* SSH Pubkey

    Copies a pubkey `PUBKEY` to the `authorized_keys2` file on the servers to be able to login with key-authentication.

### golive.layers.web.NginxSetup
* Configure Frontend-Webserver

    Installs the package nginx and then creates out of `templates/golive/nginx.conf` a configuration file.
    The file is uploaded to the directory `/etc/nginx/sites-enabled/app.conf`.

<!-- TODO: ### golive.layers.cache.RedisSetup
- Cachehost (Redis Key/Value-Store for Caching)
-->
### golive.layers.app.PythonSetup
* Virtualenv Environment

    Creates a virtualenv in `$HOME/.virtualenvs` with the name of the project (`PROJECT_NAME`).
### golive.layers.db.PostgresSetup
* Postgresql installation

    Installs the packages `postgresql`.

* Configure Postgresql

    - Allow access from the subnet `192.168.0.0/16`.
    - Listen on the network interface.

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
    - Create database `PROJECT_NAME` on `DB_HOST` with owner `USER`.

* Synchronize Databaseschema

    Exceutes `syncdb` django command. If south is installed, `migratedb` in addition.

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

[example-stackfile]: golive/stacks/ "Example Stackfile"

[ubuntu]: http://ubuntu.com "Ubuntu"
[debian]: http://debian.org "Debian"
[redhat]: http://redhat.org "Redhat"
[centos]: http://debian.org "Centos"
<<<<<<< HEAD
[nginxsetup]: http://www.bla.com
[newrelic]: http://www.newrelic.com "New Relic"
=======
>>>>>>> be0cd300de5a15d854417ada35f4844102557b7e
