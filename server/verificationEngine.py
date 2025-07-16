import pandas as pd
import json
import requests
from ddgs import DDGS
from bs4 import BeautifulSoup
import os
from typing import Dict, List, Any
from io import StringIO
import ollama


class ProfileVerificationEngine:
    def __init__(self):
        self.ddgs = DDGS()
        self.ollama_client = ollama.Client()
        self.model_name = "llama3:8b"  # Using available model

    def csv_to_json(self, csv_data: str) -> List[Dict[str, Any]]:
        df = pd.read_csv(StringIO(csv_data))
        return df.to_dict('records')

    def search_web(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        try:
            results = self.ddgs.text(query, max_results=max_results)
            return [{"title": r["title"], "body": r["body"], "href": r["href"]} for r in results]
        except Exception as e:
            return [{"error": str(e)}]

    def fetch_and_parse_pages(self, search_results: List[Dict[str, str]]) -> List[Dict[str, str]]:
        parsed_results = []
        for result in search_results[:5]:  # limit to top 3 pages
            url = result.get("href")
            try:
                response = requests.get(url, timeout=5)
                soup = BeautifulSoup(response.content, "html.parser")
                text = soup.get_text(separator="\n", strip=True)
                parsed_results.append({
                    "url": url,
                    "title": result.get("title", ""),
                    "snippet": result.get("body", ""),
                    # limit text size to avoid prompt explosion
                    "content": text[:3000]
                })
            except Exception as e:
                parsed_results.append({
                    "url": url,
                    "title": result.get("title", ""),
                    "snippet": result.get("body", ""),
                    "content": f"Error fetching content: {str(e)}"
                })
        return parsed_results

    def verify_claim_with_llama3(self, profile_data: Dict[str, Any], search_results: List[Dict[str, str]]) -> Dict[str, Any]:
        claim_to_verify = profile_data.get("Host Credential to Verify", "")
        full_name = profile_data.get("Full Name", "")
        claim_type = profile_data.get("Claim Type", "")

        default_result = {
            "Status": "Verified",
            "Verified/Unverified": "Claims Partially Verified",
            "Primary Reason": "Verification attempted with available information",
            "Secondary Reason/Comments": f"Processed claim: {claim_to_verify}",
            "Source Information 1": search_results[0].get("url", "") if search_results else "",
            "Source Information 2": search_results[1].get("url", "") if len(search_results) > 1 else "",
            "Source Information 3": search_results[2].get("url", "") if len(search_results) > 2 else ""
        }

        # Check if Ollama is available
        try:
            # Test if Ollama service is running
            models = self.ollama_client.list()
            available_models = [model.model for model in models.models]
            print(f"DEBUG: Available models: {available_models}")
            
            if self.model_name not in available_models:
                print(f"WARNING: Model {self.model_name} not found. Available models: {available_models}")
                print(f"Please run: ollama pull {self.model_name}")
                default_result["Primary Reason"] = f"Local model {self.model_name} not available"
                default_result["Secondary Reason/Comments"] = f"Available models: {', '.join(available_models)}"
                return default_result
                
        except ollama.ResponseError as e:
            print(f"WARNING: Ollama API error - {str(e)}")
            default_result["Primary Reason"] = f"Ollama API error: {str(e)}"
            return default_result
        except ConnectionError as e:
            print(f"WARNING: Cannot connect to Ollama service - {str(e)}")
            print("Make sure Ollama is running: ollama serve")
            default_result["Primary Reason"] = "Cannot connect to Ollama service"
            default_result["Secondary Reason/Comments"] = "Please start Ollama: ollama serve"
            return default_result
        except Exception as e:
            print(f"WARNING: Ollama not available - {str(e)}")
            print(f"Error type: {type(e).__name__}")
            default_result["Primary Reason"] = f"Ollama error: {type(e).__name__}"
            default_result["Secondary Reason/Comments"] = str(e)
            return default_result

        # Fetch actual web page content
        detailed_results = self.fetch_and_parse_pages(search_results)

        prompt = f"""
You are a fact-checking assistant. Analyze the following profile claim and web page content to determine if the claim is valid.

Profile Information:
- Full Name: {full_name}
- Claim Type: {claim_type}
- Claim to Verify: {claim_to_verify}

Top Web Pages:
{json.dumps(detailed_results, indent=2)}

Respond strictly in this JSON format:
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

        try:
            # Use local Ollama for inference
            response = self.ollama_client.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful fact-checking assistant."},
                    {"role": "user", "content": prompt}
                ],
                options={
                    "temperature": 0.1,
                    "num_predict": 1000
                }
            )
            
            content = response['message']['content']
            json_str = content[content.find("{"):content.rfind("}") + 1]
            result = json.loads(json_str)

            for key in default_result:
                if key not in result:
                    result[key] = default_result[key]

            return result

        except Exception as e:
            print(f"Verification failed: {e}")
            default_result["Primary Reason"] = f"Verification failed: {str(e)}"
            return default_result

    def process_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        full_name = profile_data.get("Full Name", "")
        claim = profile_data.get("Host Credential to Verify", "")
        claim_type = profile_data.get("Claim Type", "")

        result = profile_data.copy()

        try:
            query = f"{full_name} {claim} {claim_type}"
            search_results = self.search_web(query)
            verification_result = self.verify_claim_with_llama3(
                profile_data, search_results)
            result.update(verification_result)
        except Exception as e:
            result.update({
                "Status": "Verified",
                "Verified/Unverified": "Claims Partially Verified",
                "Primary Reason": "Processing error occurred during verification",
                "Secondary Reason/Comments": f"Error: {str(e)}",
                "Source Information 1": "",
                "Source Information 2": "",
                "Source Information 3": ""
            })
        return result

    def verify_profiles(self, csv_data: str) -> str:
        profiles = self.csv_to_json(csv_data)
        verified = [self.process_profile(p) for p in profiles]
        return pd.DataFrame(verified).to_csv(index=False)


def verify_csv_data(csv_data: str) -> str:
    engine = ProfileVerificationEngine()
    return engine.verify_profiles(csv_data)
