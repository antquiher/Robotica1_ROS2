# Robotica1_ROS2

## Ejecución

1. Abre una terminal nueva y entra en el entorno del curso:

```bash
source ~/.bashrc
ai-on
```

2. Compila el workspace:

```bash
cd ~/ros2_ws
colcon build --symlink-install
```

3. Carga el overlay del workspace:

```bash
source ~/ros2_ws/install/setup.bash
```

4. Lanza la simulación del robot:

```bash
ros2 launch diff_robot_urdf sim.launch.py
```

5. Para ver la cámara frontal estéreo en color, abre otro terminal y ejecuta:

```bash
source ~/.bashrc
ai-on
source ~/ros2_ws/install/setup.bash
ros2 launch diff_robot_urdf camera_view.launch.py
```

## Comandos útiles

Movimiento de la base y del brazo:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Si quieres cambiar el mapa o la posición inicial del robot, revisa:

- [sim.launch.py](src/diff_robot_urdff/launch/sim.launch.py)
- [Loyola_Hospital_min.world](src/diff_robot_urdff/worlds/Loyola_Hospital_min.world)
