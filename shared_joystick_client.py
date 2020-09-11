import pygame
import socket
import time

from control_state import ControlState


class SharedJoystick(object):

    def __init__(self):
        self.devices = list()

        self.steer_device = None
        self.steer_axis = None
        self.steer_center_value = 0
        self.full_left_steer_value = 0
        self.full_right_steer_value = 0

        self.throttle_device = None
        self.throttle_axis = None
        self.throttle_0_value = 0
        self.throttle_full_value = 0

        self.brake_device = None
        self.brake_axis = None
        self.brake_0_value = 0
        self.brake_full_value = 0

        self.control_state = ControlState()

        self.udp_destination_ip = input("Enter IPv4 address of server: ")
        self.udp_port = 42069
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        pygame.init()
        self.get_devices()
        pygame.event.pump()

    def get_button_down_async(self):
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                return True
        return False

    def wait_button_press_release(self):
        # TODO this would get a button press for one button and release for another. Is that a problem?
        event_type = None
        while event_type != pygame.JOYBUTTONDOWN:
            event_type = pygame.event.wait().type
        while event_type != pygame.JOYBUTTONUP:
            event_type = pygame.event.wait().type

    def get_devices(self):
        device_count = pygame.joystick.get_count()
        for i in range(device_count):
            self.devices.append(pygame.joystick.Joystick(i))
            self.devices[i].init()

    def _calibration_loop(self):
        # TODO can device be used as a dictionary key?
        axis_start = {device: [0]*device.get_numaxes() for device in self.devices}
        min_axis_pos = {device: [1]*device.get_numaxes() for device in self.devices}
        max_axis_pos = {device: [-1]*device.get_numaxes() for device in self.devices}
        pygame.event.pump()
        for device in self.devices:
            for axis in range(device.get_numaxes()):
                axis_start[device][axis] = device.get_axis(axis)
        press = False
        release = False
        button_pressed = None
        while not (press and release):
            pygame.event.pump()
            for device in self.devices:
                for axis in range(device.get_numaxes()):
                    axis_pos = device.get_axis(axis)
                    if axis_pos < min_axis_pos[device][axis]:
                        min_axis_pos[device][axis] = axis_pos
                    if axis_pos > max_axis_pos[device][axis]:
                        max_axis_pos[device][axis] = axis_pos
            # TODO this would get a button press for one button and release for another. Is that a problem?
            if not press and any(event.type == pygame.JOYBUTTONDOWN for event in pygame.event.get()):
                press = True
            if press and any(event.type == pygame.JOYBUTTONUP for event in pygame.event.get()):
                release = True
        return axis_start, min_axis_pos, max_axis_pos

    def get_axis_with_max_diff(self, min_axis_pos, max_axis_pos):
        max_axis_diff = 0.0
        # TODO error handling for case where all axis diffs are 0.0
        for device in self.devices:
            axis_diffs = [abs(max_axis_pos[device][axis] - min_axis_pos[device][axis]) for axis in range(device.get_numaxes())]
            if max(axis_diffs) > max_axis_diff:
                detected_device = device
                detected_axis = axis_diffs.index(max(axis_diffs))
                max_axis_diff = max(axis_diffs)
        return detected_device, detected_axis

    def _calibrate_bidirectional_axis(self, message_center, message_direction_1, message_direction_2):
        # TODO it isn't great that all these messages rely on the calling function to specify pressing enter or a button
        # TODO the inconsistency between pressing enter and a button isn't great either
        print(message_center)
        self.wait_button_press_release()
        print(message_direction_1)
        axis_start, min_axis_pos, max_axis_pos = self._calibration_loop()
        detected_device, detected_axis = self.get_axis_with_max_diff(min_axis_pos, max_axis_pos)
        center_value = axis_start[detected_device][detected_axis]
        if abs(max_axis_pos[detected_device][detected_axis] - axis_start[detected_device][detected_axis]) > abs(min_axis_pos[detected_device][detected_axis] - axis_start[detected_device][detected_axis]):
            # direction 1 is maximum
            full_direction_1_value = max_axis_pos[detected_device][detected_axis]
        else:
            full_direction_1_value = min_axis_pos[detected_device][detected_axis]
        print(message_direction_2)
        axis_start, min_axis_pos, max_axis_pos = self._calibration_loop()
        # TODO naming
        device, axis = self.get_axis_with_max_diff(min_axis_pos, max_axis_pos)
        if (device, axis) != (detected_device, detected_axis):
            # TODO raise exception
            print("It seems you've selected a different axis.")
        # TODO some error checking is needed here, to make sure right and left aren't the same direction
        if abs(max_axis_pos[device][axis] - axis_start[device][axis]) > abs(min_axis_pos[device][axis] - axis_start[device][axis]):
            full_direction_2_value = max_axis_pos[device][axis]
        else:
            full_direction_2_value = min_axis_pos[device][axis]
        return device, axis, center_value, full_direction_1_value, full_direction_2_value

    def _calibrate_unidirectional_axis(self, message_0, message_full):
        print(message_0)
        self.wait_button_press_release()
        print(message_full)
        axis_start, min_axis_pos, max_axis_pos = self._calibration_loop()
        device, axis = self.get_axis_with_max_diff(min_axis_pos, max_axis_pos)
        value_0 = axis_start[device][axis]
        if abs(max_axis_pos[device][axis] - axis_start[device][axis]) > abs(min_axis_pos[device][axis] - axis_start[device][axis]):
            # full travel is maximum
            value_full = max_axis_pos[device][axis]
        else:
            value_full = min_axis_pos[device][axis]
        return device, axis, value_0, value_full

    def calibrate_steer_axis(self):
        self.steer_device, self.steer_axis, self.steer_center_value, self.full_left_steer_value, self.full_right_steer_value = self._calibrate_bidirectional_axis(
            "Center the wheel then press a button.",
            "Turn the wheel fully left, then return to center, then press a button.",
            "Turn the wheel fully right, then return to center, then press a button.",
        )
        self.full_left_center_offset = self.full_left_steer_value - self.steer_center_value
        self.full_right_center_offset = self.full_right_steer_value - self.steer_center_value
    
    def calibrate_throttle_axis(self):
        self.throttle_device, self.throttle_axis, self.throttle_0_value, self.throttle_full_value = self._calibrate_unidirectional_axis(
            "Release the throttle then press a button.",
            "Press the throttle then press a button.",
        )

    def calibrate_brake_axis(self):
        self.brake_device, self.brake_axis, self.brake_0_value, self.brake_full_value = self._calibrate_unidirectional_axis(
            "Release the brake then press a button.",
            "Press the brake then press a button.",
        )

    def calibrate_axes(self):
        self.calibrate_steer_axis()
        self.calibrate_throttle_axis()
        self.calibrate_brake_axis()

    # return the distance along min-max represented by val, scaled to [0,1]
    def get_proportional_value(self, min, max, val):
        return (val - min) / (max - min)

    # return steering position scaled to [-1,1] with negative values meaning left and positive right
    def get_calibrated_steer_position(self):
        raw_position = self.steer_device.get_axis(self.steer_axis)
        # TODO there has to be a better way to see whether two numbers are the same side of 0
        if raw_position > self.steer_center_value and self.full_left_steer_value > self.steer_center_value or raw_position < self.steer_center_value and self.full_left_steer_value < self.steer_center_value:
            # input is left
            return -self.get_proportional_value(self.steer_center_value, self.full_left_steer_value, raw_position)
        else:
            # input is right
            return self.get_proportional_value(self.steer_center_value, self.full_right_steer_value, raw_position)

    def get_calibrated_throttle_position(self):
        return self.get_proportional_value(self.throttle_0_value, self.throttle_full_value, self.throttle_device.get_axis(self.throttle_axis))

    def get_calibrated_brake_position(self):
        return self.get_proportional_value(self.brake_0_value, self.brake_full_value, self.brake_device.get_axis(self.brake_axis))

    def run(self):
        self.calibrate_axes()
        print("Steer axis is {}:{} range {} - {} - {}".format(self.steer_device.get_name(), self.steer_axis, self.full_left_steer_value, self.steer_center_value, self.full_right_steer_value))
        print("Throttle axis is {}:{} range {} - {}".format(self.throttle_device.get_name(), self.throttle_axis, self.throttle_0_value, self.throttle_full_value))
        print("Brake axis is {}:{} range {} - {}".format(self.brake_device.get_name(), self.brake_axis, self.brake_0_value, self.brake_full_value))

        loop_count = 0
        start = time.time()

        while True:
            pygame.event.pump()
            self.control_state.steer_from_float(self.get_calibrated_steer_position())
            self.control_state.throttle_from_float(self.get_calibrated_throttle_position())
            self.control_state.brake_from_float(self.get_calibrated_brake_position())
            self.sock.sendto(bytes(self.control_state), (self.udp_destination_ip, self.udp_port))


if __name__ == "__main__":
    SharedJoystick().run()
    