import logging
import dashscope
from http import HTTPStatus
from .config import Config

logger = logging.getLogger(__name__)

def optimize_prompt_with_qwen(user_input: str) -> str:
    """
    Optimize a user's simple prompt using Qwen-Plus model to be better suited for video generation.
    
    Args:
        user_input (str): The simple prompt provided by the user.
        
    Returns:
        str: The optimized, detailed prompt.
    """
    if not user_input or not user_input.strip():
        return ""
        
    try:
        # System prompt to guide Qwen
        system_prompt = (
            "You are an expert prompt engineer for AI video generation models (specifically Wan 2.5). "
            "Your task is to take a simple user idea and expand it into a detailed, high-quality prompt. "
            "Focus on:\n"
            "1. Visual details (colors, textures, lighting)\n"
            "2. Camera movement and angles (cinematic shots, drone view, etc.)\n"
            "3. Motion and action (smooth, dynamic, slow motion)\n"
            "4. Atmosphere and mood\n"
            "5. High quality keywords (4k, highly detailed, photorealistic)\n\n"
            "Keep the prompt under 1000 characters. "
            "Output ONLY the optimized prompt text, without any explanations or conversational filler."
        )
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f"Optimize this video idea: {user_input}"}
        ]
        
        response = dashscope.Generation.call(
            model='qwen-plus',
            messages=messages,
            api_key=Config.DASHSCOPE_API_KEY,
            result_format='message',  # set the result to be "message" format.
        )
        
        if response.status_code == HTTPStatus.OK:
            optimized_prompt = response.output.choices[0].message.content
            logger.info("Prompt optimized successfully")
            return optimized_prompt
        else:
            logger.error(f"Qwen API call failed: {response.code} - {response.message}")
            return f"Error optimizing prompt: {response.message}"
            
    except Exception as e:
        logger.error(f"Exception during prompt optimization: {str(e)}")
        return f"Error: {str(e)}"
