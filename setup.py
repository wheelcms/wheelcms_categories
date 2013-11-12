from setuptools import setup, find_packages
import os

version = '0.9'

setup(name='wheelcms_categories',
      version=version,
      description="WheelCMS category implementation",
      long_description=open("README.txt").read(),
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='Ivo van der Wijk',
      author_email='wheelcms@in.m3r.nl',
      url='http://github.com/wheelcms/wheelcms_categories',
      license='BSD',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=[],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'pytest',
      ],
      entry_points={
      },

      )

