from setuptools import setup

package_name = 'teleop_twist_keyboard'

setup(
    name='teleop_twist_keyboard_ros2ws',
    version='2.4.0',
    packages=[package_name],
    py_modules=['teleop_twist_keyboard_ros2ws'],
    scripts=['scripts/teleop_twist_keyboard'],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='antonio',
    maintainer_email='antonio@local',
    description='Keyboard teleop for cmd_vel plus elbow arm control keys.',
    license='BSD-3-Clause',
)
