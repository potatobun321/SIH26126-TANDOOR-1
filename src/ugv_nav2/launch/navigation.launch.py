import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import TimerAction
from launch_ros.actions import Node

def generate_launch_description():
    pkg_nav2 = get_package_share_directory('ugv_nav2')
    nav2_params_file = os.path.join(pkg_nav2, 'config', 'nav2_params.yaml')

    lifecycle_nodes = [
        'controller_server',
        'smoother_server',
        'planner_server',
        'behavior_server',
        'bt_navigator',
        'velocity_smoother'
    ]

    # 1. Controller Server (outputs cmd_vel_nav to velocity_smoother)
    node_controller = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[nav2_params_file],
        remappings=[('cmd_vel', 'cmd_vel_nav')]
    )

    # 2. Path Smoother Server
    node_smoother = Node(
        package='nav2_smoother',
        executable='smoother_server',
        name='smoother_server',
        output='screen',
        parameters=[nav2_params_file]
    )

    # 3. Global Planner Server
    node_planner = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[nav2_params_file]
    )

    # 4. Behavior Server (Spin, Backup, Wait recovery actions)
    node_behavior = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        output='screen',
        parameters=[nav2_params_file],
        remappings=[('cmd_vel', 'cmd_vel_nav')]
    )

    # 5. BT Navigator (Executes navigation action tree)
    node_bt_navigator = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[nav2_params_file]
    )

    # 6. Velocity Smoother (takes cmd_vel_nav, applies smooth limits, outputs directly to /cmd_vel)
    node_velocity_smoother = Node(
        package='nav2_velocity_smoother',
        executable='velocity_smoother',
        name='velocity_smoother',
        output='screen',
        parameters=[nav2_params_file],
        remappings=[
            ('cmd_vel', 'cmd_vel_nav'),
            ('cmd_vel_smoothed', '/cmd_vel')
        ]
    )

    # 7. Navigation Lifecycle Manager (automatically activates the 6 nodes after clock & bridge are ready)
    node_lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'autostart': True,
            'node_names': lifecycle_nodes,
            'bond_timeout': 10.0,
            'attempt_respawn_reconnection': True
        }]
    )

    delayed_lifecycle_manager = TimerAction(
        period=4.0,
        actions=[node_lifecycle_manager]
    )

    return LaunchDescription([
        node_controller,
        node_smoother,
        node_planner,
        node_behavior,
        node_bt_navigator,
        node_velocity_smoother,
        delayed_lifecycle_manager
    ])
