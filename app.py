#!/usr/bin/env python3
import os
import sys
import shlex
import subprocess
import threading
import yaml
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# Diccionario global para almacenar el estado y la información de cada herramienta.
scan_status = {}

def run_tool(tool_name, command, output_file):
    """
    Ejecuta el comando de una herramienta, guarda su salida en 'output_file' y
    actualiza el estado en el diccionario global 'scan_status'.
    """
    try:
        scan_status[tool_name]['status'] = 'running'
        with open(output_file, "w") as f:
            process = subprocess.Popen(
                shlex.split(command),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            for line in process.stdout:
                f.write(line)
        returncode = process.wait()
        if returncode != 0:
            scan_status[tool_name]['status'] = 'error'
            scan_status[tool_name]['error'] = f"El comando retornó el código {returncode}"
        else:
            scan_status[tool_name]['status'] = 'completed'
    except Exception as e:
        scan_status[tool_name]['status'] = 'error'
        scan_status[tool_name]['error'] = str(e)
    print(f"[+] {tool_name} finalizado con estado: {scan_status[tool_name]['status']}")

def start_scans(config):
    """
    Lee la configuración, expande la ruta de salida, crea el directorio correspondiente
    (por ejemplo, en el directorio home, en una carpeta con el nombre o IP del objetivo)
    y lanza en paralelo las herramientas definidas.
    """
    target = config.get("target")
    # Expande la ruta del directorio de salida (por ejemplo, ~/resultados_{target})
    output_dir = os.path.expanduser(config.get("output_dir", f"~/resultados_{target}"))
    os.makedirs(output_dir, exist_ok=True)

    tools = config.get("tools", {})
    executor = ThreadPoolExecutor(max_workers=5)
    futures = []
    for tool_name, tool_data in tools.items():
        command = tool_data.get("command", "")
        options = tool_data.get("options", "")
        # Reemplaza {target} en las opciones por el valor real del objetivo
        formatted_options = options.format(target=target)
        full_command = f"{command} {formatted_options}"
        # Define el archivo de salida para esta herramienta dentro de output_dir
        output_file = os.path.join(output_dir, f"{tool_name}.txt")
        # Inicializa el estado de la herramienta
        scan_status[tool_name] = {
            'status': 'pending',
            'command': full_command,
            'output_file': output_file,
            'error': ''
        }
        futures.append(executor.submit(run_tool, tool_name, full_command, output_file))
    # No se espera a que todas las tareas finalicen para permitir que la interfaz web se actualice.

def load_config(config_file):
    """
    Carga la configuración desde un archivo YAML.
    """
    with open(config_file, "r") as f:
        return yaml.safe_load(f)

# Rutas de la aplicación Flask

@app.route('/')
def index():
    return render_template('index.html', scan_status=scan_status)

@app.route('/progress')
def progress():
    return jsonify(scan_status)

@app.route('/results/<tool_name>')
def results(tool_name):
    """
    Devuelve el contenido del archivo de salida de la herramienta especificada.
    """
    if tool_name in scan_status:
        output_file = scan_status[tool_name]['output_file']
        if os.path.exists(output_file):
            with open(output_file, "r") as f:
                content = f.read()
            return f"<h2>Resultados de {tool_name}</h2><pre>{content}</pre>"
        else:
            return f"No se encontró el archivo de salida para {tool_name}", 404
    else:
        return "Herramienta no encontrada", 404

if __name__ == '__main__':
    # Permite pasar el archivo de configuración como argumento (por defecto es "config.yaml")
    config_file = "config.yaml"
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    config = load_config(config_file)
    
    # Inicia los escaneos en un hilo separado para no bloquear la interfaz web.
    scan_thread = threading.Thread(target=start_scans, args=(config,))
    scan_thread.start()

    # Inicia la aplicación Flask.
    app.run(debug=True, host='0.0.0.0', port=5000)
