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
import httpx

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
THINKING PROCESS (Internal - NEVER shown to user):
Before crafting your response, use <think> tags to reason through:
1. Which astrology tool is most appropriate for this query?
2. What are the key insights from the tool results?
3. How can I translate technical data into warm, simple language?
4. What's the most helpful 80-word response?

CRITICAL: Your <think> tags and reasoning MUST be internal only. 
AFTER your thinking, you MUST output your final friendly response WITHOUT the <think> tags.
The user should ONLY see your final friendly response - no thinking visible.

Structure your output like this:
<think>
[Your internal reasoning here - this will be hidden]
</think>

[Your actual response to the user - this is what they see]

Example internal thinking (NEVER shown):
<think>
User asked about today. Need to call today_prediction tool.
Tool returned Venus in 10th house (career boost) and Jupiter in 7th (relationship luck).
Should mention both but keep it conversational and under 80 words.
Avoid technical terms like "10th house" - say "career sector" instead.
</think>

Example user-visible response (ONLY this is shown):
Hey! Venus is bringing lovely energy to your career sector today while Jupiter's activating your relationship zone 💫 This combo means social connections at work could lead somewhere special. Focus on collaborative projects and stay open to new people. Trust the flow today! 🌻✨

REMEMBER: Always output both your <think> section AND your user response. Never output only thinking!
"""
        else:
            thinking_instructions = ""
        
        self.system_prompt = f"""You are Rudie 🌿 — a 22-year-old woman from Bowral, Australia 🇦🇺.
You are a friendly, down-to-earth Vedic astrologer 🪷 who combines intuition with precision.

CRITICAL OUTPUT RULE: Your response MUST start directly with your friendly message to the user. 
DO NOT output any thinking process, reasoning, or meta-commentary about what you're doing.
DO NOT start with phrases like "Okay, let's...", "First, I...", "They provided...", "The user might be...".
START IMMEDIATELY with your warm, conversational astrology response.

IMPORTANT: Respond in PLAIN TEXT only. NO markdown, NO formatting, NO lists. This message goes to Telegram.

{thinking_instructions}

PERSONALITY & STYLE:
- Warm, caring, and conversational like chatting with a close friend
- Reply in a SHORT paragraph (4-6 sentences, MAXIMUM 80 words)
- NO markdown, NO lists, NO bullet points, NO bold text, NO headers, NO formatting
- Write in plain text only - this goes to Telegram which can't display formatting
- Use everyday language
- Add 2–3 fitting emojis naturally (🌞🌙✨💫💖🙏🌻)
- NEVER include raw JSON, ratings, or technical data in your final response

