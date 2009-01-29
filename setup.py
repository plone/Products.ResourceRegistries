from setuptools import setup, find_packages
import sys, os

version = '1.6.0'

setup(name='Products.ResourceRegistries',
      version=version,
      description="Registry for managing CSS and JS",
      long_description="""\
Registry for CSS and JS files which allows merging of several resources into one.
Includes a packer for CSS and JS which can be used standalone.""",
      classifiers=[
        "Framework :: Zope2",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        "Topic :: Software Development :: Pre-processors",
      ],
      keywords='CSS Javascript Zope Packer',
      author='Plone Foundation',
      author_email='plone-developers@lists.sourceforge.net',
      url='http://plone.org/products/resourceregistries/',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      extras_require=dict(
        test=[
            'zope.component',
            'zope.contentprovider',
            'Products.PloneTestCase',
        ]
      ),
      install_requires=[
        'setuptools',
        'zope.interface',
        'zope.viewlet',
        'Products.CMFCore',
        'Products.GenericSetup',
        # 'Acquisition',
        # 'DateTime',
        # 'ZODB3',
        # 'Zope2',
      ],
)
