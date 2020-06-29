
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="credbl", # Replace with your own username
    packages=['credbl',],
    version="0.0.2",
    author="Dima Lituiev",
    author_email="d.lituiev@gmail.com",
    description="package for database cofiguration and credential management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=['pymongo', 'pyyaml', 'click', 'keyring'],
    #packages=setuptools.find_packages(),
    # url="https://github.com/pypa/sampleproject",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

