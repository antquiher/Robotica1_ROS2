from launch import LaunchDescription
from launch.actions import ExecuteProcess


def generate_launch_description():
    left_view = ExecuteProcess(
        cmd=[
            'ros2', 'run', 'image_tools', 'showimage',
            '--ros-args', '-r', 'image:=/front_stereo/left/image'
        ],
        output='screen'
    )

    right_view = ExecuteProcess(
        cmd=[
            'ros2', 'run', 'image_tools', 'showimage',
            '--ros-args', '-r', 'image:=/front_stereo/right/image'
        ],
        output='screen'
    )

    return LaunchDescription([left_view, right_view])