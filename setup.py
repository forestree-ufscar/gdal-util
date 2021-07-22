import io

from setuptools import setup

with io.open("README.md", "rt", encoding="utf8") as f:
    readme = f.read()

setup(
    name="gdal_util",
    version="1.0.0",
    url="https://github.com/forestree-ufscar/gdal-util",
    license="Apache 2.0",
    maintainer="Rodolfo Cugler",
    maintainer_email="rodolfocugler@outlook.com",
    long_description=readme,
    packages=["gdal_util"],
    install_requires=[],
    include_package_data=True
)
