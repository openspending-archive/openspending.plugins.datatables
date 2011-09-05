from setuptools import setup, find_packages
import sys, os

from datatables import __version__

setup(
    name='openspending.plugins.datatables',
    version=__version__,
    description='OpenSpending Data Tables',
    keywords='openspending openspending-plugin datatables',
    author='Open Knowledge Foundation',
    author_email='okfn-help at lists okfn org',
    url='http://github.com/okfn/openspending.plugins.datatables',
    license='GPL v3',
    install_requires=[
        'openspending'
    ],
    packages=find_packages('.packageroot'),
    package_dir={'': '.packageroot'},
    namespace_packages=['openspending', 'openspending.plugins'],
    include_package_data=True,
    message_extractors = {
        'datatables': [
            ('**.py', 'python', None),
            ('public/**', 'ignore', None)
        ]
    },
    entry_points={
        'openspending.plugins': [
            'datatables = openspending.plugins.datatables:DataTablesPlugin'
        ]
    },
    zip_safe=False
)