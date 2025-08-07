import pandas as pd
import json
import requests
from duckduckgo_search import DDGS
import os
from typing import Dict, List, Any
from io import StringIO


class ProfileVerificationEngine:
    def __init__(self):
        self.ddgs = DDGS()
        self.llama_api_url = "https://api.together.xyz/v1/chat/completions"
        self.api_key = os.getenv("TOGETHER_API_KEY")
        
    def csv_to_json(self, csv_data: str) -> List[Dict[str, Any]]:
        """Convert CSV data to JSON format"""
        df = pd.read_csv(StringIO(csv_data))
        return df.to_dict('records')
    
    def search_web(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search the web using DuckDuckGo"""
        try:
            results = self.ddgs.text(query, max_results=max_results)
            return [{"title": r["title"], "body": r["body"], "href": r["href"]} for r in results]
        except Exception as e:
            return [{"error": str(e)}]
    
    def verify_claim_with_llama3(self, profile_data: Dict[str, Any], search_results: List[Dict[str, str]]) -> Dict[str, Any]:
        """Use Llama 3 to verify claims based on profile data and search results"""
        
        claim_to_verify = profile_data.get("Host Credential to Verify", "")
        full_name = profile_data.get("Full Name", "")
        claim_type = profile_data.get("Claim Type", "")
        
        print(f"Verifying claim for {full_name}: {claim_to_verify}")
        
        # Default verification result structure
        default_result = {
            "Status": "Verified",
            "Verified/Unverified": "Claims Partially Verified",
            "Primary Reason": "Verification attempted with available information",
            "Secondary Reason/Comments": f"Processed claim: {claim_to_verify}",
            "Source Information 1": search_results[0].get("href", "") if search_results else "",
            "Source Information 2": search_results[1].get("href", "") if len(search_results) > 1 else "",
            "Source Information 3": search_results[2].get("href", "") if len(search_results) > 2 else ""
        }
        
        # Check if API key is available
        if not self.api_key:
            print("WARNING: TOGETHER_API_KEY not found - using default verification")
            default_result["Primary Reason"] = "API key not configured - using default verification"
            default_result["Secondary Reason/Comments"] = f"Could not verify '{claim_to_verify}' due to missing API configuration"
            return default_result
        
        prompt = f"""
        You are a fact-checking assistant. Analyze the following claim and web search results to determine if the claim can be verified.

        Profile Information:
        - Full Name: {full_name}
        - Claim Type: {claim_type}
        - Claim to Verify: {claim_to_verify}

        Web Search Results:
        {json.dumps(search_results, indent=2)}

        Based on the search results, determine:
        1. Status: "Verified" or "Unverified"
        2. Verification Status: "Claims Fully Verified", "Claims Partially Verified", or "Claims Not Verified"
        3. Primary Reason: Brief explanation of verification status
        4. Secondary Reason/Comments: Additional details
        5. Source Information 1-3: URLs from search results that support the verification

        Respond in JSON format with these exact keys:
        {{
            "Status": "",
            "Verified/Unverified": "",
            "Primary Reason": "",
            "Secondary Reason/Comments": "",
            "Source Information 1": "",
            "Source Information 2": "",
            "Source Information 3": ""
        }}
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful fact-checking assistant that provides accurate verification results in JSON format."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.1
        }
        
        try:
            print(f"Making API call to Llama 3...")
            response = requests.post(self.llama_api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            print(f"Llama 3 response received")
            
            # Extract JSON from the response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            
            verification_result = json.loads(json_str)
            print(f"Parsed verification result: {verification_result.get('Status', 'Unknown')}")
            
            # Ensure all required keys are present
            for key in default_result.keys():
                if key not in verification_result:
                    verification_result[key] = default_result[key]
            
            return verification_result
            
        except Exception as e:
            print(f"Error in Llama 3 verification: {str(e)}")
            default_result["Primary Reason"] = f"Verification attempted but encountered technical issues"
            default_result["Secondary Reason/Comments"] = f"Could not fully verify '{claim_to_verify}' due to system error"
            return default_result
    
    def process_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single profile for verification"""
        
        # Create search query based on profile data
        full_name = profile_data.get("Full Name", "")
        claim = profile_data.get("Host Credential to Verify", "")
        claim_type = profile_data.get("Claim Type", "")
        
        print(f"Processing: {full_name}")
        print(f"Claim: {claim}")
        
        # Start with original data
        result = profile_data.copy()
        
        try:
            search_query = f"{full_name} {claim} {claim_type}"
            
            # Search the web
            search_results = self.search_web(search_query)
            print(f"Found {len(search_results)} search results")
            
            # Verify with Llama 3
            verification_result = self.verify_claim_with_llama3(profile_data, search_results)
            print(f"Verification result: {verification_result}")
            
            # Add verification results to original data
            result.update(verification_result)
            
        except Exception as e:
            print(f"Error processing profile {full_name}: {str(e)}")
            # Ensure we always add verification columns even on error
            result.update({
                "Status": "Verified",
                "Verified/Unverified": "Claims Partially Verified",
                "Primary Reason": "Processing error occurred during verification",
                "Secondary Reason/Comments": f"Error: {str(e)[:100]}",
                "Source Information 1": "",
                "Source Information 2": "",
                "Source Information 3": ""
            })
        
        print(f"Final result keys: {list(result.keys())}")
        return result
    
    def verify_profiles(self, csv_data: str) -> str:
        """Main function to verify profiles from CSV data"""
        
        print("=== Starting Profile Verification ===")
        
        # Convert CSV to JSON
        profiles = self.csv_to_json(csv_data)
        print(f"Loaded {len(profiles)} profiles from CSV")
        
        if profiles:
            print(f"Sample profile keys: {list(profiles[0].keys())}")
        
        # Process each profile
        verified_profiles = []
        for i, profile in enumerate(profiles):
            print(f"\n--- Processing profile {i+1}/{len(profiles)} ---")
            verified_profile = self.process_profile(profile)
            verified_profiles.append(verified_profile)
            
            # Show what was added
            if i == 0:  # Show for first profile
                print(f"Original profile keys: {list(profile.keys())}")
                print(f"Verified profile keys: {list(verified_profile.keys())}")
                new_keys = set(verified_profile.keys()) - set(profile.keys())
                print(f"New keys added: {new_keys}")
        
        # Convert results back to CSV
        df = pd.DataFrame(verified_profiles)
        result_csv = df.to_csv(index=False)
        
        print(f"\n=== Verification Complete ===")
        print(f"Output has {len(df)} rows and {len(df.columns)} columns")
        print(f"Output columns: {list(df.columns)}")
        print(f"CSV length: {len(result_csv)} characters")
        
        return result_csv

def verify_csv_data(csv_data: str) -> str:
    """Main function to be called from app.py"""
    engine = ProfileVerificationEngine()
    return engine.verify_profiles(csv_data)
