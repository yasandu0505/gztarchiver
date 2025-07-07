"""
Gazette classification utilities.
"""

def classify_gazette(description: str) -> str:
    """
    Classify gazette based on description content.
    Returns 'people', 'org', or 'unknown'.
    """
    desc = description.lower()
    
    # Person-specific changes
    people_keywords = [
        "appoint", "appointed", "appointment", "resign", "resignation", "relinquish",
        "portfolio", "minister of", "state minister of", "members of parliament",
        "secretary to", "held by", "removal", "m.p.", "cease", "hon.", "prime minister"
    ]
    
    # Org-specific keywords
    org_keywords = [
        "duties and functions", "subjects and functions", "assignment of subjects",
        "assigned to", "amendment", "correction notice", "extraordinary no.",
        "gazette extraordinary", "laws and ordinance", "departments", "projects and acts",
        "institutions", "statutory institutions", "public corporations", "ministries under the president",
        "functions and tasks", "gaz. ex.", "functions of the ministry"
    ]
    
    # Exception: if both org and person terms exist, and it's about transferring duties TO a person → it's likely "people"
    if any(p in desc for p in people_keywords):
        # But make sure it's not structural/organizational
        if any(org in desc for org in org_keywords):
            if "to the state minister" in desc or "state minister of" in desc:
                return "people"
            return "org"
        return "people"
    elif any(org in desc for org in org_keywords):
        return "org"
    else:
        return "unknown"