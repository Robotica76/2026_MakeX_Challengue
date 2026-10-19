# codes make you happy
import novapi
from mbuild.encoder_motor import encoder_motor_class

# new class
encoder_motor_M1 = encoder_motor_class("M1", "INDEX1")
encoder_motor_M2 = encoder_motor_class("M2", "INDEX1")
encoder_motor_M3 = encoder_motor_class("M3", "INDEX1")
encoder_motor_M4 = encoder_motor_class("M4", "INDEX1")

encoder_motor_M1.set_speed(10)
encoder_motor_M2.set_speed(10)
encoder_motor_M3.set_speed(10)
encoder_motor_M4.set_speed(10)
