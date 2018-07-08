from setuptools import setup, find_packages

setup(
  name='pureapi',
  version='1.0.0',
  description='Tools for working with Elsevier\'s Pure API.',
  url='https://github.com/UMNLibraries/pureapi',
  author='David Naughton',
  author_email='nihiliad@gmail.com',
  packages=find_packages(exclude=['tests','docs']),
  install_requires=[
    'addict',
    'requests',
    'tenacity',
  ],
  extras_require={
    'dev': [
      'pytest',
      'python-dotenv',
    ],
  }
)
