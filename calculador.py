from flask import Flask, render_template, request, jsonify
import itertools
import math

app = Flask(__name__)

def decodificar_entrada(texto):
    texto = texto.strip().replace(" ", "").replace(",", ".")
    if not texto: raise ValueError("Entrada vacía")
    if texto.endswith(('k', 'K')): return float(texto[:-1]) * 1e3
    elif texto.endswith('M'): return float(texto[:-1]) * 1e6
    elif texto.endswith('m'): return float(texto[:-1]) * 1e-3
    elif texto.endswith(('G', 'g')): return float(texto[:-1]) * 1e9
    valor = float(texto)
    if not math.isfinite(valor) or valor <= 0: raise ValueError("El valor debe ser positivo")
    return valor

def obtener_lista_colores(valor, tol_str):
    if valor <= 0: return []
    colores = ["Negro", "Marrón", "Rojo", "Naranja", "Amarillo", "Verde", "Azul", "Violeta", "Gris", "Blanco"]
    mult_colores = {-3: "?", -2: "Plata", -1: "Oro", 0: "Negro", 1: "Marrón", 2: "Rojo", 3: "Naranja", 
                    4: "Amarillo", 5: "Verde", 6: "Azul", 7: "Violeta", 8: "Gris", 9: "Blanco"}
    valor = round(valor, 6)
    exp = int(math.floor(math.log10(valor)))
    if "1%" in tol_str:
        norm = round(valor / (10**(exp - 2)))
        mult = exp - 2
        if norm >= 1000: norm //= 10; mult += 1
        return [colores[(norm // 100) % 10], colores[(norm // 10) % 10], colores[norm % 10], mult_colores.get(mult, '?'), "Marrón"]
    else:
        norm = round(valor / (10**(exp - 1)))
        mult = exp - 1
        if norm >= 100: norm //= 10; mult += 1
        return [colores[(norm // 10) % 10], colores[norm % 10], mult_colores.get(mult, '?'), "Oro" if "5%" in tol_str else "Plata"]

def algoritmo_busqueda(target, tol_str):
    bases_10 = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]
    bases_5 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
    bases_1 = [1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24, 1.27, 1.30, 1.33, 1.37, 1.40, 1.43, 1.47, 1.50, 1.54, 1.58, 
               1.62, 1.65, 1.69, 1.74, 1.78, 1.82, 1.87, 1.91, 1.96, 2.00, 2.05, 2.10, 2.15, 2.21, 2.26, 2.32, 2.37, 2.43, 2.49, 2.55, 
               2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09, 3.16, 3.24, 3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12, 
               4.22, 4.32, 4.42, 4.53, 4.64, 4.75, 4.87, 4.99, 5.11, 5.23, 5.36, 5.49, 5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65, 
               6.81, 6.98, 7.15, 7.32, 7.50, 7.68, 7.87, 8.06, 8.25, 8.45, 8.66, 8.87, 9.09, 9.31, 9.53, 9.76]

    if "10%" in tol_str: bases, limite_tol = bases_10, 10
    elif "5%" in tol_str: bases, limite_tol = bases_5, 5
    else: bases, limite_tol = bases_1, 1

    todos_r = sorted(list({round(b * (10**i), 6) for b in bases for i in range(-2, 7)}))
    pool_amplio = [r for r in todos_r if target / 100 <= r <= target * 100]
    pool_estricto = [r for r in todos_r if target / 10 <= r <= target * 10]

    mejores = {1: (float('inf'), 0, [], ""), 2: (float('inf'), 0, [], ""), 3: (float('inf'), 0, [], "")}

    for r in pool_amplio:
        if abs(target - r) < mejores[1][0]: mejores[1] = (abs(target - r), r, [r], "1 Resistor")
    for r1, r2 in itertools.combinations_with_replacement(pool_amplio, 2):
        if abs(target - (r1 + r2)) < mejores[2][0]: mejores[2] = (abs(target - (r1 + r2)), r1 + r2, [r1, r2], "2 en Serie")
        if abs(target - ((r1 * r2)/(r1 + r2))) < mejores[2][0]: mejores[2] = (abs(target - ((r1 * r2)/(r1 + r2))), (r1 * r2)/(r1 + r2), [r1, r2], "2 en Paralelo")
    for r1, r2, r3 in itertools.combinations_with_replacement(pool_estricto, 3):
        if r1==0 or r2==0 or r3==0: continue
        if abs(target - (r1+r2+r3)) < mejores[3][0]: mejores[3] = (abs(target - (r1+r2+r3)), r1+r2+r3, [r1, r2, r3], "3 en Serie")
        if abs(target - (1/(1/r1+1/r2+1/r3))) < mejores[3][0]: mejores[3] = (abs(target - (1/(1/r1+1/r2+1/r3))), 1/(1/r1+1/r2+1/r3), [r1, r2, r3], "3 en Paralelo")
        for a, b, c in [(r2, r3, r1), (r1, r3, r2), (r1, r2, r3)]:
            if abs(target - (((a*b)/(a+b))+c)) < mejores[3][0]: mejores[3] = (abs(target - (((a*b)/(a+b))+c)), ((a*b)/(a+b))+c, [a,b,c], "Mixto (2 Paralelo + 1 Serie)")
            if abs(target - (((a+b)*c)/(a+b+c))) < mejores[3][0]: mejores[3] = (abs(target - (((a+b)*c)/(a+b+c))), ((a+b)*c)/(a+b+c), [a,b,c], "Mixto (2 Serie || 1 Paralelo)")

    return mejores, limite_tol

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calcular', methods=['POST'])
def calcular():
    datos = request.json
    try:
        objetivo = decodificar_entrada(datos['resistencia'])
        mejores, limite_tol = algoritmo_busqueda(objetivo, datos['tolerancia'])
        
        hex_colors = {"Negro": "#000", "Marrón": "#8B4513", "Rojo": "#F00", "Naranja": "#FF8C00", "Amarillo": "#FF0", 
                      "Verde": "#080", "Azul": "#00F", "Violeta": "#800080", "Gris": "#888", "Blanco": "#FFF", 
                      "Oro": "#FFD700", "Plata": "#C0C0C0", "?": "#F0F"}

        resultados_json = []
        for num in [1, 2, 3]:
            diff, req, comp, tipo = mejores[num]
            error = (diff / objetivo) * 100
            comp_data = []
            for val in comp:
                colores = obtener_lista_colores(val, datos['tolerancia'])
                val_str = f"{val/1e6:g} MΩ" if val >= 1e6 else f"{val/1e3:g} kΩ" if val >= 1e3 else f"{val:g} Ω"
                comp_data.append({"val_str": val_str, "colores_hex": [hex_colors.get(c, "#000") for c in colores], "es_precision": "1%" in datos['tolerancia']})
            
            resultados_json.append({
                "tipo": tipo, "equivalente": round(req, 3), "error": round(error, 4),
                "cumple": error <= limite_tol, "componentes": comp_data
            })
            
        return jsonify({"success": True, "objetivo": objetivo, "margen": limite_tol, "resultados": resultados_json})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)