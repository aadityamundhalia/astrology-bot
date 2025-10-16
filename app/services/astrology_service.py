import httpx
from config import get_settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class AstrologyService:
    def __init__(self):
        self.base_url = settings.astrology_api_url
    
    async def _make_request(self, endpoint: str, birth_data: dict, extra_params: dict = None) -> dict:
        """Make request to astrology API"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                payload = {
                    "date_of_birth": birth_data["date_of_birth"],
                    "time_of_birth": birth_data["time_of_birth"],
                    "place_of_birth": birth_data["place_of_birth"]
                }
                
                if extra_params:
                    payload.update(extra_params)
                
                response = await client.post(
                    f"{self.base_url}{endpoint}",
                    json=payload,
                    headers={"accept": "application/json"}
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Error calling {endpoint}: {e}")
                raise
    
    async def get_today_prediction(self, birth_data: dict) -> dict:
        return await self._make_request("/predictions/today", birth_data)
    
    async def get_weekly_prediction(self, birth_data: dict) -> dict:
        return await self._make_request("/predictions/week", birth_data)
    
    async def get_quarterly_prediction(self, birth_data: dict) -> dict:
        return await self._make_request("/predictions/quarter", birth_data)
    
    async def get_yearly_prediction(self, birth_data: dict) -> dict:
        return await self._make_request("/predictions/yearly", birth_data)
    
    async def get_current_month_prediction(self, birth_data: dict) -> dict:
        return await self._make_request("/predictions/current-month", birth_data)
    
    async def get_love_prediction(self, birth_data: dict, start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
        extra = {}
        if start_date:
            extra["start_date"] = start_date
        if end_date:
            extra["end_date"] = end_date
        return await self._make_request("/predictions/love", birth_data, extra)
    
    async def get_health_prediction(self, birth_data: dict, start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
        extra = {}
        if start_date:
            extra["start_date"] = start_date
        if end_date:
            extra["end_date"] = end_date
        return await self._make_request("/predictions/health", birth_data, extra)
    
    async def get_career_prediction(self, birth_data: dict, start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
        extra = {}
        if start_date:
            extra["start_date"] = start_date
        if end_date:
            extra["end_date"] = end_date
        return await self._make_request("/predictions/career", birth_data, extra)
    
    async def get_wealth_prediction(self, birth_data: dict, start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
        extra = {}
        if start_date:
            extra["start_date"] = start_date
        if end_date:
            extra["end_date"] = end_date
        return await self._make_request("/predictions/wealth", birth_data, extra)
    
    async def get_wildcard_prediction(self, birth_data: dict, query: str, specific_date: Optional[str] = None) -> dict:
        extra = {"query": query}
        if specific_date:
            extra["specific_date"] = specific_date
        return await self._make_request("/predictions/wildcard", birth_data, extra)
    
    async def get_daily_horoscope(self, birth_data: dict) -> dict:
        return await self._make_request("/horoscope/daily", birth_data)
    
    async def get_weekly_horoscope(self, birth_data: dict) -> dict:
        return await self._make_request("/horoscope/weekly", birth_data)
    
    async def get_monthly_horoscope(self, birth_data: dict) -> dict:
        return await self._make_request("/horoscope/monthly", birth_data)
