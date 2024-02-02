from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='five9_agent_sup_rest',
    version='0.9.2b1',
    packages=find_packages(),
    description='A module for interacting with Five9 Supervisor REST API',
    long_description=open('README.md').read(),
    install_requires=requirements,
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.12',
    ],
)
