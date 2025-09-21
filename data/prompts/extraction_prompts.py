# data/prompts/extraction_prompts.py

EXTRACTION_PROMPTS = {
    "founders": """
    Extract founder information from the following text. Look for:
    - Names of founders/co-founders
    - Previous work experience (especially "ex-" companies)
    - Educational background
    - Years of experience
    - Roles and responsibilities
    
    Text: {text}
    
    Return JSON in this format:
    {{
        "founders": [
            {{
                "name": "Founder Name",
                "background": "Brief background description",
                "experience_years": number,
                "previous_companies": ["Company1", "Company2"],
                "education": "University/Degree",
                "role": "CEO/CTO/etc"
            }}
        ]
    }}
    """,
    
    "market": """
    Extract market size and opportunity information from the following text:
    
    Text: {text}
    
    Look for:
    - TAM (Total Addressable Market)
    - SAM (Serviceable Addressable Market) 
    - SOM (Serviceable Obtainable Market)
    - Market growth rates
    - Target market description
    
    Return JSON in this format:
    {{
        "tam": number or null,
        "sam": number or null,
        "som": number or null,
        "target_market": "description",
        "market_growth_rate": number or null,
        "market_trends": ["trend1", "trend2"]
    }}
    """,
    
    "traction": """
    Extract traction and growth metrics from the following text:
    
    Text: {text}
    
    Look for:
    - MRR (Monthly Recurring Revenue)
    - ARR (Annual Recurring Revenue)
    - CAC (Customer Acquisition Cost)
    - LTV (Lifetime Value)
    - Churn rate
    - User/customer counts
    - Growth rates
    
    Return JSON in this format:
    {{
        "mrr": number or null,
        "arr": number or null,
        "cac": number or null,
        "ltv": number or null,
        "churn_rate": number or null,
        "user_count": number or null,
        "customer_count": number or null,
        "growth_rate": number or null,
        "key_metrics": ["metric1: value", "metric2: value"]
    }}
    """,
    
    "financials": """
    Extract financial information from the following text:
    
    Text: {text}
    
    Look for:
    - Current revenue
    - Burn rate
    - Funding requested
    - Valuation
    - Runway (months)
    - Previous funding rounds
    
    Return JSON in this format:
    {{
        "revenue": number or null,
        "burn_rate": number or null,
        "funding_requested": number or null,
        "valuation": number or null,
        "runway_months": number or null,
        "previous_funding": [
            {{
                "round": "Seed/Series A/etc",
                "amount": number,
                "date": "YYYY-MM-DD",
                "investors": ["Investor1", "Investor2"]
            }}
        ]
    }}
    """,
    
    "company_basics": """
    Extract basic company information from the following text:
    
    Text: {text}
    
    Look for:
    - Company name
    - Problem being solved
    - Solution description
    - Competitors mentioned
    - Technology stack
    
    Return JSON in this format:
    {{
        "company_name": "Company Name",
        "problem_statement": "Clear problem description",
        "solution_description": "How they solve the problem",
        "competitors": ["Competitor1", "Competitor2"],
        "technology": ["Tech1", "Tech2"],
        "business_model": "B2B/B2C/Marketplace/etc"
    }}
    """
}
