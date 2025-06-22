from flask import Flask, render_template, request, redirect, send_file, session
import pandas as pd
import os
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = "clave-secreta-supersegura"
ACCESS_CODE = "mv2025"

PRODUCTOS_PATH = "Productos Planta Balanceados.xlsx"
MOVIMIENTOS_PATH = "movimientos.xlsx"

# Cargar productos al inicio
df_productos = pd.read_excel(PRODUCTOS_PATH, usecols="A:D")
df_productos.rename(columns={"KOPR": "Código", "NOKOPR": "Producto", "STOCK INICIAL": "Stock Inicial"}, inplace=True)
df_productos["Código"] = df_productos["Código"].astype(str).str.strip().str.upper()
codigos_validos = df_productos["Código"].tolist()

@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        code = request.form.get("code")
        if code == ACCESS_CODE:
            session["auth"] = True
            return redirect("/home")
        else:
            return render_template("login.html", error="Código incorrecto.")
    return render_template("login.html")

@app.route('/home', methods=["GET", "POST"])
def index():
    if not session.get("auth"):
        return redirect("/")
    mensaje = ""
    if request.method == "POST":
        codigo_input = request.form["codigo"].strip().upper()
        tipo = request.form["tipo"]
        cantidad = int(request.form["cantidad"])

        if codigo_input not in codigos_validos:
            mensaje = f"❌ Código {codigo_input} no válido."
        else:
            producto = df_productos[df_productos["Código"] == codigo_input]["Producto"].values[0]
            stock_inicial = df_productos[df_productos["Código"] == codigo_input]["Stock Inicial"].values[0]

            entradas, salidas = 0, 0
            if os.path.exists(MOVIMIENTOS_PATH):
                df_mov = pd.read_excel(MOVIMIENTOS_PATH)
                entradas = df_mov[(df_mov["Código"] == codigo_input) & (df_mov["Tipo"] == "entrada")]["Cantidad"].sum()
                salidas = df_mov[(df_mov["Código"] == codigo_input) & (df_mov["Tipo"] == "salida")]["Cantidad"].sum()

            stock_actual = stock_inicial + entradas - salidas
            nuevo_stock = stock_actual + cantidad if tipo == "entrada" else stock_actual - cantidad

            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            nueva_fila = pd.DataFrame([{
                "Fecha": fecha,
                "Código": codigo_input,
                "Producto": producto,
                "Tipo": tipo,
                "Cantidad": cantidad,
                "Stock Resultante": nuevo_stock
            }])

            if os.path.exists(MOVIMIENTOS_PATH):
                df_mov = pd.read_excel(MOVIMIENTOS_PATH)
                df_mov.to_excel("reportes/historial_movimientos.xlsx", index=False)
                mensaje = f"✅ Movimiento registrado: {cantidad} {tipo} de {producto}"
                df_mov = pd.concat([df_mov, nueva_fila], ignore_index=True)
            else:
                df_mov = nueva_fila

            df_mov.to_excel(MOVIMIENTOS_PATH, index=False)
            mensaje = f"✅ {tipo.capitalize()} registrada: {cantidad} de {producto}. Stock actual: {nuevo_stock}"

    return render_template("index.html", mensaje=mensaje)

@app.route('/stock')
def mostrar_stock():
    if not session.get("auth"):
        return redirect("/")

    df_stock = pd.read_excel(PRODUCTOS_PATH, usecols="A:C")
    df_stock.rename(columns={"KOPR": "Código", "NOKOPR": "Producto", "STOCK INICIAL": "Stock Inicial"}, inplace=True)
    df_stock["Stock Inicial"] = df_stock["Stock Inicial"].fillna(0)

    if os.path.exists(MOVIMIENTOS_PATH):
        df_mov = pd.read_excel(MOVIMIENTOS_PATH)
        entradas = df_mov[df_mov["Tipo"] == "entrada"].groupby("Código")["Cantidad"].sum()
        salidas = df_mov[df_mov["Tipo"] == "salida"].groupby("Código")["Cantidad"].sum()

        df_stock = df_stock.set_index("Código")
        df_stock["Entradas"] = entradas
        df_stock["Salidas"] = salidas
        df_stock = df_stock.fillna(0)
        df_stock["Stock Total"] = df_stock["Stock Inicial"] + df_stock["Entradas"] - df_stock["Salidas"]
        df_stock = df_stock.reset_index()
    else:
        df_stock["Entradas"] = 0
        df_stock["Salidas"] = 0
        df_stock["Stock Total"] = df_stock["Stock Inicial"]

    df_stock.to_excel("reportes/stock_actualizado.xlsx", index=False)
    tabla_html = df_stock.to_html(index=False)
    return render_template("stock.html", tabla=tabla_html)

@app.route('/descargar_stock')
def descargar_stock():
    if not session.get("auth"):
        return redirect("/")
    return send_file("stock_actualizado.xlsx", as_attachment=True)
@app.route('/descargar_historial')
def descargar_historial():
    if not session.get("auth"):
        return redirect("/")
    return send_file("reportes/historial_movimientos.xlsx", as_attachment=True)    

    historial_path = "reportes/historial_movimientos.xlsx"

    if os.path.exists(historial_path):
        return send_file(historial_path, as_attachment=True)
    else:
        return "⚠️ El archivo de historial no está disponible.", 404


if __name__ == '__main__':
    print("🚀 Servidor Monte Verde G.F en http://0.0.0.0:10000")
    app.run(host="0.0.0.0", port=10001, debug=True)

