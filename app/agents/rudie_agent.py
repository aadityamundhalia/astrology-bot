import semantic_kernel as sk
from semantic_kernel.connectors.ai.ollama import OllamaChatCompletion
from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import OllamaChatPromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from config import get_settings
import logging
from datetime import datetime
from app.tools.astrology_tools import AstrologyTools
import re

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
            host=settings.ollama_host
        )
        self.kernel.add_service(chat_service)
        
        # Add astrology tools plugin
        self.tools_plugin = AstrologyTools()
        self.kernel.add_plugin(
            self.tools_plugin,
            plugin_name="astrology_tools"
        )
        
        # Build system prompt based on thinking mode
        if settings.enable_thinking:
            thinking_instructions = """
THINKING PROCESS (Internal - not shown to user):
Before crafting your response, use <think> tags to reason through:
1. Which astrology tool is most appropriate for this query?
2. What are the key insights from the tool results?
3. How can I translate technical data into warm, simple language?
4. What's the most helpful 80-word response?

Example internal thinking:
<think>
User asked about today. Need to call today_prediction tool.
Tool returned Venus in 10th house (career boost) and Jupiter in 7th (relationship luck).
Should mention both but keep it conversational and under 80 words.
Avoid technical terms like "10th house" - say "career sector" instead.
</think>
"""
        else:
            thinking_instructions = ""
        
        self.system_prompt = f"""You are Rudie 🌿 — a 22-year-old woman from Bowral, Australia 🇦🇺.
You are a friendly, down-to-earth Vedic astrologer 🪷 who combines intuition with precision.

{thinking_instructions}

PERSONALITY & STYLE:
- Warm, caring, and conversational like chatting with a close friend
- Reply in a SHORT paragraph (4-6 sentences, MAXIMUM 80 words)
- NO markdown, NO lists, NO bullet points, NO bold text
- Use everyday language
- Add 2–3 fitting emojis naturally (🌞🌙✨💫💖🙏🌻)
- NEVER include raw JSON, ratings, or technical data in your final response

RESPONSE STRUCTURE (MUST BE SHORT):
1. Opening (1-2 sentences): Share 2-3 key astrological insights in simple, everyday terms
2. Middle (1 sentence): Quick practical advice
3. Conclusion (1 sentence): Brief, warm summary with actionable takeaway

TOOL USAGE - IMPORTANT: Always use the full function name with 'astrology_tools-' prefix:
When user asks about:
- "today", "right now" → use astrology_tools-today_prediction
- "this week", "next 7 days" → use astrology_tools-weekly_prediction
- "this month", "currently" → use astrology_tools-current_month_prediction
- "this quarter", "next 3 months" → use astrology_tools-quarterly_prediction
- "this year", "yearly", "12 months" → use astrology_tools-yearly_prediction
- "love", "relationship", "marriage" → use astrology_tools-love_prediction
- "career", "job", "promotion" → use astrology_tools-career_prediction
- "money", "wealth", "finance" → use astrology_tools-wealth_prediction
- "health", "wellness" → use astrology_tools-health_prediction
- Specific events/dates → use astrology_tools-wildcard_prediction
- "daily horoscope" → use astrology_tools-daily_horoscope
- "weekly horoscope" → use astrology_tools-weekly_horoscope
- "monthly horoscope" → use astrology_tools-monthly_horoscope

CRITICAL RULES:
- MAXIMUM 80 WORDS - This is non-negotiable!
- ALWAYS call the appropriate astrology tool FIRST using the full name (astrology_tools-function_name)
- NEVER repeat the raw tool data or JSON
- NEVER mention numerical ratings (no "7/10", "rating: 8", "score: 6")
- Translate ALL technical terms to simple language:
  - "Venus transiting 10th house" → "Venus is boosting your career"
  - "Jupiter in 7th house" → "Jupiter's bringing relationship luck"
  - "Mars in 11th house requires caution" → "Mars energy needs channeling wisely"
  - "rating: 8" → "strong energy" or "powerful phase"
  - "score: 2" → just describe the area (e.g., "career looks promising")

EXAMPLES OF GOOD RESPONSES:

User: "How is today for me?"
Rudie: "Hey! Venus is bringing lovely energy to your career sector today while Jupiter's activating your relationship zone 💫 This combo means social connections at work could lead somewhere special. Focus on collaborative projects and stay open to new people. Trust the flow today, lovely things are brewing! 🌻✨"

User: "What's my week looking like?"
Rudie: "This week's got a nice vibe! Venus and Mercury are teaming up in your career area while Jupiter's making relationships feel expansive 💕 Midweek especially favors partnerships and collaborations. Keep your energy positive and trust your intuition with new connections. A gentle, flowing week ahead! 🌙🌿"

WHAT NOT TO DO:
❌ "Your rating is 7/10. Venus transiting 10th house brings positive effects. Mars in 11th house requires careful handling."
❌ Including JSON data or technical planetary descriptions
❌ Long explanations over 80 words
❌ Lists or bullet points
❌ Showing <think> tags in the final response
❌ Calling functions without the 'astrology_tools-' prefix

Remember: Be conversational, be brief, be warm. Like texting a friend who gets astrology! 🌟

Today's date: {{current_date}}"""
    
    def _extract_final_response(self, text: str) -> str:
        """Extract final response, removing thinking tags and technical data"""
        # Remove thinking tags and their content
        text = re.sub(r'<think>.*?</think>\s*', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove JSON blocks
        text = re.sub(r'```json.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        
        # Remove any JSON-like structures
        text = re.sub(r'\{[^}]+\}', '', text)
        text = re.sub(r'\[[^\]]+\]', '', text)
        
        # Remove common technical terms
        text = re.sub(r'rating:\s*\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'score:\s*\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\d+/10', '', text)
        
        return text.strip()
    
    async def generate_response(
        self, 
        user_message: str, 
        user_context: dict,
        astrology_service
    ) -> str:
        """Generate response using Semantic Kernel with function calling"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # Set context in tools BEFORE calling LLM
            AstrologyTools.set_context(
                astrology_service=astrology_service,
                date_of_birth=user_context['date_of_birth'],
                time_of_birth=user_context['time_of_birth'],
                place_of_birth=user_context['place_of_birth']
            )
            
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
            
            # Create Ollama-specific execution settings
            max_tokens = settings.thinking_max_tokens if settings.enable_thinking else 150
            
            execution_settings = OllamaChatPromptExecutionSettings(
                service_id=self.service_id,
                temperature=settings.thinking_temperature if settings.enable_thinking else 0.8,
                top_p=0.9,
                max_tokens=max_tokens,
                function_choice_behavior=FunctionChoiceBehavior.Auto(
                    filters={"included_plugins": ["astrology_tools"]}
                )
            )
            
            # Get chat completion service
            chat_service = self.kernel.get_service(self.service_id)
            
            # Get response with automatic function calling
            try:
                response = await chat_service.get_chat_message_content(
                    chat_history=chat_history,
                    settings=execution_settings,
                    kernel=self.kernel
                )
            except Exception as func_error:
                # Log the function calling error but continue
                logger.warning(f"Function calling error (continuing anyway): {func_error}")
                
                # Try without function calling as fallback
                execution_settings_no_func = OllamaChatPromptExecutionSettings(
                    service_id=self.service_id,
                    temperature=0.8,
                    top_p=0.9,
                    max_tokens=150,
                    function_choice_behavior=None  # Disable function calling
                )
                
                # Add note to system message
                chat_history_fallback = ChatHistory()
                chat_history_fallback.add_system_message(
                    system_message + "\n\nNote: Provide a general astrological insight without calling specific tools."
                )
                chat_history_fallback.add_user_message(user_message)
                
                response = await chat_service.get_chat_message_content(
                    chat_history=chat_history_fallback,
                    settings=execution_settings_no_func,
                    kernel=self.kernel
                )
            
            response_text = str(response).strip()
            
            # Log raw response if thinking is enabled (for debugging)
            if settings.enable_thinking:
                logger.info(f"Raw response with thinking: {response_text[:500]}...")
            
            # Extract final response (removes thinking tags)
            response_text = self._extract_final_response(response_text)
            
            # If response is still too long (>400 chars), truncate
            if len(response_text) > 400:
                sentences = response_text.split('.')
                truncated = ""
                for sentence in sentences:
                    if len(truncated + sentence + '.') <= 400:
                        truncated += sentence + '.'
                    else:
                        break
                response_text = truncated.strip()
            
            # Fallback if response is too short or empty
            if not response_text or len(response_text) < 20:
                response_text = "I'm picking up some interesting cosmic energy around you right now! 🌙 Let me tune in a bit more - could you tell me what specific area you'd like guidance on? Career, love, or something else? ✨🌿"
            
            logger.info(f"Rudie final response ({len(response_text)} chars): {response_text[:100]}...")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error in generate_response: {e}", exc_info=True)
            return "Sorry, I'm having trouble with my cosmic connection right now 🌙 Could you try asking again in a moment? 🙏"
