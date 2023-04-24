#!/usr/bin/env python3
import rospy
from turtlesim.srv import Spawn
from turtlesim.srv import SetPen
from turtlesim.msg import Pose
from geometry_msgs.msg import Twist
from turtlesim.srv import TeleportAbsolute
from std_srvs.srv import Empty
from math import radians, atan2, sqrt, pi
import time
import threading


def change_background_color():
    rospy.wait_for_service('/clear')
    clear_background = rospy.ServiceProxy('/clear', Empty)
    rospy.set_param('/turtlesim/background_r', 211)
    rospy.set_param('/turtlesim/background_g', 211)
    rospy.set_param('/turtlesim/background_b', 211)
    clear_background()

def spawn_turtle(name, x, y, theta):
    rospy.wait_for_service('/spawn')
    spawner = rospy.ServiceProxy('/spawn', Spawn)
    spawner(x, y, theta, name)

def set_pen(name, r, g, b, width, off):
    rospy.wait_for_service(f'/{name}/set_pen')
    pen = rospy.ServiceProxy(f'/{name}/set_pen', SetPen)
    pen(r, g, b, width, off)


def move_in_straight_line(name, x, y, linear_velocity, publ_msg, rate):
    pose_msg = rospy.wait_for_message(f'/{name}/pose', Pose)
    twist = Twist()

    twist.linear.x = linear_velocity
    twist.linear.y = 0
    twist.linear.z = 0
    twist.angular.x = 0
    twist.angular.y = 0
    twist.angular.z = 0

    distance = ((x - round(pose_msg.x, 4)) ** 2 + (y - round(pose_msg.y, 4)) ** 2) ** 0.5

    t0 = rospy.Time.now().to_sec()
    current_distance = 0

    while(current_distance < distance):
        publ_msg.publish(twist)
        rate.sleep()
        current_distance = linear_velocity * (rospy.Time.now().to_sec() - t0)

    twist.linear.x = 0
    twist.linear.y = 0
    publ_msg.publish(twist)
    rospy.sleep(1)



def move_in_circle(name, rad, deg, publ_msg, rate):
    publ_msg = rospy.Publisher(f'/{name}/cmd_vel', Twist, queue_size=10)
    twist = Twist()

    vel_lin = 0.5
    ang = deg * 3.14 /180
    vel_ang = vel_lin/rad
    direction = 1 if deg>0 else -1

    twist.linear.x = 0.5
    twist.linear.y = 0
    twist.linear.z = 0
    twist.angular.x = 0
    twist.angular.y = 0
    twist.angular.z = vel_ang * direction

    time = abs(ang / vel_ang)
    start_time = rospy.get_time()

    while  (rospy.get_time() - start_time) < time:
        publ_msg.publish(twist)
        rate.sleep()

    twist.linear.x = 0
    twist.angular.z = 0
    publ_msg.publish(twist)
    rospy.sleep(1)



def rotate(name, x, y, angular_velocity, publ_msg, rate):
    pose_msg = rospy.wait_for_message(f'/{name}/pose', Pose)
    twist = Twist()
    angular_speed = angular_velocity*2*pi/360
    relative_angle = atan2(y-pose_msg.y, x-pose_msg.x)
    
    twist.linear.y = 0
    twist.linear.x = 0
    twist.linear.z = 0
    twist.angular.x = 0
    twist.angular.y = 0
    
    # calculate the minimum angle needed to rotate
    angle_diff = relative_angle - pose_msg.theta
    if angle_diff > pi:
        angle_diff -= 2*pi
    elif angle_diff < -pi:
        angle_diff += 2*pi
    
    # choose the direction to rotate based on the minimum angle
    if angle_diff > 0:
        twist.angular.z = abs(angular_speed) #clockwise
    else:
        twist.angular.z = -abs(angular_speed) #counter-clockwise

    t0 = rospy.Time.now().to_sec()
    current_angle = 0

    while(current_angle < abs(angle_diff)):
        publ_msg.publish(twist)
        t1 = rospy.Time.now().to_sec()
        current_angle = angular_speed*(t1-t0)
        rate.sleep()

    twist.angular.z = 0
    publ_msg.publish(twist)
    rospy.sleep(1)



def teleportation(name, x, y, initial):
    if(initial):
        set_pen(name, 0, 0, 0, 0, 1)
    teleport = rospy.ServiceProxy(f'/{name}/teleport_absolute', TeleportAbsolute)
    teleport(x, y, 0)
    if(initial):
        if(name == "turtle1"):
            set_pen("turtle1", 255, 0, 0, 3, 0)
        if(name == "turtle2"):
            set_pen("turtle2", 0, 255, 0, 3, 0)
        if(name == "turtle3"):
            set_pen("turtle3", 0, 0, 255, 3, 0)
    

