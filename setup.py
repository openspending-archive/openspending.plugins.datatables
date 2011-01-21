from setuptools import setup, find_packages
import sys, os

from wdmmgext.datatables import __version__

setup(name='wdmmg-datatables',
      version=__version__,
      description="Where Does My Money Go? Data Tables",
      long_description="",
      classifiers=[], 
      keywords='wdmmg datatables js jquery',
      author='Open Knowledge Foundation',
      author_email='info@okfn.org',
      url='http://www.okfn.org',
      license='GPL v3',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      namespace_packages=['wdmmgext'],
      zip_safe=False,
      message_extractors = {
            'wdmmgext/datatables': [
                ('**.py', 'python', None)
                ],
            'theme': [
                ('templates/**.html', 'genshi', None),
                ('public/**', 'ignore', None)
                ],
            },
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      
      [wdmmg.plugins]
      datatables = wdmmgext.datatables:DataTablesGenshiStreamFilter
      """,
      )
