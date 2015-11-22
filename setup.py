from setuptools import setup


setup(name='codemon',
      version='0.1',
      description='Monitors your code for changes and runs affected tests',
      url='http://github.com/emintham/codemon',
      author='Emin Tham',
      author_email='emin@securitycompass.com',
      license='MIT',
      packages=['codemon'],
      install_requires=[
          'msgpack-python',
          'coverage',
          'pyyaml'
      ],
      test_suite='nose.collector',
      tests_require=['nose'],
      zip_safe=False)
