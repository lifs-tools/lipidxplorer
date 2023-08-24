from setuptools import setup, find_packages

setup(name="simtrim",
      version='0.0.2',
      packages=find_packages(),
      install_requires=[
    "numpy",
    "brain-isotopic-distribution",
    "ms_peak_picker",
    "ms_deisotope",
    "pathlib",
    "gooey"
]
      )
# pip install -e . to install for develop
