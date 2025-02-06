
# Multi-Tool CTF Automation Wrapper

Este es un *wrapper* en Python para automatizar herramientas de reconocimiento y enumeración en **CTFs** y pruebas de seguridad.

## Características
- Ejecución paralela con `ThreadPoolExecutor`
- Interfaz web con Flask
- Integración con herramientas como Nmap, Nikto, Gobuster, SQLmap, etc.
- Configuración mediante `config.yaml`

## Instalación
```bash
git clone https://github.com/tomasbacigalupo-tintin/automation-wrapper.git
cd automation-wrapper
pip install flask pyyaml
