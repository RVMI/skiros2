# Use ROS Noetic base image
FROM ros:noetic-ros-base
RUN apt-get update && apt-get install -y git tmux python3-pip python3-catkin-tools ros-noetic-rosmon

# Set the working directory in the container
RUN mkdir -p /catkin_ws/src
WORKDIR /catkin_ws
RUN /bin/bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash; catkin init"
RUN /bin/bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash; catkin build"
WORKDIR /catkin_ws/src
RUN git clone https://github.com/RVMI/skiros2
RUN git clone https://github.com/RVMI/skiros2_std_lib
RUN git clone https://github.com/RVMI/skiros2_examples
RUN git clone https://github.com/RVMI/skiros2_template_lib

COPY ./skiros2/scripts/install_fd_task_planner.sh /root/install_fd_task_planner.sh
RUN /root/install_fd_task_planner.sh ~/.skiros/planner

# Install dependencies & python dependencies
RUN /bin/bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash; rosdep install --from-paths . --ignore-src --rosdistro=$ROS_DISTRO -y"
RUN /bin/bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash; cd skiros2; pip install -r requirements.txt --user; cd .."

# Build the catkin workspace
RUN /bin/bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash; cd /catkin_ws && catkin build"
# Add source command to bashrc
RUN echo "source /catkin_ws/devel/setup.bash" >> /root/.bashrc

# tmux session
ENTRYPOINT ["/bin/bash"]