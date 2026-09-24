import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_localization = get_package_share_directory('ugv_localization')
    ekf_config_path = os.path.join(pkg_localization, 'config', 'ekf.yaml')

    enable_vo = LaunchConfiguration('enable_vo')

    declare_enable_vo = DeclareLaunchArgument(
        'enable_vo',
        default_value='False',
        description='Whether to run heavy RTAB-Map RGB-D visual odometry (benchmark only)'
    )

    # 1. EKF State Estimation Node (fusing wheel odometry and IMU) — 1.8cm ATE RMSE, <1% CPU
    node_ekf = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_config_path, {'use_sim_time': True}]
    )

    # 2. Static transform from map -> odom (for GPS-denied navigation reference)
    node_static_tf_map_odom = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_transform_publisher_map_odom',
        arguments=['--frame-id', 'map', '--child-frame-id', 'odom'],
        parameters=[{'use_sim_time': True}]
    )

    # 3. Visual-Inertial Odometry Node (Optional benchmark)
    vo_launch_path = os.path.join(pkg_localization, 'launch', 'visual_odometry.launch.py')
    include_vo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(vo_launch_path),
        condition=IfCondition(enable_vo),
        launch_arguments={'use_sim_time': 'true'}.items()
    )

    return LaunchDescription([
        declare_enable_vo,
        node_ekf,
        node_static_tf_map_odom,
        include_vo
    ])