def draw_initials():
    name = "turtle1"
    rate = rospy.Rate(10)
    publ_msg = rospy.Publisher(f'/{name}/cmd_vel', Twist, queue_size=10)
    # Draw the initials "UBF" with turtle1
    teleportation(name, 1.5, 9.5, True)

    #draw U
    rotate(name, 1.4, 6.5, 30, publ_msg, rate)
    move_in_straight_line(name, 1.5, 7.5, 2, publ_msg, rate)
    move_in_circle(name, 1, 175, publ_msg, rate)
    move_in_straight_line(name, 3.2, 9.4, 2, publ_msg, rate)

    #draw B
    teleportation(name, 4.5, 9.5, True)
    move_in_straight_line(name, 5.5, 9.5, 2, publ_msg, rate)
    move_in_circle(name, 0.75, -180, publ_msg, rate)
    rotate(name, 6.5, 8, 30, publ_msg, rate)
    move_in_circle(name, 0.75, -175, publ_msg, rate)
    move_in_straight_line(name, 4.5, 6.5, 2, publ_msg, rate)
    rotate(name, 4.3, 9.5, 30, publ_msg, rate)
    move_in_straight_line(name, 4.5, 9.4, 2, publ_msg, rate)

    #draw F
    teleportation(name, 7.5, 9.5, True)
    move_in_straight_line(name, 9.5, 9.5, 2, publ_msg, rate)
    rotate(name, 7.5, 9.7, 30, publ_msg, rate)
    move_in_straight_line(name, 7.5, 9.5, 2, publ_msg, rate)
    rotate(name, 7.15, 6.5, 30, publ_msg, rate)
    move_in_straight_line(name, 7.5, 6.5, 2, publ_msg, rate)
    rotate(name, 7.15, 8, 30, publ_msg, rate)
    move_in_straight_line(name, 7.5, 8, 2, publ_msg, rate)
    rotate(name, 9, 8.25, 30, publ_msg, rate)
    move_in_straight_line(name, 9, 8, 2, publ_msg, rate)


def draw_student_id():
    name = "turtle2"
    rate = rospy.Rate(10)
    #Draw the last 3 digits of student ID "300" with turtle2
    publ_msg = rospy.Publisher(f'/{name}/cmd_vel', Twist, queue_size=10)

    # draw 3
    teleportation(name, 1.5, 4.5, True)
    move_in_straight_line(name, 3.5, 4.5, 2, publ_msg, rate)
    rotate(name, 3.4, 3, 30, publ_msg, rate)
    move_in_straight_line(name, 3.5, 1.5, 2, publ_msg, rate)
    rotate(name, 1.5, 1.2, 30, publ_msg, rate)
    move_in_straight_line(name, 1.5, 1.5, 2, publ_msg, rate)
    rotate(name, 3.5, 1.2, 30, publ_msg, rate)
    move_in_straight_line(name, 3.1, 1.5, 2, publ_msg, rate)
    rotate(name, 3.4, 3, 30, publ_msg, rate)
    move_in_straight_line(name, 3.5, 3, 2, publ_msg, rate)
    rotate(name, 1.5, 3.3, 30, publ_msg, rate)
    move_in_straight_line(name, 1.7, 3, 2, publ_msg, rate)

    #draw first 0 
    teleportation(name, 4.5, 4.5, True)
    move_in_straight_line(name, 6.5, 4.5, 2, publ_msg, rate)
    rotate(name, 6.7, 1.5, 30, publ_msg, rate)
    move_in_straight_line(name, 6.5, 1.5, 2, publ_msg, rate)
    rotate(name, 4.5, 1.3, 30, publ_msg, rate)
    move_in_straight_line(name, 4.7, 1.5, 2, publ_msg, rate)
    rotate(name, 4.3, 4.5, 30, publ_msg, rate)
    move_in_straight_line(name, 4.3, 4.5, 2, publ_msg, rate)

    #draw second 0 
    teleportation(name, 7.5, 4.5, True)
    move_in_straight_line(name, 9.5, 4.5, 2, publ_msg, rate)
    rotate(name, 9.7, 1.5, 30, publ_msg, rate)
    move_in_straight_line(name, 9.5, 1.5, 2, publ_msg, rate)
    rotate(name, 7.5, 1.3, 30, publ_msg, rate)
    move_in_straight_line(name, 7.7, 1.5, 2, publ_msg, rate)
    rotate(name, 7.3, 4.5, 30, publ_msg, rate)
    move_in_straight_line(name, 7.5, 4.5, 2, publ_msg, rate)


def draw_frame():
    name = "turtle3"
    rate = rospy.Rate(10)
    #Draw the frame with turtle3
    publ_msg = rospy.Publisher(f'/{name}/cmd_vel', Twist, queue_size=10)
    teleportation(name, 0.5, 0.5, True)
    move_in_straight_line(name, 10.5, 0.5, 2, publ_msg, rate)
    rotate(name, 11, 10.5, 30, publ_msg, rate)
    move_in_straight_line(name, 10.5, 10.5, 2, publ_msg, rate)
    rotate(name, 0.5, 11.3, 30, publ_msg, rate)
    move_in_straight_line(name, 0.8, 10.5, 2, publ_msg, rate)
    rotate(name, 0, 0.5, 30, publ_msg, rate)
    move_in_straight_line(name, 0.5, 0.5, 2, publ_msg, rate)
    rotate(name, 10.5, 0.5, 30, publ_msg, rate)


def main():
    rospy.init_node('draw_S', anonymous=True)

    change_background_color()

    spawn_turtle("turtle2", 3, 6, 0)
    spawn_turtle("turtle3", 9, 6, 0)

    # Set pen colors and width
    set_pen("turtle1", 255, 0, 0, 8, 0)
    set_pen("turtle2", 0, 255, 0, 8, 0)
    set_pen("turtle3", 0, 0, 255, 8, 0)

    # Draw initials, student ID and frame with turtle1, turtle2 and turtle3
    t1 = threading.Thread(target=draw_initials, name="t1")
    t2 = threading.Thread(target=draw_student_id, name="t2")
    t3 = threading.Thread(target=draw_frame, name="t3")

    t1.start()
    t2.start()
    t3.start()

    t1.join()
    t2.join()
    t3.join()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass