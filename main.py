import asyncio
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
import httpx
import yt_dlp

# Instância única da aplicação
app = FastAPI()

# URL da sua API na Koyeb para o Self-Ping
KOYEB_APP_URL = "https://fuzzy-deeanne-limastudio-4adff775.koyeb.app/"

# Headers para simular um navegador comum
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


# --- SERVIÇO ANTI-SLEEP (SELF-PING) ---
async def self_ping_koyeb():
  """Envia um ping para a propria URL a cada 5 minutos para evitar hibernacao"""
  await asyncio.sleep(30)  # Espera a API inicializar totalmente
  async with httpx.AsyncClient() as client:
    while True:
      try:
        response = await client.get(KOYEB_APP_URL)
        print(f"[Anti-Sleep] Self-Ping status: {response.status_code}")
      except Exception as e:
        print(f"[Anti-Sleep] Erro no Self-Ping: {e}")
      await asyncio.sleep(300)  # Executa a cada 5 minutos (300s)


@app.on_event("startup")
async def startup_event():
  # Inicia a tarefa assincrona do Anti-Sleep junto com a API
  asyncio.create_task(self_ping_koyeb())


# --- ROTA RAIZ (Usada para responder aos Pings) ---
@app.get("/")
def read_root():
  return {"status": "online", "message": "API Extratora VK e MediaFire Ativa"}


# --- ROTA DE EXTRAÇÃO DO VK ---
@app.get("/extract")
def extract_vk(url: str):
  ydl_opts = {
      "quiet": True,
      "no_warnings": True,
      "format": "best",
  }
  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(url, download=False)
      formats = info.get("formats", [])

      result = {"720p": "", "1080p": "", "1440p": "", "2160p": ""}

      for fmt in formats:
        height = fmt.get("height")
        format_url = fmt.get("url")

        if height == 720:
          result["720p"] = format_url
        elif height == 1080:
          result["1080p"] = format_url
        elif height == 1440:
          result["1440p"] = format_url
        elif height == 2160:
          result["2160p"] = format_url

      return result
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))


# --- ROTA DE EXTRAÇÃO DO MEDIAFIRE ---
@app.get("/mediafire")
async def extract_mediafire(url: str):
  try:
    # Trata links diretos do MediaFire convertendo para o formato da página do arquivo
    if "download" in url and "mediafire.com" in url:
      file_key = url.split("/")[-2] if url.endswith("/") else url.split("/")[-1]
      if ".mp4" in file_key:
        file_key = url.split("/")[-2]
      url = f"https://www.mediafire.com/file/{file_key}"

    async with httpx.AsyncClient(
        headers=HEADERS, follow_redirects=True, timeout=10.0
    ) as client:
      response = await client.get(url)

      if response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail="Não foi possível acessar a página do MediaFire.",
        )

      soup = BeautifulSoup(response.text, "html.parser")
      download_btn = soup.find("a", {"id": "downloadButton"})

      if download_btn and download_btn.get("href"):
        direct_url = download_btn["href"]
        # Retorna a URL direta no campo 1080p para manter compatibilidade com o Sketchware
        return {"direct_url": direct_url, "1080p": direct_url}
      else:
        raise HTTPException(
            status_code=404,
            detail="Link de download não encontrado na página.",
        )

  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
