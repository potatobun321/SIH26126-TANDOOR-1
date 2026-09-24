import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    pkg_bringup = get_package_share_directory('ugv_bringup')
    pkg_localization = get_package_share_directory('ugv_localization')
    pkg_nav2 = get_package_share_directory('ugv_nav2')
    pkg_perception = get_package_share_directory('ugv_perception')

    headless = LaunchConfiguration('headless')

    declare_headless = DeclareLaunchArgument(
        'headless',
        default_value='False',
        description='Whether to run Gazebo in headless mode (server only)'
    )

    declare_enable_vo = DeclareLaunchArgument(
        'enable_vo',
        default_value='False',
        description='Run heavy RTAB-Map RGB-D visual odometry (benchmark only)'
    )

    enable_vo = LaunchConfiguration('enable_vo')

    # 1. Simulation & Robot State Publisher Bringup
    sim_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'sim_bringup.launch.py')
        ),
        launch_arguments={'headless': headless}.items()
    )

    # 2. Baseline Localization (Wheel+IMU EKF) — 1.8cm ATE RMSE, <1% CPU
    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_localization, 'launch', 'localization.launch.py')
        ),
        launch_arguments={'enable_vo': enable_vo}.items()
    )

    # 3. Nav2 Navigation Stack
    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav2, 'launch', 'navigation.launch.py')
        )
    )

    # 4. AI Terrain Perception & Traversability Segmentation
    perception = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_perception, 'launch', 'perception.launch.py')
        )
    )

    return LaunchDescription([
        declare_headless,
        declare_enable_vo,
        sim_bringup,
        localization,
        navigation,
        perception
    ])
