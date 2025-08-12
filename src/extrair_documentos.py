import os
import base64
import gzip
import argparse
from lxml import etree

# .env opcional (apenas para PASTA_RESPOSTAS/PASTA_SAIDA)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

PASTA_RESPOSTAS = os.getenv("PASTA_SAIDA", "xml_respostas")
PASTA_SAIDA     = os.getenv("PASTA_EXTRAIDOS", "xml_extraidos")

os.makedirs(PASTA_SAIDA, exist_ok=True)

NS = {
    "soap": "http://schemas.xmlsoap.org/soap/envelope/",
    "nfe":  "http://www.portalfiscal.inf.br/nfe",
}

def listar_arquivos_xml(pasta):
    return [os.path.join(pasta, f) for f in os.listdir(pasta) if f.lower().endswith(".xml")]

def extrair_doczip_de_xml(caminho_xml):
    print(f"\n📂 Processando: {caminho_xml}")
    with open(caminho_xml, "rb") as f:
        conteudo = f.read()

    root = etree.fromstring(conteudo)
    doczips = root.findall(".//nfe:docZip", namespaces=NS)

    if not doczips:
        print("⚠️ Nenhum docZip encontrado.")
        return 0

    print(f"🔍 {len(doczips)} docZip encontrados.")
    count = 0

    for idx, doczip in enumerate(doczips, start=1):
        nsu    = doczip.get("NSU") or f"nsu_{idx}"
        schema = doczip.get("schema") or "desconhecido"
        b64txt = (doczip.text or "").strip()

        if not b64txt:
            print(f"⚠️ docZip {idx} sem conteúdo.")
            continue

        try:
            dados_xml = gzip.decompress(base64.b64decode(b64txt))
        except Exception as e:
            print(f"❌ Erro ao decodificar/descompactar docZip {idx}: {e}")
            continue

        nome_arquivo = f"{nsu}_{schema}.xml".replace("/", "_")
        caminho_saida = os.path.join(PASTA_SAIDA, nome_arquivo)

        with open(caminho_saida, "wb") as out:
            out.write(dados_xml)

        count += 1
        print(f"✅ Salvo: {nome_arquivo}")

    return count

def parse_args():
    p = argparse.ArgumentParser(description="Extrai docZip (Base64+GZIP) de respostas da SEFAZ.")
    p.add_argument("--input", help="Arquivo XML específico para extrair. Se omitido, varre a pasta xml_respostas.")
    p.add_argument("--outdir", default=PASTA_SAIDA, help="Pasta de saída (default: xml_extraidos).")
    return p.parse_args()

def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    if args.input:
        arquivos = [args.input]
    else:
        arquivos = listar_arquivos_xml(PASTA_RESPOSTAS)

    if not arquivos:
        print(f"⚠️ Nenhum XML encontrado em: {PASTA_RESPOSTAS}")
        return

    total = 0
    for arq in arquivos:
        total += extrair_doczip_de_xml(arq)

    print(f"\n📦 Total de arquivos extraídos: {total}")

if __name__ == "__main__":
    main()
