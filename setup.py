from setuptools import setup

setup(
    name='revshellgen',
    version='1.0',
    author='Kristof Toth',
    author_email='tothkrisi@gmail.com',
    description='Standalone python script for generating reverse shells easily and automating the boring stuff like '
                'URL encoding the command and setting up a listener.',
    install_requires=['pyperclip', 'colorama', 'readchar']
)
