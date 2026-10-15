FROM ros:humble

ARG HOST_UID=1000
ARG HOST_GID=1000
ENV DEBIAN_FRONTEND=noninteractive \
    GZ_VERSION=harmonic

RUN apt-get update && apt-get install -y --no-install-recommends \
      sudo git wget curl gnupg lsb-release ca-certificates default-jre \
      ros-dev-tools mesa-utils x11-apps tmux nano \
 && rm -rf /var/lib/apt/lists/*

# Gazebo Harmonic
RUN curl -fsSL https://packages.osrfoundation.org/gazebo.gpg \
      -o /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg \
 && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" \
      > /etc/apt/sources.list.d/gazebo-stable.list \
 && apt-get update && apt-get install -y gz-harmonic \
 && rm -rf /var/lib/apt/lists/*

# Non-root user matching host UID
RUN groupadd -g ${HOST_GID} student \
 && useradd -m -u ${HOST_UID} -g ${HOST_GID} -s /bin/bash student \
 && echo "student ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/student \
 && mkdir -p /opt/ardu_ws/src && chown -R student:student /opt/ardu_ws

USER student
WORKDIR /opt/ardu_ws
ENV USER=student

RUN vcs import --recursive \
      --input https://raw.githubusercontent.com/ArduPilot/ardupilot/master/Tools/ros2/ros2.repos src \
 && vcs import --recursive \
      --input https://raw.githubusercontent.com/ArduPilot/ardupilot_gz/main/ros2_gz.repos src

RUN cd src/ardupilot && Tools/environment_install/install-prereqs-ubuntu.sh -y

RUN sudo apt-get update \
 && . /opt/ros/humble/setup.sh \
 && rosdep update \
 && rosdep install --from-paths src --ignore-src -r -y \
 && sudo rm -rf /var/lib/apt/lists/*

# Micro-XRCE-DDS-Gen (required by ardupilot_sitl)
RUN sudo apt-get update && sudo apt-get install -y default-jdk \
 && sudo rm -rf /var/lib/apt/lists/* \
 && git clone --recurse-submodules https://github.com/ardupilot/Micro-XRCE-DDS-Gen.git /opt/ardu_ws/Micro-XRCE-DDS-Gen \
 && cd /opt/ardu_ws/Micro-XRCE-DDS-Gen && ./gradlew assemble
ENV PATH=/opt/ardu_ws/Micro-XRCE-DDS-Gen/scripts:/home/student/.local/bin:$PATH

RUN . /opt/ros/humble/setup.sh \
 && colcon build --parallel-workers 2 \
      --packages-up-to ardupilot_gz_bringup ardupilot_dds_tests

# Fix: robot_state_publisher cannot resolve the package:// URI of the drone model
RUN sed -i 's#"package://ardupilot_gazebo/models/iris_with_standoffs"#"model://iris_with_standoffs"#' \
      /opt/ardu_ws/install/ardupilot_gz_bringup/share/ardupilot_gz_bringup/launch/robots/iris_lidar.launch.py

RUN echo 'source /opt/ros/humble/setup.bash' >> ~/.bashrc \
 && echo 'source /opt/ardu_ws/install/setup.bash' >> ~/.bashrc \
 && echo '[ -f ~/fpv_labs/install/setup.bash ] && source ~/fpv_labs/install/setup.bash' >> ~/.bashrc

WORKDIR /home/student
CMD ["sleep", "infinity"]
