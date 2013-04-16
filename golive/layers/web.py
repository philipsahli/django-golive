from golive.layers.base import BaseTask, DebianPackageMixin


class NginxSetup(BaseTask, DebianPackageMixin):
    package_name = 'nginx'
    ROLES = "WEB_HOST"
