import setuptools

long_description = '''
Splash - the sound an Orca would make if it had a Bath.\n\n

`nimbus_splash`, or `splash` for short, is a package to make life easier
when using the University of Bath's `Nimbus` cloud computing suite for Orca calculations.\n\n

Please see the `nimbus_splash` documentation for more details.
'''

# DO NOT EDIT THIS NUMBER!
# IT IS AUTOMATICALLY CHANGED BY python-semantic-release
__version__ = "1.0.3"

setuptools.setup(
    name="Nimbus Splash",
    version=__version__,
    author="Jon Kragskow",
    author_email="jgck20@bath.ac.uk",
    description="A package to make life easier when using the University of \
        Bath's cloud computing suite for Orca calculations.",
    long_descrption=long_description,
    url="https://github.com/jonkragskow/nimbus_splash",
    # project_urls={
        # "Bug Tracker": "",
        # "Documentation": ""
    # },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "."},
    packages=setuptools.find_packages(),
    python_requires=">=3.10",
    install_requires=["numpy", "xyz_py"],
    entry_points={
        'console_scripts': [
            'splash = nimbus_splash.cli:interface',
            'nimbussplash = nimbus_splash.cli:interface'
        ]
    }
)
