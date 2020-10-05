

class ControlState(object):
    STEER_FULL_LEFT = 0
    STEER_CENTER = 32768
    STEER_FULL_RIGHT = 65535
    THROTTLE_IDLE = 0
    THROTTLE_OPEN = 65535
    BRAKE_MIN = 0
    BRAKE_MAX = 65535
    
    def __init__(self):
        self._steer_value = self.STEER_CENTER
        self._throttle_value = self.THROTTLE_IDLE
        self._brake_value = self.BRAKE_MIN

    @property
    def steer_value(self):
        return self._steer_value

    @steer_value.setter
    def steer_value(self, steer_value):
        if steer_value > 0xffff:
            steer_value = 0xffff
        if steer_value < 0x0000:
            steer_value = 0x0000
        self._steer_value = steer_value

    @property
    def throttle_value(self):
        return self._throttle_value

    @throttle_value.setter
    def throttle_value(self, throttle_value):
        if throttle_value > 0xffff:
            throttle_value = 0xffff
        if throttle_value < 0x0000:
            throttle_value = 0x0000
        self._throttle_value = throttle_value

    @property
    def brake_value(self):
        return self._brake_value
    
    @brake_value.setter
    def brake_value(self, brake_value):
        if brake_value > 0xffff:
            brake_value = 0xffff
        if brake_value < 0x0000:
            brake_value = 0x0000
        self._brake_value = brake_value


    def __str__(self):
        string = "S{:0>4x}T{:0>4x}B{:0>4x}".format(self.steer_value, self.throttle_value, self.brake_value)
        if len(string) != 15:
            raise ValueError("String length is incorrect. '{}'".format(string))
        return string

    def __bytes__(self):
        # TODO would be nice to make this S{int}T{int}B{int} but I'm having trouble figuring out just how to do that and the performance hit from making each message 6 bytes longer will likely be minimal.
        b = str(self).encode('ascii')
        return b
    
    @classmethod
    def from_string(cls, string):
        cs = cls()
        cs.set_from_string(string)
        return cs

    def set_from_string(self, string):
        while string:
            sub = string[:5]
            if len(sub) != 5:
                raise ValueError("String formatted incorrectly")
            if sub[0] == 'S':
                self.steer_value = int(sub[1:], 16)
            elif sub[0] == 'T':
                self.throttle_value = int(sub[1:], 16)
            elif sub[0] == 'B':
                self.brake_value = int(sub[1:], 16)
            string = string[5:]

    # TODO make this generic
    def steer_from_float(self, steer_float):
        self.steer_value = int(steer_float * 32767 + 32767)

    def throttle_from_float(self, throttle_float):
        self.throttle_value = int(throttle_float * 65535)

    def brake_from_float(self, brake_float):
        self.brake_value = int(brake_float * 65535)