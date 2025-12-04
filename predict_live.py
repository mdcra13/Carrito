import time
import numpy as np
import joblib
import smbus2
import RPi.GPIO as GPIO

# ----------------------------------
#  CONFIGURACIÓN DEL ADC
# ----------------------------------
I2C_ADDR = 0x4B
CMD = 0x84
bus = smbus2.SMBus(1)

def leer_adc(canal):
    return bus.read_byte_data(I2C_ADDR, CMD | (canal << 4))


# ----------------------------------
#  CONFIGURACIÓN MOTORES (PWM)
# ----------------------------------
ENA = 18     # Motor DERECHO
IN1 = 17
IN2 = 27

ENB = 13     # Motor IZQUIERDO
IN3 = 22
IN4 = 23

GPIO.setmode(GPIO.BCM)
GPIO.setup([ENA, IN1, IN2, ENB, IN3, IN4], GPIO.OUT)

motorA = GPIO.PWM(ENA, 1000)  # DERECHO
motorB = GPIO.PWM(ENB, 1000)  # IZQUIERDO
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

def girar_izquierda():
    print("LUZ IZQUIERDA → GIRAR HACIA LUZ")
    direccion_adelante()
    motorA.ChangeDutyCycle(70)   # derecho rápido
    motorB.ChangeDutyCycle(20)   # izquierdo lento

def girar_derecha():
    print("LUZ DERECHA → GIRAR HACIA LUZ")
    direccion_adelante()
    motorA.ChangeDutyCycle(20)   # derecho lento
    motorB.ChangeDutyCycle(70)   # izquierdo rápido


# ----------------------------------
#  CONFIGURACIÓN IA
# ----------------------------------
SAMPLE_RATE = 40
VENTANA_SEG = 0.05
MUESTRAS_POR_VENTANA = int(SAMPLE_RATE * VENTANA_SEG)

clasificador = joblib.load("modelo_luz.pkl")
print("Modelo cargado correctamente.")


# ----------------------------------
#  LOOP PRINCIPAL (IA + MOVIMIENTO)
# ----------------------------------
print("Iniciando detección...")

try:
    while True:
        valores_L = []
        valores_R = []

        for _ in range(MUESTRAS_POR_VENTANA):
            L = leer_adc(0)
            R = leer_adc(2)
            valores_L.append(L)
            valores_R.append(R)
            time.sleep(1.0 / SAMPLE_RATE)

        # ----- Características -----
        caracteristicas = [
            np.mean(valores_L), np.std(valores_L),
            np.mean(valores_R), np.std(valores_R)
        ]

        X = np.array([caracteristicas])
        prediccion = clasificador.predict(X)[0]

        # ================================
        #   1 = LINTERN A   —   0 = AMBIENTE
        # ================================
        if prediccion == 1:
            print("🔦 LINTERN A — ¡Mover hacia la luz!")

            # Movimiento usando L y R del ÚLTIMO segundo
            L_ult = valores_L[-1]
            R_ult = valores_R[-1]

            if L_ult > R_ult:
                girar_izquierda()
            elif R_ult > L_ult:
                girar_derecha()
            else:
                avanzar()

        else:
            print("🌙 AMBIENTE — Deteniendo carro")
            detener()

except KeyboardInterrupt:
    print("Finalizando...")
    detener()
    GPIO.cleanup()
