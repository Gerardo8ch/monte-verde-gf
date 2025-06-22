from flask import Flask, render_template, request, redirect, send_file, session
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "clave-secreta-supersegura"  # Clave para mantener la sesión activa
ACCESS_CODE = "mv2025"  # Código que los usuarios deben ingresar

PRODUCTOS_PATH = "Productos Planta Balanceados.xlsx"
MOVIMIENTOS_PATH = "movimientos.xlsx"

# Cargar productos al inicio
df_productos = pd.read_excel(PRODUCTOS_PATH, usecols="A:B")
df_productos.rename(columns={"KOPR": "Código", "NOKOPR": "Producto"}, inplace=True)
codigos_validos = df_productos["Código"].astype(str).str.strip().str.upper().tolist()

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
        codigo = request.form["codigo"].strip().upper()
        tipo = request.form["tipo"]
        cantidad = int(request.form["cantidad"])

        if codigo not in codigos_validos:
            mensaje = f"❌ Código {codigo} no válido."
        else:
            producto = df_productos[df_productos["Código"] == codigo]["Producto"].values[0]
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            nueva_fila = pd.DataFrame([{
                "Fecha": fecha,
                "Código": codigo,
                "Producto": producto,
                "Tipo": tipo,
                "Cantidad": cantidad
            }])

            if os.path.exists(MOVIMIENTOS_PATH):
                df_mov = pd.read_excel(MOVIMIENTOS_PATH)
                df_mov = pd.concat([df_mov, nueva_fila], ignore_index=True)
            else:
                df_mov = nueva_fila

            df_mov.to_excel(MOVIMIENTOS_PATH, index=False)
            mensaje = f"✅ Movimiento registrado: {cantidad} {tipo} de {producto}"

    return render_template("index.html", mensaje=mensaje)

@app.route('/stock')
def mostrar_stock():
    if not session.get("auth"):
        return redirect("/")
        
    df_stock = pd.read_excel(PRODUCTOS_PATH, usecols="A:C")
    df_stock.columns = ["Código", "Producto", "Stock Inicial"]
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

    df_stock.to_excel("stock_actualizado.xlsx", index=False)
    tabla_html = df_stock.to_html(index=False)
    return render_template("stock.html", tabla=tabla_html)

@app.route('/descargar_stock')
def descargar_stock():
    if not session.get("auth"):
        return redirect("/")
    return send_file("stock_actualizado.xlsx", as_attachment=True)

if __name__ == '__main__':
    print("🚀 Servidor Monte Verde G.F en http://0.0.0.0:10000")
    app.run(host="0.0.0.0", port=10001, debug=True)

