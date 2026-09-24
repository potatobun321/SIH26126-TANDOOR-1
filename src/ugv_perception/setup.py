from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'ugv_perception'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Tikka Techies',
    maintainer_email='team@tikkatechies.org',
    description='AI-driven semantic terrain segmentation and traversability mapping for outdoor UGV',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'terrain_segmentation_node = ugv_perception.terrain_segmentation_node:main',
        ],
    },
)
