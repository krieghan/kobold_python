from setuptools import setup, find_packages

setup(
    name='kobold',
    version='8',
    packages=find_packages(),
    install_requires=['python-dateutil==2.2'],
    tests_require=['nosetests'],
)
