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

                # Padrão 1: Procura por urls diretas de vídeo no HTML (mp4 / get_stream)
                stream_matches = re.findall(r'https?://[^\s\'"]+/get_stream/[^\s\'"]+', html)
                if not stream_matches:
                    # Tenta capturar URLs .mp4 gerais dentro do código fonte/scripts
                    stream_matches = re.findall(r'https?://[^\s\'"]+\.mp4[^\s\'"]*', html)

                if stream_matches:
                    for stream_url in stream_matches:
                        clean_url = stream_url.replace("&amp;", "&").replace("\\/", "/")
                        if "1080" in clean_url:
                            result["1080p"] = clean_url
                        elif "720" in clean_url:
                            result["720p"] = clean_url
                        elif not result["1080p"]:
                            result["1080p"] = clean_url

                # Padrão 2: Fallback via API do OK.ru (Procura por IDs do OK.ru no HTML)
                if not result["1080p"] and not result["720p"]:
                    # Busca por padrões como ok.ru/videoembed/NUMEROS ou vids=NUMEROS
                    ok_id_match = re.search(r'(?:ok\.ru/videoembed/|vids=)(\d+)', html)
                    if ok_id_match:
                        vid_id = ok_id_match.group(1)
                        api_ok = f"https://api.ok.ru/fb.do?application_key=CBAFJIICABABABABA&fields=video.url_high%2Cvideo.url_fullhd%2Cvideo.url_med&method=video.get&format=json&vids={vid_id}"
                        ok_res = await client.get(api_ok)
                        if ok_res.status_code == 200:
                            data = ok_res.json()
                            if isinstance(data, list) and len(data) > 0:
                                video_info = data[0]
                                result["1080p"] = video_info.get("url_fullhd") or video_info.get("url_high") or ""
                                result["720p"] = video_info.get("url_med") or ""
                            elif "videos" in data and len(data["videos"]) > 0:
                                video_info = data["videos"][0]
                                result["1080p"] = video_info.get("url_fullhd") or video_info.get("url_high") or ""
                                result["720p"] = video_info.get("url_med") or ""

                return result

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao extrair: {str(e)}")

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
