import os
import re
import json
import argparse
import datetime as dt
import requests
from lxml import etree

# .env opcional
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ================== Config (com defaults + .env) ==================
KEY_PATH        = os.getenv("KEY_PATH", "tmp/key.pem")
CERT_PATH       = os.getenv("CERT_PATH", "tmp/cert.pem")
XML_ENTRADA     = os.getenv("XML_ENTRADA", "entrada.xml")
PASTA_SAIDA     = os.getenv("PASTA_SAIDA", "xml_respostas")
ARQUIVO_NSU     = os.getenv("ARQUIVO_NSU", "nsu.json")
CNPJ_ENV        = os.getenv("CNPJ", "")
UF_AUTOR_ENV    = os.getenv("UF_AUTOR", "35")   # 35 = SP
TP_AMB_ENV      = os.getenv("TP_AMB", "1")      # 1=Prod, 2=Homolog
SSL_VERIFY_ENV  = os.getenv("SSL_VERIFY", "false").lower() in ("1","true","yes")
HTTP_TIMEOUT    = float(os.getenv("HTTP_TIMEOUT", "30"))
ENDPOINT_ENV    = os.getenv("ENDPOINT", "https://www1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx")

os.makedirs(PASTA_SAIDA, exist_ok=True)


# ================== Helpers ==================
def valida_cnpj(cnpj: str) -> str:
    c = re.sub(r"\D", "", cnpj or "")
    if len(c) != 14:
        raise ValueError("CNPJ deve conter 14 dígitos.")
    return c

def carregar_nsu(path: str) -> str:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                dados = json.load(f)
                return dados.get("ultNSU", "000000000000000")
        except Exception:
            pass
    return "000000000000000"

def salvar_nsu(path: str, novo_nsu: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"ultNSU": novo_nsu}, f, ensure_ascii=False, indent=2)
    print(f"💾 NSU atualizado para: {novo_nsu}")

def montar_xml_dist_dfe(cnpj: str, cuf_autor: str, ult_nsu: str, tp_amb: str):
    ns = "http://www.portalfiscal.inf.br/nfe"
    root = etree.Element(f"{{{ns}}}distDFeInt", nsmap={None: ns}, versao="1.01")
    etree.SubElement(root, f"{{{ns}}}tpAmb").text = tp_amb
    etree.SubElement(root, f"{{{ns}}}cUFAutor").text = cuf_autor
    etree.SubElement(root, f"{{{ns}}}CNPJ").text = cnpj
    dist_nsu = etree.SubElement(root, f"{{{ns}}}distNSU")
    etree.SubElement(dist_nsu, f"{{{ns}}}ultNSU").text = ult_nsu
    return root

def salvar_xml(xml_element, caminho):
    tree = etree.ElementTree(xml_element)
    with open(caminho, "wb") as f:
        tree.write(f, encoding="utf-8", xml_declaration=True, pretty_print=True)
    print(f"📁 XML salvo em: {caminho}")

def envelope_soap(xml_str: str) -> str:
    return f"""
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
      <soap:Body>
        <nfeDistDFeInteresse xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe">
          <nfeDadosMsg>{xml_str}</nfeDadosMsg>
        </nfeDistDFeInteresse>
      </soap:Body>
    </soap:Envelope>
    """.strip()

