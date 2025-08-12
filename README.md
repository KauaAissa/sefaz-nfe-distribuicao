# sefaz-nfe-distribuicao

Consulta de documentos fiscais eletrônicos (NF-e) via **NFeDistribuicaoDFe** da SEFAZ, utilizando certificado digital A1 no formato PEM.

---

## 📖 Visão Geral

Este projeto demonstra como integrar com o Web Service da SEFAZ para baixar documentos fiscais eletrônicos disponíveis para um **CNPJ específico**, utilizando o serviço **NFeDistribuicaoDFe**.

A aplicação:

- Consulta a SEFAZ a partir do último NSU processado
- Salva as respostas XML localmente
- Atualiza automaticamente o `ultNSU` para a próxima execução
- Utiliza **SOAP** com certificado digital A1

> **Finalidade**: estudo, prototipagem e integração com sistemas fiscais.

---

## 📂 Estrutura do Projeto

```
sefaz-nfe-distribuicao/
├─ src/
│  ├─ consultar_distribuicao.py   # Script principal
│  └─ extrair_documentos.py       # Script para extração
├─ tmp/
│  ├─ cert.pem                    # Certificado digital A1 (placeholder)
│  └─ key.pem                     # Chave privada do certificado (placeholder)
├─ xml_respostas/                 # Respostas recebidas da SEFAZ
├─ xml_extraidos/                 # XMLs processados e extraídos
├─ nsu.json                       # Armazena o último NSU processado
├─ requirements.txt               # Dependências do projeto
├─ .env                           # Configurações opcionais
├─ LICENSE
└─ README.md
```

---

## ⚙ Requisitos

- **Python** 3.10 ou superior
- Certificado Digital A1 no formato **PEM** (`cert.pem` e `key.pem`)
- Dependências listadas no `requirements.txt`

```bash
pip install -r requirements.txt
```

---

## 🚀 Como Usar

1. Coloque seu certificado digital e chave privada na pasta `tmp/` com os nomes `cert.pem` e `key.pem`.
   - Caso possua o certificado no formato `.pfx`, converta-o para `.pem` e chave privada com:

```bash
openssl pkcs12 -in certificado.pfx -out cert.pem -clcerts -nokeys
openssl pkcs12 -in certificado.pfx -out key.pem -nocerts -nodes
```

2. Ajuste as variáveis de configuração no código ou crie um `.env` com o seguinte formato:

```
CNPJ=00000000000000
TP_AMB=1
UF_AUTOR=35
CERT_PATH=tmp/cert.pem
KEY_PATH=tmp/key.pem
ENDPOINT=https://www1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx
VERIFY_SSL=false
```

3. Execute a consulta:

```bash
python src/consultar_distribuicao.py
```

4. (Opcional) Extraia os documentos baixados:

```bash
python src/extrair_documentos.py
```

---

## 📦 Saída dos Arquivos

- As respostas da SEFAZ serão salvas na pasta `xml_respostas/`
- Os documentos XML extraídos irão para `xml_extraidos/`

---

## 📌 Observações

- O campo **CNPJ** deve ser alterado no código ou `.env` para o documento que será consultado.
- O **último NSU** é armazenado no arquivo `nsu.json` e atualizado automaticamente a cada consulta.
- Por padrão, o script está configurado para **ambiente de produção** (`tpAmb=1`).

---

## 📄 Licença

Este projeto é distribuído sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.
