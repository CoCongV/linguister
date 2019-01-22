from os.path import dirname, join
from setuptools import (
    find_packages,
    setup,
)

requires = [
    'aiohttp', 'click', 'requests', 'colorama', 'playsound', 'pygobject',
    'pycairo'
]

with open(join(dirname(__file__), 'linguister/VERSION.txt'), 'rb') as f:
    version = f.read().decode('ascii').strip()

setup(
    name='linguister',
    version=version,
    description='Terminal translation tool',
    packages=find_packages(exclude=[]),
    author='CoCong',
    author_email='cong.lv.yx@gmail.com',
    license='MIT',
    package_data={
        '': ['*.*']
    },
    install_requires=requires,
    zip_safe=False,
    entry_points={
        "console_scripts": [
            'translator = linguister:translate',
            'trans = linguister:translate',
            'fy = linguister:translate',
            'linguister = linguister:translate',
            'linguister-cli = linguister:cli'
        ]
    },
    classifiers=[
        'Programming Language :: Python',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    test_suite='nose.collector',
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'linguister', 'pytest', 'pytest_cov', 'nose',
    ],
)