def enviar(endpoint, xml_enveloped, cert_path, key_path, verify, timeout):
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe/nfeDistDFeInteresse",
    }
    resp = requests.post(
        endpoint,
        data=xml_enveloped.encode("utf-8"),
        headers=headers,
        cert=(cert_path, key_path),
        verify=verify,
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.text

def extrair_ult_nsu(resposta_xml: str):
    ns = {
        "soap": "http://schemas.xmlsoap.org/soap/envelope/",
        "nfe": "http://www.portalfiscal.inf.br/nfe",
    }
    root = etree.fromstring(resposta_xml.encode("utf-8"))
    el = root.find(".//nfe:ultNSU", namespaces=ns)
    return el.text.strip() if el is not None and el.text else None

def salvar_resposta(resposta: str, dir_saida: str, ult_nsu: str) -> str:
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(dir_saida, f"resposta_{ult_nsu}_{timestamp}.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(resposta)
    print(f"💾 Resposta salva em: {path}")
    return path


# ================== CLI ==================
def parse_args():
    p = argparse.ArgumentParser(description="Cliente SEFAZ - NFeDistribuicaoDFe")
    p.add_argument("--cnpj", help="CNPJ do interessado (14 dígitos). Se omitido, usa .env.")
    p.add_argument("--uf-autor", default=UF_AUTOR_ENV, help="cUFAutor (IBGE). Ex.: 35=SP.")
    p.add_argument("--tp-amb", default=TP_AMB_ENV, choices=["1", "2"], help="Ambiente: 1=Produção, 2=Homolog.")
    p.add_argument("--endpoint", default=ENDPOINT_ENV, help="URL do serviço SOAP.")
    p.add_argument("--cert", default=CERT_PATH, help="Caminho do cert.pem.")
    p.add_argument("--key", default=KEY_PATH, help="Caminho do key.pem.")
    p.add_argument("--entrada-xml", default=XML_ENTRADA, help="Arquivo para salvar o XML de entrada.")
    p.add_argument("--saida", default=PASTA_SAIDA, help="Pasta de saída para respostas.")
    p.add_argument("--verify", default=str(SSL_VERIFY_ENV), help="Validar SSL (true/false).")
    p.add_argument("--timeout", type=float, default=HTTP_TIMEOUT, help="Timeout HTTP (s).")
    p.add_argument("--nsu-file", default=ARQUIVO_NSU, help="Arquivo de persistência do ultNSU (json).")
    return p.parse_args()


def main():
    args = parse_args()
    verify = str(args.verify).lower() in ("1","true","yes")
    os.makedirs(args.saida, exist_ok=True)

    # 1) CNPJ/NSU
    try:
        cnpj = valida_cnpj(args.cnpj or CNPJ_ENV)
    except ValueError as e:
        print(f"❌ {e}")
        return

    ult_nsu = carregar_nsu(args.nsu_file)
    print(f"🔢 Usando ultNSU: {ult_nsu}")

    # 2) Montar XML
    xml_el = montar_xml_dist_dfe(cnpj, args.uf_autor, ult_nsu, args.tp_amb)
    salvar_xml(xml_el, args.entrada_xml)

    xml_str = etree.tostring(xml_el, encoding="utf-8", xml_declaration=False).decode("utf-8").strip()
    soap_env = envelope_soap(xml_str)

    print("\n📤 XML ENVIADO (SOAP):")
    print(soap_env)

    # 3) Enviar
    try:
        print("\n📨 Enviando para a SEFAZ...")
        resposta = enviar(
            endpoint=args.endpoint,
            xml_enveloped=soap_env,
            cert_path=args.cert,
            key_path=args.key,
            verify=verify,
            timeout=args.timeout,
        )
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP {e.response.status_code}: {e.response.text[:400]}")
        return
    except requests.exceptions.SSLError as e:
        print(f"❌ Erro SSL: {e}")
        return
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de requisição: {e}")
        return

    print("\n📩 Resposta DA SEFAZ (trecho):")
    print(resposta[:2000] + ("...\n[truncado]" if len(resposta) > 2000 else ""))

    # 4) Persistir resposta + atualizar ultNSU
    salvar_resposta(resposta, args.saida, ult_nsu)
    novo_nsu = extrair_ult_nsu(resposta)
    if novo_nsu:
        salvar_nsu(args.nsu_file, novo_nsu)
    else:
        print("⚠️ Não foi possível extrair o ultNSU da resposta.")


if __name__ == "__main__":
    main()
