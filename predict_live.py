import time
import os
import numpy as np
import joblib
import smbus2
import RPi.GPIO as GPIO

from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime
import pytz

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
print("Conectado a Supabase correctamente.")

I2C_ADDR = 0x4B
CMD = 0x84
bus = smbus2.SMBus(1)

def leer_adc(canal):
    return bus.read_byte_data(I2C_ADDR, CMD | (canal << 4))

ENA = 18
IN1 = 17
IN2 = 27

ENB = 13
IN3 = 22
IN4 = 23

GPIO.setmode(GPIO.BCM)
GPIO.setup([ENA, IN1, IN2, ENB, IN3, IN4], GPIO.OUT)

motorA = GPIO.PWM(ENA, 1000)
motorB = GPIO.PWM(ENB, 1000)
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
    print("GIRO IZQUIERDA")
    direccion_adelante()
    motorA.ChangeDutyCycle(70)
    motorB.ChangeDutyCycle(20)

def girar_derecha():
    print("GIRO DERECHA")
    direccion_adelante()
    motorA.ChangeDutyCycle(20)
    motorB.ChangeDutyCycle(70)

#  IA
SAMPLE_RATE = 40
VENTANA_SEG = 0.05
MUESTRAS_POR_VENTANA = int(SAMPLE_RATE * VENTANA_SEG)

clasificador = joblib.load("modelo_luz.pkl")
print("Modelo IA cargado correctamente.")


ultima_accion = None

tz_panama = pytz.timezone("America/Panama")

print("Iniciando detección...")

try:
    while True:
        # === CAPTURA RÁPIDA ===
        valores_L = []
        valores_R = []

        for _ in range(MUESTRAS_POR_VENTANA):
            L = leer_adc(0)
            R = leer_adc(2)
            valores_L.append(L)
            valores_R.append(R)
            time.sleep(1.0 / SAMPLE_RATE)

        # Datos promediados
        prom_L = float(np.mean(valores_L))
        prom_R = float(np.mean(valores_R))
        desv_L = float(np.std(valores_L))
        desv_R = float(np.std(valores_R))

        X = np.array([[prom_L, desv_L, prom_R, desv_R]])
        prediccion = int(clasificador.predict(X)[0])

        L_ult = valores_L[-1]
        R_ult = valores_R[-1]

        if prediccion == 1:
            print("🔦 Luz detectada → movimiento")

            if L_ult > R_ult:
                accion = "girar_izquierda"
                girar_izquierda()
            elif R_ult > L_ult:
                accion = "girar_derecha"
                girar_derecha()
            else:
                accion = "avanzar"
                avanzar()
        
        else:
            print("🌙 No hay linterna → detener")
            accion = "detener"
            detener()

        # Convertir predicción
        pred_texto = "linterna" if prediccion == 1 else "ambiente"


        # =====================================================
        #   SOLO GUARDA EN SUPABASE SI LA ACCIÓN CAMBIA
        # =====================================================
        fecha_local = datetime.now(tz_panama).strftime("%Y-%m-%d %H:%M:%S")
        if accion != ultima_accion:
            try:
                supabase.table("sensores_luz").insert({
                    "fecha_hora": fecha_local,
                    "valor_l": prom_L,
                    "valor_r": prom_R,
                    "prediccion": pred_texto,
                    "accion": accion
                }).execute()

                print("✔ Registro guardado (acción nueva):", accion)

                # ACTUALIZA LA ACCIÓN RECORDADA
                ultima_accion = accion

            except Exception as e:
                print("ERROR enviando a Supabase:", e)

        # Si no cambia, solo sigue moviéndose sin guardar
        else:
            print("↻ Acción repetida, no se guarda en BD.")


except KeyboardInterrupt:
    print("Finalizando programa...")
    detener()
    GPIO.cleanup()
