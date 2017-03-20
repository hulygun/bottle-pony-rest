from distutils.core import setup

with open('requirements.txt') as f:
    requires = f.read().splitlines()

setup(
    name='bottle-pony-rest',
    version='1.0',
    packages=['bottle_pony_rest'],
    url='https://github.com/hulygun/bottle-pony-rest',
    license='MIT',
    author='hulygun',
    requires=requires,
    author_email='hulygun@gmail.com',
    description='Base Resource View for REST API via bottle framework and pony orm'
)
