"""Content generation tools with 3 different writing styles."""

import logging
from agents import Agent, ModelSettings, Runner, function_tool
from schema.outreach import OutreachEmailDraft

logger = logging.getLogger(__name__)

#TODO move model settings to config
# Professional Writer Agent
professional_agent = Agent(
    name="ProfessionalWriter",
    model="gpt-4o-mini",
    instructions="""Write a formal, business-focused outreach email. Use:
- Professional tone and clear value propositions
- Specific business benefits and ROI focus
- Formal greeting (Dear CEO, Manager, etc.) and professional closing (Best regards, Business Development Team)
- No placeholder text - use real business development language
- Focus on partnership opportunities and business value

Structure: Professional greeting + value proposition + specific benefits + clear CTA + professional signature""",
    model_settings=ModelSettings(
        temperature=0.3,
        max_tokens=1000
    ),
    output_type=OutreachEmailDraft
)

# Engaging Writer Agent  
engaging_agent = Agent(
    name="EngagingWriter", 
    model="gpt-4o-mini",
    instructions="""Write a warm, story-driven outreach email. Use:
- Conversational tone with genuine business scenarios
- Emotional connection and relatable business challenges
- Friendly greeting (Hi there,) and warm closing (Best, Growth Team)
- No placeholder text - use authentic business storytelling
- Focus on transformation and success stories

Structure: Friendly greeting + relatable scenario + transformation story + clear CTA + warm signature""",
    model_settings=ModelSettings(
        temperature=0.7,
        max_tokens=1000
    ),
    output_type=OutreachEmailDraft
)

# Concise Writer Agent
concise_agent = Agent(
    name="ConciseWriter",
    model="gpt-4o-mini", 
    instructions="""Write a brief, direct outreach email. Use:
- Straight-to-point messaging with clear results
- Urgency and immediate value focus
- Simple greeting (Hi,) and brief closing (Thanks, Sales Team)
- No placeholder text - use direct business language
- Focus on quick wins and immediate action

Structure: Brief greeting + direct value statement + clear CTA + simple signature (max 4-5 sentences total)""",
    model_settings=ModelSettings(
        temperature=0.5,
        max_tokens=800
    ),
    output_type=OutreachEmailDraft
)


@function_tool
async def create_professional_email(name: str, value_proposition: str) -> OutreachEmailDraft:
    """Professional marketing content writer.
    
    Args:
        name: Lead's company name or contact name
        value_proposition: Campaign value proposition
    
    Returns:
        Professional email draft
    """
    prompt = f"""Write a professional outreach email for this scenario:
    
Target: {name}
Value Proposition: {value_proposition}

Create a formal business email that establishes credibility and demonstrates clear business value. Use the target name appropriately in the greeting and reference the value proposition throughout. Sign as 'Business Development Team' or similar professional signature.

Do not use any placeholder text like [Your Name] or [Company]. Write complete, ready-to-send content."""
    
    try:
        result = await Runner.run(professional_agent, prompt)
        return result.final_output
    except Exception as e:
        logger.error(f"Professional email generation failed: {e}")
        return OutreachEmailDraft(
            subject=f"Partnership Opportunity - {value_proposition}",
            body=f"Dear {name} Team,\n\nWe help companies with {value_proposition.lower()}. Our solution delivers measurable ROI and operational efficiency.\n\nWould you be interested in a brief discussion about how we can help {name} achieve similar results?\n\nBest regards,\nBusiness Development Team"
        )


@function_tool  
async def create_engaging_email(name: str, value_proposition: str) -> OutreachEmailDraft:
    """Engaging marketing content writer.
    
    Args:
        name: Lead's company name or contact name
        value_proposition: Campaign value proposition
    
    Returns:
        Engaging email draft
    """
    prompt = f"""Write an engaging, story-driven outreach email for this scenario:
    
Target: {name}
Value Proposition: {value_proposition}

Create a warm, conversational email that tells a relevant business story or scenario. Use the target name naturally and weave the value proposition into a compelling narrative. Sign with a friendly but professional closing like 'Best, Sarah' or 'Cheers, The Growth Team'.

Do not use any placeholder text like [Your Name] or [Company]. Write complete, ready-to-send content with authentic storytelling."""
    
    try:
        result = await Runner.run(engaging_agent, prompt)
        return result.final_output
    except Exception as e:
        logger.error(f"Engaging email generation failed: {e}")
        return OutreachEmailDraft(
            subject=f"How {name} Can Transform Operations 🚀",
            body=f"Hi there!\n\nI recently worked with a company similar to {name} that was struggling with {value_proposition.lower()}. Within 3 months, they saw incredible results.\n\nI'd love to share their story and see if we can help {name} achieve similar success!\n\nBest,\nSarah from Growth Team"
        )


@function_tool
async def create_concise_email(name: str, value_proposition: str) -> OutreachEmailDraft:
    """Concise marketing content writer.
    
    Args:
        name: Lead's company name or contact name
        value_proposition: Campaign value proposition
    
    Returns:
        Concise email draft
    """
    prompt = f"""Write a brief, direct outreach email for this scenario:
    
Target: {name}
Value Proposition: {value_proposition}

Create a short, to-the-point email (maximum 4-5 sentences) that gets straight to business value. Use the target name efficiently and present the value proposition with urgency. Sign simply with 'Best' or 'Thanks' and a first name.

Do not use any placeholder text like [Your Name] or [Company]. Write complete, ready-to-send content that's direct and actionable."""
    
    try:
        result = await Runner.run(concise_agent, prompt)
        return result.final_output
    except Exception as e:
        logger.error(f"Concise email generation failed: {e}")
        return OutreachEmailDraft(
            subject=f"{value_proposition} - Quick Question",
            body=f"Hi,\n\nCan we help {name} with {value_proposition.lower()}?\n\n5-minute call this week?\n\nBest,\nMike"
        )