import tkinter as tk
import requests
from config import MOTOR_URL

motor_session = requests.Session()

#thrust = 0-255 forward
#yaw = +-1, neg = left pos = right
#vert = +-255 pos = up
motor_state = {
    "thrust": 0,
    "yaw": 0.0,
    "vertical": 0,
}

def compute_motor_values():
    thrust = motor_state["thrust"]
    yaw = motor_state["yaw"]
    vertical = motor_state["vertical"]

    #yaw pos -> reduce left yaw neg -> reduce right
    left = int(thrust * (1.0 - max(0,yaw)))
    left = int(thrust * (1.0 - max(0,-yaw)))

    left = max(0, min(255, left))
    right = max(0, min(255, right))
    vertical = max(-255, min(255, vertical))

    return left, right, vertical
def send_motor_command():
    left, right, vertical = compute_motor_values()

    try:
        motor_session.get(
            f"{MOTOR_URL}?m1={left}&m2={right}&m3={vertical}",
            timeout=(1, 2),
        )
    except Exception as e:
        print("Motor error:", e)
