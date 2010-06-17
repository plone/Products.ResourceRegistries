from setuptools import setup, find_packages
from os.path import join


version = open(join('Products', 'ResourceRegistries', 'version.txt')).read().strip()
readme = open(join('Products', 'ResourceRegistries', "README.txt")).read()
history = open(join('Products', 'ResourceRegistries', 'doc', 'HISTORY.txt')).read()

setup(name='Products.ResourceRegistries',
      version=version,
      description="Registry for managing CSS and JS",
      long_description=readme[readme.find('\n\n'):] + '\n' + history,
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Zope2",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Pre-processors",
      ],
      keywords='CSS Javascript Zope Packer',
      author='Plone Foundation',
      author_email='plone-developers@lists.sourceforge.net',
      url='http://svn.plone.org/svn/plone/ResourceRegistries',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'setuptools',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
)
