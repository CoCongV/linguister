import codecs
import os
from setuptools import (
    find_packages,
    setup,
)

about = {}
here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = "\n" + f.read()

with open(os.path.join(here, "linguister", "__version__.py")) as f:
    exec(f.read(), about)

requires = [
    'click', 'colorama', 'playsound', 'pygobject',
    'pycairo'
]

setup(
    name='linguister',
    version=about['__version__'],
    description='Terminal translation tool',
    long_description=long_description,
    long_description_content_type='text/markdown',
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
        'Operating System :: Unix',
        'Programming Language :: Python :: 3.9',
    ],
    test_suite='nose.collector',
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'linguister', 'pytest', 'pytest_cov', 'nose',
    ],
)
