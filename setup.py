from distutils.core import setup

setup(
    name='txOpenvpnMgmt',
    version='0.1.0',
    author='Mike Mattice',
    author_email='mattice@debian.org',
    packages=['txopenvpnmgmt',],
    scripts=[],
    url='http://pypi.python.org/pypi/txOpenvpnMgmt/',
    license='LICENSE.txt',
    description='Twisted Openvpn Mgmt interface protocol',
    long_description=open('README.txt').read(),
    install_requires=[
    ],
)
