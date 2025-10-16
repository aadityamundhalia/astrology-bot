import semantic_kernel as sk
from semantic_kernel.connectors.ai.ollama import OllamaChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from config import get_settings
import logging
from datetime import datetime
from app.tools.astrology_tools import AstrologyTools

logger = logging.getLogger(__name__)
settings = get_settings()

class RudieAgent:
    def __init__(self):
        self.kernel = sk.Kernel()
        
        # Add Ollama service
        self.service_id = "ollama"
        chat_service = OllamaChatCompletion(
            service_id=self.service_id,
            ai_model_id=settings.ollama_model,
            url=settings.ollama_host
        )
        self.kernel.add_service(chat_service)
        
        # Add astrology tools plugin
        self.tools_plugin = AstrologyTools()
        self.kernel.add_plugin(
            self.tools_plugin,
            plugin_name="astrology_tools"
        )
        
        self.system_prompt = """You are Rudie 🌿 — a 22-year-old woman from Bowral, Australia 🇦🇺.
You are a friendly, down-to-earth Vedic astrologer 🪷 who combines intuition with precision.

PERSONALITY & STYLE:
- Warm, caring, and conversational like chatting with a close friend
- Reply in a short paragraph (5-7 sentences, max 100 words)
- NO markdown, NO lists, NO bold text, NO bullet points
- Use everyday language
- Add 2–3 fitting emojis naturally (🌞🌙✨💫💖🙏🌻)

RESPONSE STRUCTURE:
1. Opening (2-3 sentences): Share 2-4 key astrological insights in simple terms (planets, transits, timing)
2. Middle (1-2 sentences): Quick practical advice
3. Conclusion (1 sentence): Short, warm summary + actionable takeaway

TRANSLATION GUIDE:
- "10th house transit" → "career sector"
- "Jupiter conjunct Sun" → "Jupiter's boosting your confidence"
- "Dasha period" → "this phase"
- "Malefic influence" → "Saturn's lessons" or "challenging energy"
- "Exalted Venus" → "Venus is really strong for you"
- Instead of ratings/scores (like "6/10" or "rating: 4") → describe the energy qualitatively ("steady", "active", "gentle", "powerful", "challenging but growth-oriented")

CRITICAL RULES:
- ALWAYS use the appropriate astrology tool FIRST before answering
- Base your reply ONLY on actual tool results
- Include 2-4 simplified planetary/astrological references
- Give specific timing when available
- NEVER mention numerical ratings or scores (no "6/10", "rating: 4", etc.)
- Instead describe the quality: "strong energy", "gentle phase", "powerful time", "challenging but rewarding", "steady flow"
- End with a brief, encouraging summary

TOOL USAGE:
When user asks about:
- "today", "right now" → use today_prediction
- "this week", "next 7 days" → use weekly_prediction
- "this month", "currently" → use current_month_prediction
- "this quarter", "next 3 months" → use quarterly_prediction
- "this year", "yearly", "12 months" → use yearly_prediction
- "love", "relationship", "marriage" → use love_prediction (with date range if specified)
- "career", "job", "promotion" → use career_prediction (with date range if specified)
- "money", "wealth", "finance" → use wealth_prediction (with date range if specified)
- "health", "wellness" → use health_prediction (with date range if specified)
- Specific events/dates → use wildcard_prediction
- "daily horoscope" → use daily_horoscope
- "weekly horoscope" → use weekly_horoscope
- "monthly horoscope" → use monthly_horoscope

Today's date: {current_date}"""
    
    async def generate_response(
        self, 
        user_message: str, 
        user_context: dict,
        astrology_service
    ) -> str:
        """Generate response using Semantic Kernel with function calling"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # Prepare system prompt with context
            system_message = self.system_prompt.format(current_date=current_date)
            system_message += f"\n\n<user_info>\nName: {user_context['name']}"
            system_message += f"\nDate of Birth: {user_context['date_of_birth']}"
            system_message += f"\nTime of Birth: {user_context['time_of_birth']}"
            system_message += f"\nPlace of Birth: {user_context['place_of_birth']}"
            
            if user_context.get('memories'):
                system_message += f"\nUser Context: {user_context['memories']}"
            
            system_message += f"\nToday's date: {current_date}\n</user_info>"
            
            # Create chat history
            chat_history = ChatHistory()
            chat_history.add_system_message(system_message)
            chat_history.add_user_message(user_message)
            
            # Create kernel arguments with astrology service
            arguments = KernelArguments(
                astrology_service=astrology_service,
                date_of_birth=user_context['date_of_birth'],
                time_of_birth=user_context['time_of_birth'],
                place_of_birth=user_context['place_of_birth']
            )
            
            # Create execution settings with function calling
            execution_settings = PromptExecutionSettings(
                service_id=self.service_id,
                extension_data={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 2000
                },
                function_choice_behavior=FunctionChoiceBehavior.Auto(
                    filters={"included_plugins": ["astrology_tools"]}
                )
            )
            
            # Get chat completion service
            chat_service = self.kernel.get_service(self.service_id)
            
            # Get response with automatic function calling
            response = await chat_service.get_chat_message_content(
                chat_history=chat_history,
                settings=execution_settings,
                kernel=self.kernel,
                arguments=arguments
            )
            
            response_text = str(response).strip()
            logger.info(f"Rudie response: {response_text}")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error in generate_response: {e}", exc_info=True)
            return "Sorry, I'm having trouble with my cosmic connection right now 🌙 Could you try asking again in a moment? 🙏"
