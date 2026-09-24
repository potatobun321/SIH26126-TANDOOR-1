import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )

    # RTAB-Map RGB-D Visual Odometry Node with Motion Prior Guess
    rgbd_odometry_node = Node(
        package='rtabmap_odom',
        executable='rgbd_odometry',
        name='visual_odometry',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'frame_id': 'base_footprint',
            'odom_frame_id': 'odom_vo',
            'publish_tf': False,
            'approx_sync': True,
            'approx_sync_max_interval': 0.10,
            'queue_size': 20,
            'wait_for_transform': 0.2,
            'publish_null_when_lost': False,
            'Odom/Strategy': '0',               # Frame-to-Map
            'Odom/ResetCountdown': '1',          # Re-initialize on tracking loss
            'Odom/Holonomic': 'false',           # Non-holonomic ground vehicle
            'Vis/MinInliers': '4',              # Inlier threshold for outdoor heightmap
            'Vis/FeatureType': '2',              # ORB features
            'Vis/MaxFeatures': '1000',          # Feature pool
            'FAST/Threshold': '10',              # Sensitive corner detection on dirt/grass
            'OdomF2M/BundleAdjustment': '1',     # Local BA
        }],
        remappings=[
            ('rgb/image', '/camera/image_raw'),
            ('depth/image', '/camera/depth/image_raw'),
            ('rgb/camera_info', '/camera/camera_info'),
            ('imu', '/imu'),
            ('odom', '/odom_vo')
        ]
    )

    return LaunchDescription([
        declare_use_sim_time,
        rgbd_odometry_node
    ])