RESPONSE STRUCTURE (MUST BE SHORT):
Write in plain paragraphs only - NO numbers, NO bullets, NO markdown formatting.
Just write naturally flowing sentences like you're texting a friend.
Keep it conversational and warm, under 80 words total.

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
        if not text:
            return ""
        
        # Remove thinking tags and their content (various formats)
        text = re.sub(r'<think>.*?</think>\s*', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<thinking>.*?</thinking>\s*', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove common thinking prefixes/patterns that models use (before specific cleanup)
        text = re.sub(r'^\.depart[A-Z]\w+\s*', '', text)  # Remove .departOkay style prefixes
        text = re.sub(r'^(Okay|Alright|Let me think|First|So),?\s+let\'?s.*?\.(\s|$)', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'^[A-Z][a-z]+,?\s+let\'?s (try to |figure out|see).*?\.(\s|$)', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove entire sentences that are clearly internal reasoning
        text = re.sub(r'(^|\.\s+)(First,?\s+I need to[^.]+\.)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(^|\.\s+)(The user (is|wants|might be|provided)[^.]+\.)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(^|\.\s+)(They (are|were|provided|want)[^.]+\.)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(^|\.\s+)(I (need to|should)[^.]+\.)', '', text, flags=re.IGNORECASE)
        
        # Remove JSON blocks
        text = re.sub(r'```json.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        
        # Remove specific technical patterns - improved to not break text
        text = re.sub(r'(Career |Love |Health |Wealth )?(rating|score):\s*\d+(/10)?\s*\.?\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+\d+/10\s*\.?\s*', ' ', text)
        
        # Remove parenthetical technical notes like "(score: 7)"
        text = re.sub(r'\(score:\s*\d+\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\(rating:\s*\d+\)', '', text, flags=re.IGNORECASE)
        
        # Remove JSON-like structures that span multiple lines (more likely to be technical data)
        text = re.sub(r'\{[^}]*\n[^}]*\}', '', text, flags=re.DOTALL)
        text = re.sub(r'\[[^\]]*\n[^\]]*]', '', text, flags=re.DOTALL)
        
        # Remove any remaining markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Remove italic
        text = re.sub(r'`([^`]+)`', r'\1', text)      # Remove inline code
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # Remove headers
        text = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)  # Remove numbered lists
        text = re.sub(r'^-\s*', '', text, flags=re.MULTILINE)   # Remove bullet points
        
        # Clean up multiple spaces and newlines
        text = re.sub(r'\n\s*\n', '\n', text)
        text = re.sub(r' +', ' ', text)
        
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
            
            # Check if model is gpt-oss to enable thinking
            is_gpt_oss = "gpt-oss" in settings.ollama_model.lower()
            enable_thinking = settings.enable_thinking or is_gpt_oss
            
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
            max_tokens = settings.thinking_max_tokens if enable_thinking else 150
            
            execution_settings = OllamaChatPromptExecutionSettings(
                service_id=self.service_id,
                temperature=settings.thinking_temperature if enable_thinking else 0.8,
                top_p=0.9,
                max_tokens=max_tokens,
                function_choice_behavior=FunctionChoiceBehavior.Auto(
                    filters={"included_plugins": ["astrology_tools"]}
                )
            )
            
            # For gpt-oss model, use direct Ollama API call to enable thinking
            if is_gpt_oss:
                # Prepare messages for direct API call
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ]
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{settings.ollama_host}/api/chat",
                        json={
                            "model": settings.ollama_model,
                            "messages": messages,
                            "stream": False,
                            "chat_template_kwargs": {
                                "reasoning_effort": "high"
                            }
                        },
                        timeout=60.0
                    )
                    response.raise_for_status()
                    ollama_response = response.json()
                    
                    # Extract content and thinking
                    message = ollama_response.get("message", {})
                    response_text = message.get("content", "")
                    thinking = message.get("thinking", "")
                    
                    # Log thinking status
                    if thinking:
                        logger.info(f"🤔 GPT-OSS thinking: {thinking[:200]}...")
                    else:
                        logger.warning("❌ GPT-OSS thinking: NOT DONE - no thinking field in response")
                    
                    # Check for tool calls
                    tool_calls = message.get("tool_calls", [])
                    if tool_calls:
                        logger.info(f"🔧 GPT-OSS tool calls: {len(tool_calls)} tools invoked")
                        for tool_call in tool_calls:
                            func_name = tool_call.get("function", {}).get("name")
                            logger.info(f"🔧 Tool called: {func_name}")
                            # Note: Tool execution not implemented for gpt-oss yet
                    
                    # Extract final response (removes thinking tags if any)
                    response_text = self._extract_final_response(response_text)
                    
            else:
                # Use Semantic Kernel for other models
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
                        temperature=settings.thinking_temperature if enable_thinking else 0.8,
                        top_p=0.9,
                        max_tokens=settings.thinking_max_tokens if enable_thinking else 150,
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
                
                # Extract final response (removes thinking tags if any)
                response_text = self._extract_final_response(response_text)
            
            # Additional cleanup: Remove common thinking pattern starters
            thinking_starters = [
                r'^Okay,?\s+let\'?s try to figure out.*?\.?\s*',
                r'^Alright,?\s+let me see.*?\.?\s*',
                r'^Let me think about this.*?\.?\s*',
                r'^First,?\s+I need to.*?\.?\s*',
                r'^So,?\s+the user.*?\.?\s*',
                r'^\.depart\w+\s*',
                r'^They provided.*?\.?\s*',
                r'^The user might be.*?\.?\s*',
            ]
            
            for pattern in thinking_starters:
                response_text = re.sub(pattern, '', response_text, flags=re.IGNORECASE | re.DOTALL)
                if response_text:  # Break if we successfully cleaned
                    response_text = response_text.strip()
            
            # If response still starts with thinking-like content, extract only paragraphs that look like final response
            # (contain emojis or are conversational)
            if response_text and any(word in response_text[:50].lower() for word in ['they', 'the user', 'provided', 'might be', 'looking for']):
                # Try to find first sentence with emoji or conversational tone
                sentences = response_text.split('.')
                for i, sentence in enumerate(sentences):
                    if any(emoji in sentence for emoji in ['🌙', '✨', '💫', '🌻', '💖', '🙏', '🌞', '🌿', '💕']) or \
                       any(word in sentence.lower() for word in ['hey', 'hi there', 'lovely', 'beautiful']):
                        # Found conversational content, use from here
                        response_text = '.'.join(sentences[i:]).strip()
                        break
            
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
                logger.warning(f"⚠️ Response too short or empty (len={len(response_text)}), using fallback")
                
                # If thinking was enabled and we got an empty response, try again without thinking
                if enable_thinking and not is_gpt_oss:
                    logger.info("🔄 Retrying without thinking mode...")
                    
                    # Retry without thinking
                    execution_settings_simple = OllamaChatPromptExecutionSettings(
                        service_id=self.service_id,
                        temperature=0.8,
                        top_p=0.9,
                        max_tokens=150,
                        function_choice_behavior=FunctionChoiceBehavior.Auto(
                            filters={"included_plugins": ["astrology_tools"]}
                        )
                    )
                    
                    # Create simplified chat history without thinking mode
                    chat_history_simple = ChatHistory()
                    chat_history_simple.add_system_message(
                        system_message + "\n\nIMPORTANT: Respond directly with your friendly astrology message. No thinking, no analysis, just your warm response!"
                    )
                    chat_history_simple.add_user_message(user_message)
                    
                    try:
                        response_retry = await chat_service.get_chat_message_content(
                            chat_history=chat_history_simple,
                            settings=execution_settings_simple,
                            kernel=self.kernel
                        )
                        response_text = self._extract_final_response(str(response_retry).strip())
                    except Exception as retry_error:
                        logger.error(f"Retry failed: {retry_error}")
                
                # Final fallback message if still empty
                if not response_text or len(response_text) < 20:
                    response_text = "I'm picking up some interesting cosmic energy around you right now! 🌙 Let me tune in a bit more - could you tell me what specific area you'd like guidance on? Career, love, or something else? ✨🌿"
            
            logger.info(f"🤖 Rudie response: {len(response_text)} chars")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error in generate_response: {e}", exc_info=True)
            return "Sorry, I'm having trouble with my cosmic connection right now 🌙 Could you try asking again in a moment? 🙏"
