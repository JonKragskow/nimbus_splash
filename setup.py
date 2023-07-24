import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# DO NOT EDIT THIS NUMBER!
# IT IS AUTOMATICALLY CHANGED BY python-semantic-release
__version__ = "0.16.0"

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
