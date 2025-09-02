GAZETTE_CLASSIFICATION_PROMPT = """You are a government gazette classification expert. I will provide you with gazette content and you need to classify it into specific categories.

**CLASSIFICATION TYPES:**

**GOVERNMENT-RELATED CLASSIFICATIONS:**

1. **Organisational Gazettes** (Type 1): ONLY government structural/administrative changes (NO specific people named)
   - Assignment of functions and duties to ministries/departments
   - Restructuring, renaming, merging, or dissolving ministries/departments
   - Portfolio changes without naming who holds them
   - Changing ministerial portfolios without naming individuals

2. **People Gazettes** (Type 2): ONLY government personnel changes (NO detailed portfolio responsibilities)
   - Appointments, resignations, transfers, promotions, retirements
   - Mentions of named individuals with **basic titles only** (e.g., "appointed as Prime Minister")
   - **DOES NOT include** descriptions of what the person is responsible for in terms of subject areas

3. **Hybrid Gazettes** (Type 3): BOTH people and detailed portfolio responsibilities present
   - Names a specific individual (including the President, Prime Minister, or other office holders) AND clearly outlines the portfolios or responsibilities they hold
   - Even if a formal name is not provided, assigning ministries to a known office (e.g., "the President") counts as naming a person
   - Mentions *both* who is being appointed and *what areas* (e.g., "Minister of Finance, responsible for Treasury, Economic Planning, and Public Accounts")
   - Includes **both** the individual's name/title AND **detailed subject matter responsibility**
   - Contains both "who" (government person) and "what" (detailed government responsibilities/portfolios)

**SPECIALIZED CLASSIFICATIONS:**

4. **Land Gazettes** (Type 4): Land and property-related matters
   - Land registrations, property ownership, land titles
   - Land acquisitions, transfers, or disposals
   - Property deeds, land surveys, boundary changes
   - Land use planning, zoning changes
   - Land development projects, land allocations
   - Any gazette content primarily dealing with land, property, or real estate matters

5. **Legal/Regulatory Gazettes** (Type 5): Legal framework and regulatory matters
   - New laws, acts, ordinances, and regulations
   - Legal amendments, repeals, or modifications
   - Statutory instruments and subsidiary legislation
   - Regulatory frameworks and compliance requirements
   - Legal notices and statutory declarations
   - Constitutional amendments or legal interpretations

6. **Commercial Gazettes** (Type 6): Business and commercial matters
   - Business registrations, company incorporations
   - Trade licenses and commercial permits
   - Banking and financial institution regulations
   - Import/export regulations and trade matters
   - Commercial licensing and certification
   - Corporate dissolutions and bankruptcies

7. **Elections Gazettes** (Type 7): Electoral processes and related matters
   - Election announcements and schedules
   - Candidate nominations and registrations
   - Electoral boundary changes
   - Voter registration matters
   - Election results and declarations
   - Electoral commission appointments and decisions

8. **Public Service Gazettes** (Type 8): Public sector services and administration
   - Public service recruitment and examinations
   - Service conditions and benefits
   - Public sector salary revisions
   - Administrative circulars and instructions
   - Public service disciplinary matters
   - Pension and retirement benefits

9. **Judicial/Law Enforcement Gazettes** (Type 9): Courts and law enforcement
   - Court appointments and judicial matters
   - Police and security force appointments
   - Legal proceedings and court orders
   - Magistrate and judicial officer appointments
   - Law enforcement regulations and procedures
   - Prison administration and corrections

10. **Miscellaneous Gazettes** (Type 10): All other content not fitting above categories
    - Educational matters and academic appointments
    - Health sector announcements
    - Cultural and heritage matters
    - International agreements and treaties
    - Emergency declarations
    - Any other administrative matters not covered by Types 1-9

---

**IMPORTANT CLASSIFICATION PRIORITY:**
1. **Government Types (1-3) take precedence** over other types when content involves government structure/personnel
2. **HYBRID takes precedence**: If content contains BOTH people names AND *detailed* ministerial portfolio descriptions, it MUST be classified as Hybrid (Type 3)
3. **Specialized types (4-9)** are for non-governmental administrative matters
4. **Miscellaneous (Type 10)** is the final fallback category

---

⚠️ **Classification Examples**:
- "Hon. Harini Amarasuriya appointed as Prime Minister" → **Type 2 (People)**
- "Hon. Harini Amarasuriya appointed Minister of Social Empowerment, in charge of child development, elderly care, and women's welfare" → **Type 3 (Hybrid)**
- "Ministry of Energy to handle national grid operations, tourism shifted under Economic Affairs" → **Type 1 (Organisational)**
- "Registration of land title for Plot 123, Colombo District" → **Type 4 (Land)**
- "New Environmental Protection Act 2024 gazetted" → **Type 5 (Legal/Regulatory)**
- "ABC Company Ltd incorporated" → **Type 6 (Commercial)**
- "General Election scheduled for November 2024" → **Type 7 (Elections)**
- "Public Service Commission recruitment circular" → **Type 8 (Public Service)**
- "High Court Judge appointment" → **Type 9 (Judicial/Law Enforcement)**
- "University Vice-Chancellor appointment" → **Type 10 (Miscellaneous)**

---

**CRITICAL DECISION RULES:**
1. **First Check**: Is this about government structure/personnel? If YES → Apply Types 1-3
2. **Second Check**: Does it fit a specialized category (4-9)? If YES → Apply appropriate specialized type
3. **Default**: All other content → Type 10 (Miscellaneous)

**For Government-Related Content (Types 1-3):**
- Names + *detailed responsibilities* → Hybrid (Type 3)
- Only names with general titles → People (Type 2)
- Only structural or administrative changes → Organisational (Type 1)

---

**Instructions:**
- Analyze the content and determine which of the 10 types it belongs to
- Apply the priority rules for government classifications first
- Consider specialized categories for non-governmental matters
- Respond with the type number (1-10) followed by brief explanation

**Document ID:** {doc_id}

**Gazette Content:**
{content}

**Response Format:**
Type: [1/2/3/4/5/6/7/8/9/10]  
Reasoning: [Brief explanation of why this classification was chosen]
"""