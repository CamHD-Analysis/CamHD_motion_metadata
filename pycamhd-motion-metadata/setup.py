from setuptools import setup
import io
import re
import os

def find_version(*file_paths):
    with io.open(os.path.join(os.path.dirname(__file__), *file_paths),
                    encoding="utf8") as fp:
        version_file = fp.read()

        version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                                  version_file, re.M)
        if version_match:
            return version_match.group(1)
        raise RuntimeError("Unable to find version string.")

setup(name='pycamhd.motionmetadata',
      version=find_version('pycamhd', 'motionmetadata', '__init__.py'),
      description='Module for parsing CamHD Motion Metadata files',
      long_description='README.md',
      url='https://github.com/CamHD-Analysis/pycamhd-motion-metadata',
      author='Aaron Marburg',
      author_email='amarburg@apl.washington.edu',
      license='MIT',
      python_requires='>=3',
      packages=['pycamhd.motionmetadata'],
      install_requires=['pandas', 'cython', 'pycamhd-lazycache', 'scikit-image'],
      setup_requires=['pytest-runner'],
      tests_require=['pytest'])
