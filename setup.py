from setuptools import setup, find_packages
import sys, os

version = '1.4.4'

setup(name='Products.ResourceRegistries',
      version=version,
      description="Registry for managing CSS and JS",
      long_description="""\
Registry for CSS and JS files which allows merging of several resources into one.
Includes a packer for CSS and JS which can be used standalone.""",
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
      download_url='http://plone.org/products/resourceregistries/releases',
      install_requires=[
        'setuptools',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
)
