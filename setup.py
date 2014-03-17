from distutils.core import setup

setup(name='golive',
      version='0.2',
      py_modules=['golive'],
      install_requires=['flup', 'Fabric', 'pyyaml', 'colorlog'],
)
