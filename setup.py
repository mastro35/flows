"""
flows
-----
flows allows you to create chains of simple actions and conditional statements
called recipes.

It's somehow similar to IFTTT service but based on local events.

Copyright 2016 Davide Mastromatteo
License: Apache 2.0
"""

# import platform

from setuptools import setup
from flows.Global import VERSION

setup_requires = [
    #    "adodbapi>=2.6.0.7",
    "watchdog>=0.8.3",
    "zmq>=0.0.0",
    "croniter>=0.3.12",
    "pytyler>=0.2",
]

# if platform.system() == 'Windows':
#     setup_requires.append('pypiwin32>=220')

setup(
    name="flows",
    version=VERSION,
    url="http://github.com/mastro35/flows/",
    license="Apache-2.0",
    author="Davide Mastromatteo",
    author_email="mastro35@gmail.com",
    description="a Python automated workflow generator",
    long_description=__doc__,
    packages=["flows", "flows.Actions"],
    include_package_data=True,
    zip_safe=False,
    platforms="any",
    install_requires=setup_requires,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
    ],
    entry_points={"console_scripts": ["flows = flows.__main__:main"]},
)
