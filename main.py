"""
Teste de conectividade com os servidores do eSocial.

Forma recomendada pela documentação oficial e por integradores: estabelecer
conexão TLS 1.2 na porta 443 (equivalente a `openssl s_client -connect host:443
-CAfile icp-brasil.crt -tls1_2`). Não exige certificado digital do cliente.
"""

import os
import socket
import ssl
import subprocess
import sys

TIMEOUT = 10

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

JKS_PASSWORD = "changeit"


def jks_to_pem(jks_path: str) -> str:
    """Converte keystore JKS (ICP-Brasil) para PEM, reutilizando cache."""
    pem_path = jks_path + ".pem"
    if os.path.isfile(pem_path) and os.path.getmtime(pem_path) >= os.path.getmtime(jks_path):
        return pem_path

    base, _ = os.path.splitext(jks_path)
    p12_path = base + ".p12"

    subprocess.run(
        [
            "keytool", "-importkeystore",
            "-srckeystore", jks_path,
            "-destkeystore", p12_path,
            "-deststoretype", "PKCS12",
            "-srcstorepass", JKS_PASSWORD,
            "-deststorepass", JKS_PASSWORD,
            "-noprompt",
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "openssl", "pkcs12",
            "-in", p12_path,
            "-out", pem_path,
            "-nokeys", "-nodes",
            "-passin", f"pass:{JKS_PASSWORD}",
            "-legacy",
        ],
        check=True,
        capture_output=True,
    )
    return pem_path


def test_tls(host: str, ca_pem: str) -> tuple[bool, bool, str]:
    """
    Testa conectividade TLS 1.2 com o host.
    Retorna (handshake_ok, cert_ok, detalhe).
    """
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_verify_locations(cafile=ca_pem)

    try:
        with socket.create_connection((host, 443), timeout=TIMEOUT) as sock:
            with context.wrap_socket(sock, server_hostname=host) as tls:
                return True, True, f"TLS {tls.version()} — certificado validado"
    except ssl.SSLCertVerificationError as e:
        return True, False, f"TLS conectou, mas certificado não validado: {e.verify_message}"
    except (OSError, ssl.SSLError) as e:
        return False, False, str(e)


def test_environment(env_name: str, services: list[tuple[str, str]], ca_jks: str) -> None:
    print(f"\n--- {env_name} ---")
    ca_pem = jks_to_pem(ca_jks)

    for label, host in services:
        handshake_ok, cert_ok, detail = test_tls(host, ca_pem)

        if handshake_ok and cert_ok:
            print(f"✅ {label} ({host}): {detail}")
        elif handshake_ok:
            print(f"⚠️  {label} ({host}): servidor acessível — {detail}")
        else:
            print(f"❌ {label} ({host}): {detail}")


def main() -> int:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cert_dir = os.path.join(base_dir, "cert")

    for tool in ("keytool", "openssl"):
        if subprocess.run(["which", tool], capture_output=True).returncode != 0:
            print(f"Erro: '{tool}' não encontrado. Instale o JDK (keytool) e o OpenSSL.")
            return 1

    test_environment(
        "Produção Restrita",
        HOSTS["Produção Restrita"],
        os.path.join(cert_dir, "Cacert"),
    )
    test_environment(
        "Produção",
        HOSTS["Produção"],
        os.path.join(cert_dir, "Cacert"),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
