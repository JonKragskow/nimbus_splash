!\[PyPI\](https://img.shields.io/badge/dynamic/json?label=Pypi%20&query=%24.info.version&url=https%3A%2F%2Fpypi.org%2Fpypi%2Fnimbus_splash%2Fjson)

# nimbus_splash

Splash - the sound an orca would make if it had a Bath.

`nimbus_splash` package to make life easier when using the University of Bath's cloud computing suite for Orca calculations.


# Installation

Install using pip 

```
pip install nimbus_splash
```

Then add the following environment variable in your nimbus `~/.bash_rc` file
and set it to the name of your Research Allocation ID

```
export CLOUD_ACC=<name_here>
```

and source
```
source ~/.bashrc
```

# Usage

Run

```
nimbussplash -h
```
or 
```
splash -h
```
for options.
