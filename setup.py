from setuptools import setup, find_packages

version = '3.0.8'

setup(
    name='Products.ResourceRegistries',
    version=version,
    description="Registry for managing CSS and JS",
    long_description='\n\n'.join([
        open("README.rst").read(),
        open("CHANGES.rst").read(),
    ]),
    classifiers=[
        "Development Status :: 6 - Mature",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 5.0",
        "Framework :: Plone :: 5.1",
        "Framework :: Zope2",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Pre-processors",
    ],
    keywords='CSS Javascript Zope Packer',
    author='Plone Foundation',
    author_email='plone-developers@lists.sourceforge.net',
    url='https://pypi.org/project/Products.ResourceRegistries',
    license='GPL version 2',
    packages=find_packages(),
    namespace_packages=['Products'],
    include_package_data=True,
    zip_safe=False,
    extras_require=dict(
        test=[
            'zope.contentprovider',
        ],
    ),
    install_requires=[
        'setuptools',
        'six',
        'zope.component',
        'zope.interface',
        'zope.viewlet',
        'Products.CMFCore',
        'plone.protect >= 3.0.0a1',
        'Products.GenericSetup',
        'Acquisition',
        'DateTime',
        'ZODB3',
        'Zope2',
        'plone.app.registry',
    ],
)
