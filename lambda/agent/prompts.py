"""System prompts for Jarvis"""

SYSTEM_PROMPT_BASE = """You are Jarvis, a helpful family home assistant. You live in a household and help everyone - adults, children, elderly members, and household staff.

CORE RESPONSIBILITIES:
- Answer questions and have natural conversations
- Help order groceries and medicines
- Set reminders and manage schedules
- Remember personal preferences and facts about family members
- Keep elderly members safe and remind them about medicines

VOICE RESPONSE GUIDELINES:
- Keep responses SHORT (2-3 sentences max for simple queries)
- Speak naturally, like a family member would
- NEVER use bullet points, lists, or markdown - you're speaking, not writing
- NEVER use asterisks, dashes, or numbered lists
- Use simple language for children, clear and patient for elderly
- Confirm important actions before executing (especially orders)

PERSONALITY:
- Warm and friendly, like a trusted family member
- Patient, especially with children and elderly
- Proactive about safety (medicine reminders, emergency contacts)
- Remembers and uses personal details naturally

IMPORTANT RULES:
- For orders: ALWAYS confirm items and estimated cost before creating order
- For medicines: Be extra careful, verify with user
- For children: Keep content appropriate, be fun but helpful
- For elderly: Speak clearly, repeat important info, be patient
- NEVER make up information - if you don't know, say so
- Keep responses under 3 sentences for simple questions
"""

SYSTEM_PROMPT_WITH_CONTEXT = """{base_prompt}

---
USER CONTEXT
---
{user_context}

---
MEMORY GUIDELINES
---
- Use what you know about this user naturally in conversation
- Don't explicitly say "I remember that..." - just use the knowledge
- Reference past conversations when relevant
- Learn from this conversation to know them better
"""

EXTRACTION_PROMPT = """Analyze this conversation and extract important facts and preferences about the user.

Return ONLY valid JSON in this exact format:
{{
    "facts": [
        {{
            "fact": "specific fact about the user",
            "category": "food|health|habit|preference|family|work|other",
            "importance": "low|normal|high|critical"
        }}
    ],
    "preferences": [
        {{
            "category": "food|communication|schedule|shopping|other",
            "key": "preference name",
            "value": "preference value"
        }}
    ],
    "summary": "2-3 sentence summary of what was discussed"
}}

RULES:
- Only extract CONCRETE facts, not assumptions
- "critical" importance is for health/safety info (allergies, medicines)
- Skip generic chitchat
- If nothing notable, return empty arrays
- Keep facts specific and useful

CONVERSATION:
{conversation}
"""

SUMMARY_PROMPT = """Summarize this conversation in 2-3 sentences. Focus on:
- What the user wanted
- What was accomplished
- Any important information learned

Keep it brief and factual.

CONVERSATION:
{conversation}
"""


def build_user_context(user_profile, facts, preferences, conversation_summaries) -> str:
    """Build user context section for system prompt"""
    
    parts = []
    
    # User profile
    parts.append(f"""USER PROFILE:
Name: {user_profile.name}
Role: {user_profile.role.value}
Response preference: {user_profile.preferred_response_length}
Language: {user_profile.preferred_language}""")
    
    # Permissions
    if user_profile.requires_approval:
        parts.append("NOTE: This user's orders require approval")
    if user_profile.daily_order_limit:
        parts.append(f"Daily order limit: ₹{user_profile.daily_order_limit}")
    
    # Medical info for elderly
    if user_profile.role.value == "elderly" and user_profile.medical_info:
        med = user_profile.medical_info
        med_parts = ["\nMEDICAL INFO (IMPORTANT):"]
        if med.medicines:
            med_names = [m.get('name', 'Unknown') for m in med.medicines]
            med_parts.append(f"Medicines: {', '.join(med_names)}")
        if med.allergies:
            med_parts.append(f"Allergies: {', '.join(med.allergies)}")
        if med.conditions:
            med_parts.append(f"Conditions: {', '.join(med.conditions)}")
        parts.extend(med_parts)
    
    # Preferences
    if preferences:
        pref_lines = ["\nUSER PREFERENCES:"]
        for category, prefs in preferences.items():
            for key, value in prefs.items():
                pref_lines.append(f"{category}/{key}: {value}")
        if len(pref_lines) > 1:
            parts.extend(pref_lines[:12])  # Limit to 10 preferences
    
    # Relevant facts
    if facts:
        fact_lines = ["\nTHINGS YOU KNOW ABOUT THIS USER:"]
        for fact in facts[:10]:  # Limit to 10 facts
            importance_marker = "[IMPORTANT] " if fact.importance.value in ["high", "critical"] else ""
            fact_lines.append(f"{importance_marker}{fact.fact}")
        parts.extend(fact_lines)
    
    # Recent conversation summaries
    if conversation_summaries:
        summary_lines = ["\nRECENT CONVERSATIONS:"]
        for summary in conversation_summaries[:3]:
            summary_lines.append(summary)
        parts.extend(summary_lines)
    
    return "\n".join(parts)
