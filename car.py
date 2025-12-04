import time
import smbus2
import RPi.GPIO as GPIO

# ADC ADS7830
I2C_ADDR = 0x4B
bus = smbus2.SMBus(1)
CMD = 0x84

def read_adc(ch):
    return bus.read_byte_data(I2C_ADDR, CMD | (ch << 4))

ENA = 18
IN1 = 17
IN2 = 27

ENB = 13
IN3 = 22
IN4 = 23

GPIO.setmode(GPIO.BCM)
GPIO.setup([ENA, IN1, IN2, ENB, IN3, IN4], GPIO.OUT)

motorA = GPIO.PWM(ENA, 1000)  # Motor DERECHO
motorB = GPIO.PWM(ENB, 1000)  # Motor IZQUIERDO
motorA.start(0)
motorB.start(0)

def detener():
    motorA.ChangeDutyCycle(0)
    motorB.ChangeDutyCycle(0)
    GPIO.output(IN1,0); GPIO.output(IN2,0)
    GPIO.output(IN3,0); GPIO.output(IN4,0)

def direccion_adelante():
    GPIO.output(IN1,0); GPIO.output(IN2,1)
    GPIO.output(IN3,0); GPIO.output(IN4,1)

def avanzar():
    print("ADELANTE")
    direccion_adelante()
    motorA.ChangeDutyCycle(60)
    motorB.ChangeDutyCycle(60)

def girar_hacia_luz_izquierda():
    print("LUZ IZQUIERDA → GIRAR HACIA LA LUZ")
    direccion_adelante()
    motorA.ChangeDutyCycle(70)   # derecho rápido
    motorB.ChangeDutyCycle(20)   # izquierdo lento

def girar_hacia_luz_derecha():
    print("LUZ DERECHA → GIRAR HACIA LA LUZ")
    direccion_adelante()
    motorA.ChangeDutyCycle(20)   # derecho lento
    motorB.ChangeDutyCycle(70)   # izquierdo rápido


UMBRAL = 140

try:
    while True:
        L = read_adc(0)   # sensor IZQUIERDO
        R = read_adc(2)   # sensor DERECHO

        print(f"L:{L}   R:{R}")

        if max(L, R) < UMBRAL:
            print("POCA LUZ → STOP")
            detener()

        elif L > R:
            girar_hacia_luz_izquierda()

        elif R > L:
            girar_hacia_luz_derecha()

        else:
            avanzar()

        time.sleep(0.1)

except KeyboardInterrupt:
    detener()
    GPIO.cleanup()

