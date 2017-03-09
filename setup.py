from setuptools import setup, find_packages

version = '2.2.13'

setup(
    name='Products.ResourceRegistries',
    version=version,
    description="Registry for managing CSS and JS",
    long_description='\n\n'.join([
        open("README.rst").read(),
        open("CHANGES.rst").read(),
    ]),
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.3",
        "Framework :: Zope2",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Pre-processors",
    ],
    keywords='CSS Javascript Zope Packer',
    author='Plone Foundation',
    author_email='plone-developers@lists.sourceforge.net',
    url='http://pypi.python.org/pypi/Products.ResourceRegistries',
    license='GPL version 2',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['Products'],
    include_package_data=True,
    zip_safe=False,
    extras_require=dict(
        test=[
            'zope.contentprovider',
            'Products.PloneTestCase',
        ],
    ),
    install_requires=[
        'setuptools',
        'zope.component',
        'zope.interface',
        'zope.viewlet',
        'Products.CMFCore',
        'Products.GenericSetup',
        'Acquisition',
        'DateTime',
        'ZODB3',
        'Zope2',
        'plone.app.registry',
    ],
)
