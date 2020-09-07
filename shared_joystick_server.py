import pyvjoy
import socket
import time

from control_state import ControlState

class SharedJoystickServer(object):

    def __init__(self):
        self.device = pyvjoy.VJoyDevice(1)
        self.vjoy_steer_axis = pyvjoy.HID_USAGE_X
        self.vjoy_throttle_axis = pyvjoy.HID_USAGE_Y
        self.vjoy_brake_axis = pyvjoy.HID_USAGE_Z

        self.control_state = ControlState()
        self.update_controls()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # TODO I can find this programatically, can I not?
        ip = input("Enter this computer's IP address: ")
        if not ip:
            ip = "192.168.50.69"
        self.sock.bind((ip, 42069))

    def update_controls(self):
        self.device.set_axis(self.vjoy_steer_axis, self.control_state.steer_value)
        self.device.set_axis(self.vjoy_throttle_axis, self.control_state.throttle_value)
        self.device.set_axis(self.vjoy_brake_axis, self.control_state.brake_value)

    def calibrate(self):
        print("Open iRacing steering calibration then press Enter.")
        input()
        self.control_state.steer_value = self.control_state.STEER_CENTER
        self.update_controls()
        time.sleep(0.1)
        self.control_state.steer_value = self.control_state.STEER_FULL_LEFT
        self.update_controls()
        time.sleep(0.1)
        self.control_state.steer_value = self.control_state.STEER_FULL_RIGHT
        self.update_controls()
        time.sleep(0.1)
        self.control_state.steer_value = self.control_state.STEER_CENTER
        self.update_controls()
        print("Close iRacing steering calibration, open pedal calibration, and press Enter.")
        input()
        self.control_state.throttle_value = self.control_state.THROTTLE_IDLE
        self.update_controls()
        time.sleep(0.1)
        self.control_state.throttle_value = self.control_state.THROTTLE_OPEN
        self.update_controls()
        time.sleep(0.1)
        self.control_state.throttle_value = self.control_state.THROTTLE_IDLE
        self.update_controls()
        print("Advance to brake calibration and press Enter.")
        input()
        self.control_state.brake_value = self.control_state.BRAKE_MIN
        self.update_controls()
        time.sleep(0.1)
        self.control_state.brake_value = self.control_state.BRAKE_MAX
        self.update_controls()
        time.sleep(0.1)
        self.control_state.brake_value = self.control_state.BRAKE_MIN
        self.update_controls()
        print("Select auto clutch, close calibration window, and use auto shift and press Enter.")
        input()

    def get_inputs(self):
        start = time.time()
        inputs = list()
        num = 0
        while time.time() - start < 0.01:
            data, addr = self.sock.recvfrom(16)
            data = data.decode('ascii')
            try:
                inputs.append(ControlState.from_string(data))
            except ValueError:
                pass
            num += 1
        print(num)
        if inputs:
            self.control_state.steer_value = sum(cs.steer_value for cs in inputs) // len(inputs)
            self.control_state.throttle_value = sum(cs.throttle_value for cs in inputs) // len(inputs)
            self.control_state.brake_value = sum(cs.brake_value for cs in inputs) // len(inputs)

    def run(self):
        self.calibrate()

        while True:
            self.get_inputs()
            self.update_controls()


if __name__ == "__main__":
    SharedJoystickServer().run()