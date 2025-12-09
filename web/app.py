from flask import Flask, render_template, jsonify
import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("dashboard.html") 

# API para la página
@app.route("/api/datos")
def api_datos():
    try:
        # Trae los últimos 20 registros
        res = (
            supabase
            .table("sensores_luz")
            .select("*")
            .order("id", desc=True)
            .limit(20)
            .execute()
        )

        datos = res.data

        datos_limpios = []
        for d in datos:

            # LIMPIAR Y FORMATEAR FECHA
            raw_fecha = d.get("fecha_hora") or d.get("created_at")

            if raw_fecha:
                try:
                    # Convertir ISO 8601 → datetime
                    dt = datetime.fromisoformat(raw_fecha.replace("Z", "+00:00"))
                    fecha_formateada = dt.strftime("%d/%m/%Y %I:%M:%S %p")
                except:
                    fecha_formateada = raw_fecha
            else:
                fecha_formateada = "—"

            datos_limpios.append({
                "fecha": fecha_formateada,
                "accion": d.get("accion", "—"),
                "prediccion": d.get("prediccion", "—"),
                "sensor_izq": d.get("valor_l", "—"),
                "sensor_der": d.get("valor_r", "—"),
            })

        return jsonify(datos_limpios)

    except Exception as e:
        print("ERROR:", e)
        return jsonify([])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
