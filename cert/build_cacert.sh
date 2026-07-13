#!/usr/bin/env bash
# Gera o Cacert (trustStore JKS, senha changeit) para Produção e Produção Restrita.
# Requer: keytool (JDK), openssl, curl

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"
OUTPUT="$SCRIPT_DIR/Cacert"
STOREPASS="changeit"
STORETYPE="JKS"

mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

download_if_missing() {
  local file="$1"
  local url="$2"
  if [[ -s "$file" ]]; then
    echo "    Reutilizando $file"
  else
    curl -fsSL -o "$file" "$url"
  fi
}

echo "==> 1/5 Baixando GlobalSign Root R46 (cadeia SERPRO)"
download_if_missing globalsign-root-r46.crt \
  "https://secure.globalsign.com/cacert/rootr46.crt"

echo "==> 2/5 Baixando certificados Sectigo (cadeia futura do eSocial)"
# Fonte oficial: https://www.gov.br/esocial/pt-br/noticias/atualizacao-de-certificado-do-esocial-para-um-novo-padrao-de-seguranca
download_if_missing sectigo-root-r4.crt "https://crt.sh/?d=4256644734"
download_if_missing sectigo-ca-ov-r36.crt "https://crt.sh/?d=4267304698"

echo "==> 3/5 Obtendo ACs intermediárias e ICP-Brasil"
# AC SERPRO AR46: extraída de um servidor eSocial (mesma cadeia GlobalSign/Sectigo)
if [[ -s serpro-ar46-ov-tls-ca-2025.crt ]]; then
  echo "    Reutilizando serpro-ar46-ov-tls-ca-2025.crt"
else
  echo | openssl s_client \
    -connect webservices.producaorestrita.esocial.gov.br:443 \
    -tls1_2 -showcerts 2>/dev/null \
    | awk 'BEGIN{n=0} /BEGIN CERTIFICATE/{n++} n==2,/END CERTIFICATE/{print}' \
    > serpro-ar46-ov-tls-ca-2025.crt
fi

ICP_ZIP="icp-brasil-ac.zip"
ICP_URL="https://acraiz.icpbrasil.gov.br/credenciadas/CertificadosAC-ICP-Brasil/ACcompactado.zip"
if [[ -s icp-brasil-v10.crt && -s serpro-sslv1-v10.crt ]]; then
  echo "    Reutilizando icp-brasil-v10.crt e serpro-sslv1-v10.crt"
else
  if [[ ! -s "$ICP_ZIP" ]]; then
    curl -fsSL -o "$ICP_ZIP" "$ICP_URL" \
      || curl -kfsSL -o "$ICP_ZIP" "$ICP_URL"
  fi
  unzip -p "$ICP_ZIP" ICP-Brasilv10.crt > icp-brasil-v10.crt
  unzip -p "$ICP_ZIP" AC-SERPRO-SSLv1-v10.crt > serpro-sslv1-v10.crt
fi

echo "==> 4/5 Montando Cacert (trustStore JKS, senha $STOREPASS)"
if [[ -f "$OUTPUT" ]]; then
  cp -a "$OUTPUT" "$SCRIPT_DIR/Cacert.prev"
elif [[ -f "$SCRIPT_DIR/Cacert.bak" ]]; then
  cp -a "$SCRIPT_DIR/Cacert.bak" "$OUTPUT"
else
  JAVA_CACERTS=""
  if [[ -n "${JAVA_HOME:-}" && -f "${JAVA_HOME}/lib/security/cacerts" ]]; then
    JAVA_CACERTS="${JAVA_HOME}/lib/security/cacerts"
  elif command -v java >/dev/null 2>&1; then
    JAVA_HOME="$(java -XshowSettings:properties -version 2>&1 | awk -F'= ' '/java.home/{print $2; exit}')"
    if [[ -f "${JAVA_HOME}/lib/security/cacerts" ]]; then
      JAVA_CACERTS="${JAVA_HOME}/lib/security/cacerts"
    fi
  fi

  if [[ -n "$JAVA_CACERTS" ]]; then
    echo "    Base: cacerts do JDK ($JAVA_CACERTS)"
    keytool -importkeystore \
      -srckeystore "$JAVA_CACERTS" \
      -srcstorepass "$STOREPASS" \
      -destkeystore "$OUTPUT" \
      -deststorepass "$STOREPASS" \
      -deststoretype "$STORETYPE" \
      -noprompt
  else
    echo "    Base: trustStore JKS vazio"
    keytool -genkeypair \
      -alias _bootstrap \
      -keyalg RSA \
      -keystore "$OUTPUT" \
      -storepass "$STOREPASS" \
      -storetype "$STORETYPE" \
      -dname "CN=bootstrap" \
      -keysize 2048 \
      -validity 1
    keytool -delete \
      -alias _bootstrap \
      -keystore "$OUTPUT" \
      -storepass "$STOREPASS" \
      -storetype "$STORETYPE"
  fi
fi

for cert in \
  globalsign-root-r46 \
  serpro-ar46-ov-tls-ca-2025 \
  sectigo-root-r4 \
  sectigo-ca-ov-r36 \
  icp-brasil-v10 \
  serpro-sslv1-v10
do
  keytool -delete \
    -alias "$cert" \
    -keystore "$OUTPUT" \
    -storepass "$STOREPASS" \
    -storetype "$STORETYPE" 2>/dev/null || true
  keytool -importcert \
    -alias "$cert" \
    -file "$BUILD_DIR/${cert}.crt" \
    -keystore "$OUTPUT" \
    -storepass "$STOREPASS" \
    -storetype "$STORETYPE" \
    -noprompt
done

echo "==> 5/5 Limpando cache PEM e testando"
rm -f "$OUTPUT.pem" "$OUTPUT.p12"
python3 "$(dirname "$SCRIPT_DIR")/main.py"

echo ""
echo "Cacert (JKS, senha $STOREPASS) em: $OUTPUT"
echo "Backup anterior (se existia): $SCRIPT_DIR/Cacert.prev"
