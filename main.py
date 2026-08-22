from fastapi import FastAPI, HTTPException
import yt_dlp

app = FastAPI()

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