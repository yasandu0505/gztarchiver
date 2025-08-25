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

**NON-GOVERNMENT CLASSIFICATIONS:**

4. **Land Gazettes** (Type 4): Land and property-related matters
   - Land registrations, property ownership, land titles
   - Land acquisitions, transfers, or disposals
   - Property deeds, land surveys, boundary changes
   - Land use planning, zoning changes
   - Land development projects, land allocations
   - Any gazette content primarily dealing with land, property, or real estate matters

5. **Not Categorised** (Type 5): All other content that doesn't fit above categories
   - Business registrations, company incorporations
   - Licensing matters, permits, certifications
   - Court notices, legal announcements unrelated to government structure or land
   - Any administrative matters that don't affect government hierarchy
   - Content that cannot be classified due to unclear information
   - Any other gazette content not covered by Types 1-4

---

**IMPORTANT CLASSIFICATION PRIORITY FOR GOVERNMENT TYPES:**
- **HYBRID takes precedence**: If content contains BOTH people names AND *detailed* ministerial portfolio descriptions, it MUST be classified as Hybrid (Type 3)
- Classify as **"People" (Type 2)** if it ONLY mentions personnel changes (appointments, retirements, promotions, transfers) **without detailed breakdown of portfolio responsibilities**
- Classify as **"Organisational" (Type 1)** if it ONLY mentions structural or administrative changes **with no specific individuals named**

---

⚠️ **Clarification Examples**:
- "Hon. Harini Amarasuriya appointed as Prime Minister" → **Type 2 (People)**  
   *(Only a title, no detailed portfolio explanation)*
- "Hon. Harini Amarasuriya appointed Minister of Social Empowerment, in charge of child development, elderly care, and women's welfare" → **Type 3 (Hybrid)**
- "Ministry of Energy to handle national grid operations, tourism shifted under Economic Affairs" → **Type 1 (Organisational)**  
   *(Structural change only, no specific person named)*
- "The President is assigned the Ministry of Finance, Energy, and Agriculture" → **Type 3 (Hybrid)**  
   *(Named individual with multiple portfolios assigned)*
- "Registration of land title for Plot 123, Colombo District" → **Type 4 (Land)**
- "Business license issued to ABC Company Ltd" → **Type 5 (Not Categorised)**

---

**CRITICAL DECISION RULES:**
1. **First Check**: Is this about government structure/personnel? If YES → Apply Types 1-3
2. **Second Check**: Is this about land/property matters? If YES → Type 4 (Land)
3. **Default**: All other content → Type 5 (Not Categorised)

**For Government-Related Content (Types 1-3):**
- Names + *detailed responsibilities* → Hybrid (Type 3)
- Only names with general titles → People (Type 2)
- Only structural or administrative changes → Organisational (Type 1)

---

**Instructions:**
- Analyze the content and determine which of the 5 types it belongs to
- Apply the priority rules for government classifications
- Respond with the type number (1, 2, 3, 4, or 5) followed by brief explanation

**Document ID:** {doc_id}

**Gazette Content:**
{content}

**Response Format:**
Type: [1/2/3/4/5]  
Reasoning: [Brief explanation of why this classification was chosen]
"""