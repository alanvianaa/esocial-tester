"""
Monitor de conectividade contínuo com os servidores do eSocial.
"""

import os
import socket
import ssl
import sys
import time
from collections import deque

# --- Configurações ---
CHECK_INTERVAL_SECONDS = 3
HISTORY_SIZE = 60
TIMEOUT = 10
CERT_PEM_FILENAME = "Cacert.pem"
# ---------------------

# Hosts oficiais (Manual de Orientação do Desenvolvedor)
HOSTS = {
    "Produção Restrita": [
        ("Envio/Consulta", "webservices.producaorestrita.esocial.gov.br"),
    ],
    "Produção": [
        ("Envio", "webservices.envio.esocial.gov.br"),
        ("Consulta", "webservices.consulta.esocial.gov.br"),
    ],
}

STATUS_MAP = {
    "OK":   {"bar": "█", "text": "Online"},
    "WARN": {"bar": "▒", "text": "Aviso Cert."},
    "FAIL": {"bar": "░", "text": "Offline"},
}


def test_tls(host: str, ca_pem: str) -> str:
    """Testa a conectividade TLS com um host e retorna o status ('OK', 'WARN', 'FAIL')."""
    context = ssl.create_default_context(cafile=ca_pem)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    
    try:
        with socket.create_connection((host, 443), timeout=TIMEOUT) as sock:
            with context.wrap_socket(sock, server_hostname=host):
                return "OK"
    except ssl.SSLCertVerificationError:
        return "WARN"
    except (OSError, ssl.SSLError):
        return "FAIL"


def generate_status_display(history: dict) -> str:
    col_widths = {"service": 45, "status": 15, "history": HISTORY_SIZE}
    
    top_border = f"┌{'─' * col_widths['service']}┬{'─' * col_widths['status']}┬{'─' * col_widths['history']}┐"
    header_sep = f"├{'─' * col_widths['service']}┼{'─' * col_widths['status']}┼{'─' * col_widths['history']}┤"
    bottom_border = f"└{'─' * col_widths['service']}┴{'─' * col_widths['status']}┴{'─' * col_widths['history']}┘"

    lines = []
    update_time = time.strftime('%d/%m/%Y %X')
    
    title = f"Status dos Serviços eSocial (Último update: {update_time})"
    lines.append(title)
    
    lines.append(top_border)
    header = (f"│{'Serviço':<{col_widths['service']}}"
              f"│{'Status Atual':^{col_widths['status']}}"
              f"│{'Histórico Recente':<{col_widths['history']}}│")
    lines.append(header)
    lines.append(header_sep)

    for env, services in HOSTS.items():
        for label, host in services:
            service_history = history.get(host, deque())
            
            if not service_history:
                status_text = "Verificando..."
                history_bar = ""
            else:
                last_status = service_history[-1]
                status_text = STATUS_MAP[last_status]["text"]
                history_bar = "".join(STATUS_MAP[s]["bar"] for s in service_history)
            
            service_name = f"{env} - {label}"
            padding = " " * (col_widths['history'] - len(history_bar))
            
            row = (f"│{service_name:<{col_widths['service']}}"
                   f"│{status_text:^{col_widths['status']}}"
                   f"│{history_bar + padding}│")
            lines.append(row)
            
    lines.append(bottom_border)
    return "\n".join(lines)


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def hide_cursor():
    sys.stdout.write("\x1b[?25l")
    sys.stdout.flush()

def run_monitor_loop(ca_pem: str):
    all_services = [host for _, services in HOSTS.items() for _, host in services]
    history = {host: deque(maxlen=HISTORY_SIZE) for host in all_services}
    hide_cursor()

    while True:
        start_time = time.time()

        for host in all_services:
            status = test_tls(host, ca_pem)
            history[host].append(status)

        clear_screen()
        display_text = generate_status_display(history)
        print(display_text)

        elapsed_time = time.time() - start_time
        sleep_time = max(0, CHECK_INTERVAL_SECONDS - elapsed_time)
        time.sleep(sleep_time)


if __name__ == "__main__":
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ca_pem_path = os.path.join(base_dir, CERT_PEM_FILENAME)
        run_monitor_loop(ca_pem_path)
    except KeyboardInterrupt:
        print("\nMonitoramento interrompido.")
        sys.exit(0)
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")
        sys.exit(1)
