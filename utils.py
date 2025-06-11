import re
from typing import Optional
import aiohttp

async def fetch_twitter_community_id(ipfs_uri: str) -> Optional[str]:
    """
    Извлекает ID комьюнити Twitter из IPFS-данных токена.
    Возвращает None, если ссылка на комьюнити не найдена.
    """
    try:
        async with aiohttp.ClientSession() as session:
            # Загружаем JSON-данные из IPFS
            async with session.get(ipfs_uri) as response:
                if response.status != 200:
                    return None
                data = await response.json()

            # Проверяем поля 'twitter' и 'website'
            for field in ['twitter', 'website']:
                if field in data:
                    url = data[field].strip()
                    # Ищем ID комьюнити в URL (поддержка старого x.com и нового twitter.com)
                    match = re.search(
                        r'(https?://(?:x\.com|twitter\.com)/i/communities/)(\d+)', 
                        url
                    )
                    if match:
                        return match.group(2)  # Возвращаем только ID

            return None

    except Exception as e:
        #print(f"Error fetching community ID: {e}")
        return None