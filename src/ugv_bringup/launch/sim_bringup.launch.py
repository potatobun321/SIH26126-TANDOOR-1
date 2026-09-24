import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    pkg_bringup = get_package_share_directory('ugv_bringup')
    pkg_description = get_package_share_directory('ugv_description')
    
    # Paths
    sim_dir = os.path.abspath(os.path.join(pkg_bringup, '../../../../sim'))
    models_dir = os.path.join(sim_dir, 'models')
    materials_dir = os.path.join(sim_dir, 'materials')
    default_world = os.path.join(sim_dir, 'worlds', 'outdoor_terrain.sdf')
    urdf_path = os.path.join(pkg_description, 'urdf', 'ugv.urdf')
    bridge_config_path = os.path.join(pkg_bringup, 'config', 'ros_gz_bridge.yaml')

    # Ensure Gazebo Harmonic resolves local models and textures
    existing_resource_path = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    gz_resource_path = f"{sim_dir}:{models_dir}:{materials_dir}:{existing_resource_path}"
    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=gz_resource_path
    )

    headless = LaunchConfiguration('headless')

    declare_headless_cmd = DeclareLaunchArgument(
        'headless',
        default_value='False',
        description='Run Gazebo in headless mode (server only) for low resource usage'
    )

    # Read URDF
    with open(urdf_path, 'r') as f:
        robot_desc = f.read()

    # 1. Robot State Publisher
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_desc,
            'use_sim_time': True
        }]
    )

    # 2a. Gazebo Sim Launch (GUI mode: -r <world>)
    gz_sim_gui = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            ])
        ),
        condition=UnlessCondition(headless),
        launch_arguments={
            'gz_args': f'-r {default_world}'
        }.items()
    )

    # 2b. Gazebo Sim Launch (Headless server-only mode: -s -r <world>)
    gz_sim_headless = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            ])
        ),
        condition=IfCondition(headless),
        launch_arguments={
            'gz_args': f'-s -r {default_world}'
        }.items()
    )

    # 3. Spawn UGV in Gazebo
    node_spawn_ugv = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-name', 'outdoor_ugv',
            '-file', urdf_path,
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.3',
            '-Y', '0.0'
        ]
    )

    # 4. ros_gz Bridge
    node_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        output='screen',
        parameters=[{
            'config_file': bridge_config_path,
            'use_sim_time': True
        }]
    )

    # 5. Depth Image to LaserScan (Vision-based obstacle perception)
    node_depthimage_to_laserscan = Node(
        package='depthimage_to_laserscan',
        executable='depthimage_to_laserscan_node',
        name='depthimage_to_laserscan',
        output='screen',
        parameters=[{
            'scan_time': 0.033,
            'range_min': 0.3,
            'range_max': 15.0,
            'scan_height': 40,
            'output_frame': 'camera_link',
            'use_sim_time': True
        }],
        remappings=[
            ('depth', '/camera/depth/image_raw'),
            ('depth_camera_info', '/camera/camera_info'),
            ('scan', '/scan')
        ]
    )

    return LaunchDescription([
        set_gz_resource_path,
        declare_headless_cmd,
        gz_sim_gui,
        gz_sim_headless,
        node_spawn_ugv,
        node_robot_state_publisher,
        node_gz_bridge
    ])
