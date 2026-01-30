"""
Jarvis - Smart Home AI Assistant
AWS Lambda handler for Alexa Skills Kit
"""
import logging
import json
from typing import Optional

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler,
    AbstractExceptionHandler
)
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

from agent.core import JarvisAgent
from agent.config import settings

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Global agent instance (reused across Lambda invocations)
_agent: Optional[JarvisAgent] = None


def get_agent() -> JarvisAgent:
    """Get or create agent instance"""
    global _agent
    if _agent is None:
        _agent = JarvisAgent()
    return _agent


# ============================================
# REQUEST HANDLERS
# ============================================

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch"""
    
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("LaunchRequest")(handler_input)
    
    def handle(self, handler_input: HandlerInput) -> Response:
        logger.info("LaunchRequest received")
        
        # Get session info
        session = handler_input.request_envelope.session
        user_id = session.user.user_id if session and session.user else settings.default_user_id
        session_id = session.session_id if session else None
        
        # Start agent session
        agent = get_agent()
        agent.start_session(user_id=user_id, alexa_session_id=session_id)
        
        # Get personalized greeting
        greeting = agent.get_greeting()
        
        return (
            handler_input.response_builder
                .speak(greeting)
                .ask("What would you like help with?")
                .response
        )


class CatchAllIntentHandler(AbstractRequestHandler):
    """Handler for CatchAll Intent - Main conversational handler"""
    
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("CatchAllIntent")(handler_input)
    
    def handle(self, handler_input: HandlerInput) -> Response:
        # Get user utterance
        slots = handler_input.request_envelope.request.intent.slots
        user_input = ""
        
        if slots and "utterance" in slots and slots["utterance"].value:
            user_input = slots["utterance"].value
        
        logger.info(f"CatchAllIntent: {user_input}")
        
        if not user_input:
            return (
                handler_input.response_builder
                    .speak("I didn't catch that. What would you like?")
                    .ask("You can ask me about weather, set reminders, or manage your grocery list.")
                    .response
            )
        
        # Get session info
        session = handler_input.request_envelope.session
        user_id = session.user.user_id if session and session.user else settings.default_user_id
        session_id = session.session_id if session else None
        is_new = session.new if session else True
        
        # Get agent and ensure session is started
        agent = get_agent()
        if is_new or not agent.current_user:
            agent.start_session(user_id=user_id, alexa_session_id=session_id)
        
        # Process with agent
        try:
            response_text = agent.process(user_input)
        except Exception as e:
            logger.error(f"Agent error: {e}")
            response_text = "Sorry, I had trouble processing that. Please try again."
        
        return (
            handler_input.response_builder
                .speak(response_text)
                .ask("Anything else?")
                .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent"""
    
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.HelpIntent")(handler_input)
    
    def handle(self, handler_input: HandlerInput) -> Response:
        speak_output = (
            "I'm Jarvis, your home assistant. I can help you with: "
            "checking the weather, setting reminders, managing your grocery list, "
            "doing calculations, and answering questions. Just ask!"
        )
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("What would you like help with?")
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Handler for Cancel and Stop Intents"""
    
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return (
            is_intent_name("AMAZON.CancelIntent")(handler_input) or
            is_intent_name("AMAZON.StopIntent")(handler_input)
        )
    
    def handle(self, handler_input: HandlerInput) -> Response:
        # End agent session
        agent = get_agent()
        try:
            agent.end_session(extract_learnings=True)
        except Exception as e:
            logger.error(f"Error ending session: {e}")
        
        return (
            handler_input.response_builder
                .speak("Goodbye! Talk to you later.")
                .set_should_end_session(True)
                .response
        )


class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for Fallback Intent"""
    
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)
    
    def handle(self, handler_input: HandlerInput) -> Response:
        speech = "I didn't understand that. Could you please rephrase?"
        
        return (
            handler_input.response_builder
                .speak(speech)
                .ask(speech)
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End"""
    
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("SessionEndedRequest")(handler_input)
    
    def handle(self, handler_input: HandlerInput) -> Response:
        logger.info("Session ended")
        
        # End agent session and extract learnings
        agent = get_agent()
        try:
            agent.end_session(extract_learnings=True)
        except Exception as e:
            logger.error(f"Error ending session: {e}")
        
        return handler_input.response_builder.response


# ============================================
# EXCEPTION HANDLERS
# ============================================

class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling"""
    
    def can_handle(self, handler_input: HandlerInput, exception: Exception) -> bool:
        return True
    
    def handle(self, handler_input: HandlerInput, exception: Exception) -> Response:
        logger.error(f"Exception: {exception}", exc_info=True)
        
        speak_output = "Sorry, I encountered an error. Please try again."
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("What would you like to do?")
                .response
        )


# ============================================
# SKILL BUILDER
# ============================================

sb = SkillBuilder()

# Register handlers
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(CatchAllIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

# Register exception handlers
sb.add_exception_handler(CatchAllExceptionHandler())

# Lambda handler
lambda_handler = sb.lambda_handler()
