from setuptools import find_packages, setup

package_name = 'sumo_ros_bridge_py'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/sumo_ros_bridge_py/sim', ['sim/map.sumocfg', 'sim/my_city.net.xml', 'sim/map.osm', 'sim/trips.trips.xml', 'sim/city.net.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Miguel Rodrigues',
    maintainer_email='1181734@isep.ipp.pt',
    description='Python bridge node for SUMO-ROS2 integration.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'bridge_node = sumo_ros_bridge_py.bridge_node:main',
            'traffic_data_subscriber = sumo_ros_bridge_py.traffic_data_subscriber:main',
        ],
    },
)