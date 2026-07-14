# eSocial Tester

O eSocial Tester é uma ferramenta para testar o serviço de disponibilidade do eSocial. 
Ele faz requisições para o serviço do eSocial em um intervalo de tempo configurável e exibe o status do serviço.

## Como usar

1. Clone o repositório:
```bash
git clone https://github.com/alanvianaa/esocial-tester.git
```

2. Execute o script:
```bash
python main.py
```

## Exemplo

```
┌─────────────────────────────────────────────┬───────────────┬────────────────────────────────────────────────────────────┐
│Serviço                                      │ Status Atual  │Histórico Recente (Último update: 14/07/2026 12:02:53)      │
├─────────────────────────────────────────────┼───────────────┼────────────────────────────────────────────────────────────┤
│Produção Restrita - Envio/Consulta           │    Online     │████████████████████████████████████████████████████████████│
│Produção - Envio                             │  Aviso Cert.  │████████████████████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│
│Produção - Consulta                          │    Offline    │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
└─────────────────────────────────────────────┴───────────────┴────────────────────────────────────────────────────────────┘
```

### Legenda do Histórico

*   `█` - **Online**: O serviço está operando normalmente.
*   `▒` - **Aviso Cert.**: O serviço está apresentando um erro de certificado.
*   `░` - **Offline**: O serviço está fora do ar.

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir um Pull Request.
