import asyncio
import re
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
import httpx
import yt_dlp

app = FastAPI()

# URL da sua API na Koyeb para o Self-Ping
KOYEB_APP_URL = "https://continuous-jan-limastudio-5d9efa38.koyeb.app/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# --- SERVIÇO ANTI-SLEEP (SELF-PING) ---
async def self_ping_koyeb():
    await asyncio.sleep(30)
    async with httpx.AsyncClient() as client:
        while True:
            try:
                response = await client.get(KOYEB_APP_URL)
                print(f"[Anti-Sleep] Self-Ping status: {response.status_code}")
            except Exception as e:
                print(f"[Anti-Sleep] Erro no Self-Ping: {e}")
            await asyncio.sleep(300)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(self_ping_koyeb())

@app.get("/")
def read_root():
    return {"status": "online", "message": "API Extratora Ativa"}

# --- ROTA PRINCIPAL DE EXTRAÇÃO ---
@app.get("/extract")
async def extract_video(url: str):
    # 1. TRATAMENTO ESPECÍFICO PARA THEPORNBANG
    if "thepornbang.com" in url:
        try:
            async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=15.0) as client:
                res = await client.get(url)
                if res.status_code != 200:
                    raise HTTPException(status_code=400, detail="Não foi possível acessar o site.")

                html = res.text
                result = {"720p": "", "1080p": "", "1440p": "", "2160p": ""}

                # Busca padrão 1: Links de stream do servidor do próprio site (/get_stream/)
                stream_matches = re.findall(r'https?://[^\s\'"]+/get_stream/[^\s\'"]+', html)
                if stream_matches:
                    for stream_url in stream_matches:
                        # Substitui entidades HTML codificadas como &amp;
                        clean_url = stream_url.replace("&amp;", "&")
                        if "1080" in clean_url:
                            result["1080p"] = clean_url
                        elif "720" in clean_url:
                            result["720p"] = clean_url
                        elif not result["1080p"]:
                            result["1080p"] = clean_url

                # Busca padrão 2: Fallback via API do OK.ru se não encontrar stream direto
                if not result["1080p"] and not result["720p"]:
                    ok_match = re.search(r'vids=(\d+)', html)
                    if ok_match:
                        vid_id = ok_match.group(1)
                        api_ok = f"https://api.ok.ru/fb.do?application_key=CBAFJIICABABABABA&fields=video.url_high%2Cvideo.url_fullhd&method=video.get&format=json&vids={vid_id}"
                        ok_res = await client.get(api_ok)
                        if ok_res.status_code == 200:
                            data = ok_res.json()
                            if "videos" in data and len(data["videos"]) > 0:
                                video_info = data["videos"][0]
                                result["1080p"] = video_info.get("url_fullhd") or video_info.get("url_high") or ""

                return result

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao extrair thepornbang: {str(e)}")

    # 2. TRATAMENTO PADRÃO VIA YT-DLP (VK, YOUTUBE, ETC)
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
        if "download" in url and "mediafire.com" in url:
            file_key = url.split("/")[-2] if url.endswith("/") else url.split("/")[-1]
            if ".mp4" in file_key:
                file_key = url.split("/")[-2]
            url = f"https://www.mediafire.com/file/{file_key}"

        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=10.0) as client:
            response = await client.get(url)

            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Não foi possível acessar a página do MediaFire.")

            soup = BeautifulSoup(response.text, "html.parser")
            download_btn = soup.find("a", {"id": "downloadButton"})

            if download_btn and download_btn.get("href"):
                direct_url = download_btn["href"]
                return {"direct_url": direct_url, "1080p": direct_url}
            else:
                raise HTTPException(status_code=404, detail="Link de download não encontrado na página.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))async def startup_event():
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
