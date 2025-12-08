import time, csv
import smbus2

I2C_ADDR = 0x4B
CMD = 0x84
bus = smbus2.SMBus(1)

def read_adc(ch):
    return bus.read_byte_data(I2C_ADDR, CMD | (ch << 4))

SAMPLE_RATE = 40.0
WINDOW_SEC = 1.0
SAMPLES_PER_WINDOW = int(SAMPLE_RATE * WINDOW_SEC)

label = 'ambiente'

print("""
========================================
 DATA LOGGER - Raspberry Pi 3
========================================
Comandos:
  [l]  Cambiar etiqueta a LINTERNA  
  [a]  Cambiar etiqueta a AMBIENTE
  [q]  Salir

NOTA:
Mientras corre, puedes escribir l/a/q y presionar ENTER.
""")

try:
    while True:

        window = []
        start = time.time()

        while len(window) < SAMPLES_PER_WINDOW:
            L = read_adc(0)
            R = read_adc(2)
            t = time.time()
            window.append((t, L, R))
            time.sleep(1.0 / SAMPLE_RATE)

        #GUARDAR CSV
        ts = int(start)
        fname = f"data_{ts}_{label}.csv"

        with open(fname, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["t", "L", "R"])
            for rec in window:
                writer.writerow(rec)

        print(f"\nGuardada ventana: {fname}  (etiqueta: {label})")

        print("Escribe l/a/q y ENTER para cambiar etiqueta (o ENTER para continuar): ", end="")
        cmd = input().strip().lower()

        if cmd == "l":
            label = "linterna"
            print("Etiqueta cambiada a LINTERN A")
        elif cmd == "a":
            label = "ambiente"
            print("Etiqueta cambiada a AMBIENTE")
        elif cmd == "q":
            print("Saliendo...")
            break

except KeyboardInterrupt:
    print("Interrumpido por el usuario")
