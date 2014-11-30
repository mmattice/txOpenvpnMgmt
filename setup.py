from distutils.core import setup
import versioneer
versioneer.VCS = 'git'
versioneer.versionfile_source = 'txopenvpnmgmt/_version.py'
versioneer.versionfile_build = None
versioneer.tag_prefix = 'v'
versioneer.parentdir_prefix = 'txOpenvpnMgmt-'

        

setup(
    name='txOpenvpnMgmt',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author='Mike Mattice',
    author_email='mattice@debian.org',
    packages=['txopenvpnmgmt',],
    scripts=[],
    url='http://pypi.python.org/pypi/txOpenvpnMgmt/',
    license='LICENSE.txt',
    description='Twisted Openvpn Mgmt interface protocol',
    long_description=open('README.txt').read(),
)
