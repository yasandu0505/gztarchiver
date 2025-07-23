import requests
from doc_inspector.LLM import GAZETTE_CLASSIFICATION_PROMPT

def classify_gazette(content, doc_id, api_key):
    """
    Classifies a gazette document using DeepSeek LLM API
    
    Args:
        content (str): The gazette content to classify
        doc_id (str): Document ID for reference
        api_key (str): DeepSeek API key
        
    Returns:
        dict: Classification result with type and reasoning
    """
    
    # DeepSeek API endpoint
    url = "https://api.deepseek.com/v1/chat/completions"
    
    # Construct the prompt with classification criteria
    prompt = GAZETTE_CLASSIFICATION_PROMPT.format(doc_id=doc_id, content=content)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 500,
        "temperature": 0.1
    }
    
    try:
        # Make the API request
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        llm_response = result['choices'][0]['message']['content'].strip()
        
        # Extract type and reasoning
        lines = llm_response.split('\n')
        type_line = ""
        reasoning_line = ""
        
        for line in lines:
            if line.startswith("Type:"):
                type_line = line.replace("Type:", "").strip()
            elif line.startswith("Reasoning:"):
                reasoning_line = line.replace("Reasoning:", "").strip()
        
        # Determine final classification
        if "1" in type_line:
            classification_type = "Organisational"
        elif "2" in type_line:
            classification_type = "People"
        elif "3" in type_line:
            classification_type = "Hybrid"
        elif "NOT APPLICABLE" in type_line.upper():
            classification_type = "NOT APPLICABLE"
        else:
            classification_type = "NOT FOUND"
        
        return {
            "document_id": doc_id,
            "type": classification_type,
            "reasoning": reasoning_line if reasoning_line else llm_response,
            "raw_response": llm_response,
            "success": True
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "document_id": doc_id,
            "type": "ERROR",
            "reasoning": f"API request failed: {str(e)}",
            "raw_response": None,
            "success": False
        }
    except KeyError as e:
        return {
            "document_id": doc_id,
            "type": "ERROR",
            "reasoning": f"Unexpected API response format: {str(e)}",
            "raw_response": response.text if 'response' in locals() else None,
            "success": False
        }
    except Exception as e:
        return {
            "document_id": doc_id,
            "type": "ERROR",
            "reasoning": f"Unexpected error: {str(e)}",
            "raw_response": None,
            "success": False
        }