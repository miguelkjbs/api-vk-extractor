from fastapi import FastAPI, HTTPException
import yt_dlp
import asyncio
import httpx

app = FastAPI()

# URL da sua API na Koyeb para o Self-Ping
KOYEB_APP_URL = "https://fuzzy-deeanne-limastudio-4adff775.koyeb.app/"

# --- SERVIÇO ANTI-SLEEP (SELF-PING) ---
async def self_ping_koyeb():
    """Envia um ping para a propria URL a cada 5 minutos para evitar hibernacao"""
    await asyncio.sleep(30)  # Espera a API inicializar totalmente
    async with httpx.AsyncClient() as client:
        while True:
            try:
                # Faz ping na rota raiz para manter o processo ativo
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
    return {"status": "online", "message": "API Extratora VK Ativa"}

# --- ROTA DE EXTRAÇÃO ---
@app.get("/extract")
def extract_vk(url: str):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            result = {
                "720p": "",
                "1080p": "",
                "1440p": "",
                "2160p": ""
            }
            
            for fmt in formats:
                height = fmt.get('height')
                format_url = fmt.get('url')
                
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
