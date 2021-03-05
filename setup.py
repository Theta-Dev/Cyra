# coding=utf-8
import setuptools

with open('README.rst') as f:
    README = f.read()

setuptools.setup(
    name='Cyra',
    version='0.1.0',
    author='ThetaDev',
    description='Cyra is a simple config framework for Python.',
    long_description=README,
    long_description_content_type='text/x-rst',
    license='MIT License',
    url="https://github.com/Theta-Dev/Cyra",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    py_modules=['cyra'],
    install_requires=[
        'tomlkit>=0.7.0,<1.0.0'
    ],
    packages=setuptools.find_packages(exclude=['tests*']),
)
