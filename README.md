# Projeto de Monitoramento de Preços de Criptomoedas

Este projeto visa monitorar os preços de criptomoedas, como o Bitcoin, e enviar alertas de compra e venda em um grupo no Telegram. A integração é feita utilizando a API da Binance para obter informações de mercado e o Telegram para enviar notificações.

## Configuração

Antes de começar, é necessário configurar as seguintes variáveis de ambiente:

- `API_KEY_BINANCE`: Sua chave de API da Binance.
- `SECRET_KEY_BINANCE`: Sua chave secreta de API da Binance.
- `BOT_ID_TELEGRAM`: ID do seu bot no Telegram.
- `GROUP_ID_TELEGRAM`: ID do grupo no Telegram para receber os alertas.

Certifique-se de obter suas chaves de API da Binance e configurar um bot no Telegram para obter as informações necessárias.

## Instalação

1. Clone este repositório:

```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```

2. Configure o ambiente e instale as dependências:

```bash
python3 -m venv venv
pip install -r requirements.txt
```

3. Execute o código:

```bash
python3 main.py
```

## Aviso

Este projeto lida com informações financeiras. Use-o por sua conta e risco. Não nos responsabilizamos por decisões de investimento com base nas informações fornecidas por este projeto.