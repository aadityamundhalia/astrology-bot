from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_arguments import KernelArguments
from typing import Annotated
import logging

logger = logging.getLogger(__name__)

class AstrologyTools:
    """Astrology prediction tools for Semantic Kernel"""
    
    # Class-level storage for service and birth data
    _astrology_service = None
    _birth_data = None
    
    @classmethod
    def set_context(cls, astrology_service, date_of_birth, time_of_birth, place_of_birth):
        """Set the context for all tool calls"""
        cls._astrology_service = astrology_service
        cls._birth_data = {
            "date_of_birth": date_of_birth,
            "time_of_birth": time_of_birth,
            "place_of_birth": place_of_birth
        }
    
    def _get_service_and_data(self):
        """Get service and birth data from class variables"""
        if not self._astrology_service:
            raise ValueError("Astrology service not initialized. Call set_context first.")
        if not self._birth_data:
            raise ValueError("Birth data not initialized. Call set_context first.")
        return self._astrology_service, self._birth_data
    
    @kernel_function(
        name="today_prediction",
        description="Get today's astrological prediction. Use when user asks about 'today', 'right now', or immediate daily guidance."
    )
    async def today_prediction(self) -> str:
        """Get today's prediction"""
        try:
            service, birth_data = self._get_service_and_data()
            result = await service.get_today_prediction(birth_data)
            logger.info(f"🔮 Tool call: today_prediction - API result ({len(str(result))} chars): {str(result)[:500]}{'...' if len(str(result)) > 500 else ''}")
            return str(result)
        except Exception as e:
            logger.error(f"Error in today_prediction: {e}")
            return f"Error getting today's prediction: {str(e)}"
    
    @kernel_function(
        name="weekly_prediction",
        description="Get this week's (7-day) prediction. Use when user asks about 'this week' or 'next 7 days'."
    )
    async def weekly_prediction(self) -> str:
        """Get weekly prediction"""
        try:
            service, birth_data = self._get_service_and_data()
            result = await service.get_weekly_prediction(birth_data)
            logger.info(f"🔮 Tool call: weekly_prediction - API result ({len(str(result))} chars): {str(result)[:500]}{'...' if len(str(result)) > 500 else ''}")
            return str(result)
        except Exception as e:
            logger.error(f"Error in weekly_prediction: {e}")
            return f"Error getting weekly prediction: {str(e)}"
    
    @kernel_function(
        name="current_month_prediction",
        description="Get current month's prediction. Use when user asks about 'this month', 'now', or 'currently'."
    )
    async def current_month_prediction(self) -> str:
        """Get current month prediction"""
        try:
            service, birth_data = self._get_service_and_data()
            result = await service.get_current_month_prediction(birth_data)
            logger.info(f"🔮 Tool call: current_month_prediction - API result ({len(str(result))} chars): {str(result)[:500]}{'...' if len(str(result)) > 500 else ''}")
            return str(result)
        except Exception as e:
            logger.error(f"Error in current_month_prediction: {e}")
            return f"Error getting current month prediction: {str(e)}"
    
    @kernel_function(
        name="quarterly_prediction",
        description="Get this quarter's (3-month) prediction. Use when user asks about 'this quarter' or 'next 3 months'."
    )
    async def quarterly_prediction(self) -> str:
        """Get quarterly prediction"""
        try:
            service, birth_data = self._get_service_and_data()
            result = await service.get_quarterly_prediction(birth_data)
            logger.info(f"🔮 Tool call: quarterly_prediction - API result ({len(str(result))} chars): {str(result)[:500]}{'...' if len(str(result)) > 500 else ''}")
            return str(result)
        except Exception as e:
            logger.error(f"Error in quarterly_prediction: {e}")
            return f"Error getting quarterly prediction: {str(e)}"
    
    @kernel_function(
        name="yearly_prediction",
        description="Get 12-month yearly prediction. Use when user asks about 'this year', 'yearly', or '12 months'."
    )
    async def yearly_prediction(self) -> str:
        """Get yearly prediction"""
        try:
            service, birth_data = self._get_service_and_data()
            result = await service.get_yearly_prediction(birth_data)
            logger.info(f"🔮 Tool call: yearly_prediction - API result ({len(str(result))} chars): {str(result)[:500]}{'...' if len(str(result)) > 500 else ''}")
            return str(result)
        except Exception as e:
            logger.error(f"Error in yearly_prediction: {e}")
            return f"Error getting yearly prediction: {str(e)}"
    
    @kernel_function(
        name="love_prediction",
        description="Get love and relationship predictions. Use when user asks about love, relationships, or marriage. Can specify date range."
    )
    async def love_prediction(
        self,
        start_date: Annotated[str, "Start date in YYYY-MM-DD format (optional)"] = "",
        end_date: Annotated[str, "End date in YYYY-MM-DD format (optional)"] = ""
    ) -> str:
        """Get love prediction"""
        try:
            service, birth_data = self._get_service_and_data()
            start = start_date if start_date else None
            end = end_date if end_date else None
            result = await service.get_love_prediction(birth_data, start, end)
            logger.info(f"🔮 Tool call: love_prediction - API result ({len(str(result))} chars): {str(result)[:500]}{'...' if len(str(result)) > 500 else ''}")
            return str(result)
        except Exception as e:
            logger.error(f"Error in love_prediction: {e}")
            return f"Error getting love prediction: {str(e)}"
    
    @kernel_function(
        name="career_prediction",
        description="Get career and professional predictions. Use when user asks about career, job, or promotion. Can specify date range."
    )
    async def career_prediction(
        self,
        start_date: Annotated[str, "Start date in YYYY-MM-DD format (optional)"] = "",
        end_date: Annotated[str, "End date in YYYY-MM-DD format (optional)"] = ""
    ) -> str:
        """Get career prediction"""
        try:
            service, birth_data = self._get_service_and_data()
            start = start_date if start_date else None
            end = end_date if end_date else None
            result = await service.get_career_prediction(birth_data, start, end)
            logger.info(f"🔮 Tool call: career_prediction - API result ({len(str(result))} chars): {str(result)[:500]}{'...' if len(str(result)) > 500 else ''}")
            return str(result)
        except Exception as e:
            logger.error(f"Error in career_prediction: {e}")
            return f"Error getting career prediction: {str(e)}"
    
    @kernel_function(
        name="wealth_prediction",
        description="Get wealth and financial predictions. Use when user asks about money, wealth, or finances. Can specify date range."
    )
    async def wealth_prediction(
        self,
        start_date: Annotated[str, "Start date in YYYY-MM-DD format (optional)"] = "",
        end_date: Annotated[str, "End date in YYYY-MM-DD format (optional)"] = ""
    ) -> str:
        """Get wealth prediction"""
        try:
            service, birth_data = self._get_service_and_data()
            start = start_date if start_date else None
            end = end_date if end_date else None
            result = await service.get_wealth_prediction(birth_data, start, end)
            logger.info(f"🔮 Tool call: wealth_prediction - API result ({len(str(result))} chars): {str(result)[:500]}{'...' if len(str(result)) > 500 else ''}")
            return str(result)
        except Exception as e:
            logger.error(f"Error in wealth_prediction: {e}")
            return f"Error getting wealth prediction: {str(e)}"
    
    @kernel_function(
        name="health_prediction",
        description="Get health and wellness predictions. Use when user asks about health or wellness. Can specify date range."
    )
    async def health_prediction(
        self,
        start_date: Annotated[str, "Start date in YYYY-MM-DD format (optional)"] = "",
        end_date: Annotated[str, "End date in YYYY-MM-DD format (optional)"] = ""
    ) -> str:
        """Get health prediction"""
        try:
            service, birth_data = self._get_service_and_data()
            start = start_date if start_date else None
            end = end_date if end_date else None
            result = await service.get_health_prediction(birth_data, start, end)
            logger.info(f"🔮 Tool call: health_prediction - API result ({len(str(result))} chars): {str(result)[:500]}{'...' if len(str(result)) > 500 else ''}")
            return str(result)
        except Exception as e:
            logger.error(f"Error in health_prediction: {e}")
            return f"Error getting health prediction: {str(e)}"
    
    @kernel_function(
        name="wildcard_prediction",
        description="Get prediction for specific events or questions. Use for specific dates, events, or detailed queries like 'job interview on Dec 15th' or 'buying motorcycle on Nov 5th'."
    )
    async def wildcard_prediction(
        self,
        query: Annotated[str, "Specific question or event description"],
        specific_date: Annotated[str, "Specific date for the event in YYYY-MM-DD format (optional)"] = ""
    ) -> str:
        """Get wildcard prediction"""
        try:
            service, birth_data = self._get_service_and_data()
            date = specific_date if specific_date else None
            result = await service.get_wildcard_prediction(birth_data, query, date)
            logger.info(f"🔮 Tool call: wildcard_prediction - API result ({len(str(result))} chars): {str(result)[:500]}{'...' if len(str(result)) > 500 else ''}")
            return str(result)
        except Exception as e:
            logger.error(f"Error in wildcard_prediction: {e}")
            return f"Error getting wildcard prediction: {str(e)}"
    
    @kernel_function(
        name="daily_horoscope",
        description="Get daily horoscope based on moon sign. Use for general daily horoscope requests."
    )
    async def daily_horoscope(self) -> str:
        """Get daily horoscope"""
        try:
            service, birth_data = self._get_service_and_data()
            result = await service.get_daily_horoscope(birth_data)
            logger.info(f"🔮 Tool call: daily_horoscope - API result ({len(str(result))} chars): {str(result)[:500]}{'...' if len(str(result)) > 500 else ''}")
            return str(result)
        except Exception as e:
            logger.error(f"Error in daily_horoscope: {e}")
            return f"Error getting daily horoscope: {str(e)}"
    
    @kernel_function(
        name="weekly_horoscope",
        description="Get weekly horoscope. Use for general weekly horoscope requests."
    )
    async def weekly_horoscope(self) -> str:
        """Get weekly horoscope"""
        try:
            service, birth_data = self._get_service_and_data()
            result = await service.get_weekly_horoscope(birth_data)
            logger.info(f"🔮 Tool call: weekly_horoscope - API result ({len(str(result))} chars): {str(result)[:500]}{'...' if len(str(result)) > 500 else ''}")
            return str(result)
        except Exception as e:
            logger.error(f"Error in weekly_horoscope: {e}")
            return f"Error getting weekly horoscope: {str(e)}"
    
    @kernel_function(
        name="monthly_horoscope",
        description="Get monthly horoscope. Use for general monthly horoscope requests."
    )
    async def monthly_horoscope(self) -> str:
        """Get monthly horoscope"""
        try:
            service, birth_data = self._get_service_and_data()
            result = await service.get_monthly_horoscope(birth_data)
            logger.info(f"🔮 Tool call: monthly_horoscope - API result ({len(str(result))} chars): {str(result)[:500]}{'...' if len(str(result)) > 500 else ''}")
            return str(result)
        except Exception as e:
            logger.error(f"Error in monthly_horoscope: {e}")
            return f"Error getting monthly horoscope: {str(e)}"
    
    @classmethod
    def get_tool_definitions(cls):
        """Get tool definitions in Ollama format for direct API calls"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "today_prediction",
                    "description": "Get today's astrological prediction. Use when user asks about 'today', 'right now', or immediate daily guidance.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "weekly_prediction",
                    "description": "Get this week's (7-day) prediction. Use when user asks about 'this week' or 'next 7 days'.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "current_month_prediction",
                    "description": "Get this month's prediction. Use when user asks about 'this month' or 'currently'.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "quarterly_prediction",
                    "description": "Get this quarter's (3-month) prediction. Use when user asks about 'this quarter' or 'next 3 months'.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "yearly_prediction",
                    "description": "Get this year's prediction. Use when user asks about 'this year', 'yearly', or '12 months'.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "love_prediction",
                    "description": "Get love and relationship prediction. Use when user asks about 'love', 'relationship', or 'marriage'.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "career_prediction",
                    "description": "Get career and job prediction. Use when user asks about 'career', 'job', or 'promotion'.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wealth_prediction",
                    "description": "Get wealth and money prediction. Use when user asks about 'wealth', 'money', or 'finance'.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "health_prediction",
                    "description": "Get health prediction. Use when user asks about 'health' or 'wellness'.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wildcard_prediction",
                    "description": "Get a wildcard or general prediction for unspecified topics.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "daily_horoscope",
                    "description": "Get daily horoscope for a specific zodiac sign.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sign": {
                                "type": "string",
                                "description": "The zodiac sign (e.g., 'aries', 'taurus', 'gemini', etc.)"
                            }
                        },
                        "required": ["sign"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "weekly_horoscope",
                    "description": "Get weekly horoscope for a specific zodiac sign.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sign": {
                                "type": "string",
                                "description": "The zodiac sign (e.g., 'aries', 'taurus', 'gemini', etc.)"
                            }
                        },
                        "required": ["sign"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "monthly_horoscope",
                    "description": "Get monthly horoscope for a specific zodiac sign.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sign": {
                                "type": "string",
                                "description": "The zodiac sign (e.g., 'aries', 'taurus', 'gemini', etc.)"
                            }
                        },
                        "required": ["sign"]
                    }
                }
            }
        ]
    
    async def execute_tool(self, tool_name: str, arguments: dict = None):
        """Execute a tool by name with given arguments"""
        if arguments is None:
            arguments = {}
            
        method = getattr(self, tool_name, None)
        if not method:
            raise ValueError(f"Tool {tool_name} not found")
            
        # Call the method (all our tools don't take arguments currently)
        result = await method()
        return result
