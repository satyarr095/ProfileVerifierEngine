import pandas as pd
import json
import requests
from ddgs import DDGS
from bs4 import BeautifulSoup
from typing import Dict, List, Any
from io import StringIO
import ollama


def is_valid_source(url: str) -> bool:
    blocked_keywords = [
    # Social Media Platforms
    "linkedin.com", "facebook.com", "twitter.com", "x.com", "instagram.com", "tiktok.com",
    "pinterest.com", "snapchat.com", "reddit.com", "tumblr.com", "threads.net", "discord.com",
    "wechat.com", "weibo.com", "line.me", "kakao.com", "telegram.org", "quora.com",

    # Video & Streaming Platforms
    "youtube.com", "vimeo.com", "dailymotion.com", "bilibili.com", "twitch.tv",

    # Code/Dev portfolios
    "github.com", "gitlab.com", "bitbucket.org", "dev.to", "hashnode.dev", "glitch.com",
    "replit.com", "sourceforge.net",

    
    # Misc. user-generated or unverifiable
    "personal", "portfolio", "blog", "my-site", "me.", "homepage", "user", "profile"
]
    return not any(kw in url.lower() for kw in blocked_keywords)


class ProfileVerificationEngine:
    def __init__(self):
        self.ddgs = DDGS()
        self.ollama_client = ollama.Client()
        self.model_name = "llama3:8b"

    def csv_to_json(self, csv_data: str) -> List[Dict[str, Any]]:
        df = pd.read_csv(StringIO(csv_data))
        return df.to_dict('records')

    def search_web(self, query: str, max_results: int = 7) -> List[Dict[str, str]]:
        try:
            results = self.ddgs.text(query, max_results=max_results)
            return [{"title": r["title"], "body": r["body"], "href": r["href"]} for r in results]
        except Exception as e:
            return [{"error": str(e)}]

    def fetch_and_parse_pages(self, search_results: List[Dict[str, str]]) -> List[Dict[str, str]]:
        parsed_results = []
        for result in search_results:
            url = result.get("href")
            if not is_valid_source(url):
                continue
            try:
                response = requests.get(url, timeout=5)
                soup = BeautifulSoup(response.content, "html.parser")
                text = soup.get_text(separator="\n", strip=True)
                parsed_results.append({
                    "url": url,
                    "title": result.get("title", ""),
                    "snippet": result.get("body", ""),
                    "content": text[:3000]
                })
            except Exception as e:
                parsed_results.append({
                    "url": url,
                    "title": result.get("title", ""),
                    "snippet": result.get("body", ""),
                    "content": f"Error fetching content: {str(e)}"
                })
        return parsed_results[:5]

    def verify_with_llama(self, profile_data, detailed_results):
        claim_to_verify = profile_data.get("Host Credential to Verify", "")
        full_name = profile_data.get("Full Name", "")
        claim_type = profile_data.get("Claim Type", "")

        prompt = f"""
You are a strict fact-checking assistant. Given a profile claim and supporting web documents, verify the claim according to the following rules:

- NEVER use social media or personal/portfolio websites.
- ONLY use third-party credible sources.
- If evidence is from host's website only, label as "General Employment".
- If public links verify background but not from credible third-party sources, label "Partially Verified".
- Contradictory verified claims → "False Claim".
- If enough info but unable to confirm → "Inconclusive Claim".
- If org is permanently closed, label → "Establishment Permanently Closed".
- No credible sources → "Unverifiable".
- DO NOT return "Verified" unless a valid link is present.
- Only ONE status per claim.
- ALWAYS include Secondary Reason stating what is verified and what is not.

Profile:
- Full Name: {full_name}
- Claim Type: {claim_type}
- Claim to Verify: {claim_to_verify}

Web Evidence:
{json.dumps(detailed_results, indent=2)}

Respond strictly in this JSON format:
{{
  "Status": "",  // One of: Verified, Partially Verified, Unverifiable, Inconclusive Claim, False Claim, Establishment Permanently Closed
  "Verified/Unverified": "",
  "Primary Reason": "",
  "Secondary Reason/Comments": "",
  "Source Information 1": "",
  "Source Information 2": "",
  "Source Information 3": ""
}}
"""

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
        return json.loads(json_str)

    def verify_claim_with_llama3(self, profile_data: Dict[str, Any], search_results: List[Dict[str, str]]) -> Dict[str, Any]:
        default_result = {
            "Status": "Inconclusive Claim",
            "Verified/Unverified": "",
            "Primary Reason": "Default fallback",
            "Secondary Reason/Comments": "",
            "Source Information 1": "",
            "Source Information 2": "",
            "Source Information 3": ""
        }

        try:
            models = self.ollama_client.list()
            available_models = [model.model for model in models.models]
            if self.model_name not in available_models:
                return {
                    **default_result,
                    "Primary Reason": f"Model {self.model_name} not available",
                    "Secondary Reason/Comments": f"Available: {', '.join(available_models)}"
                }
        except Exception as e:
            return {
                **default_result,
                "Primary Reason": f"Ollama error: {type(e).__name__}",
                "Secondary Reason/Comments": str(e)
            }

        # First round
        detailed_results = self.fetch_and_parse_pages(search_results)
        try:
            result = self.verify_with_llama(profile_data, detailed_results)
            # Retry logic for certain fallback cases
            if result.get("Status") in ["Inconclusive Claim", "Unverifiable"]:
                print("🔁 Retrying with refined search...")
                refined_query = f"{profile_data.get('Full Name')} {profile_data.get('Claim Type')} {profile_data.get('Host Credential to Verify')} site:.org OR site:.edu OR site:.gov"
                refined_results = self.search_web(refined_query)
                refined_detailed = self.fetch_and_parse_pages(refined_results)
                result = self.verify_with_llama(profile_data, refined_detailed)
        except Exception as e:
            result = {
                **default_result,
                "Primary Reason": f"Verification failed: {str(e)}"
            }

        # Ensure fallbacks are filled
        for i in range(1, 4):
            key = f"Source Information {i}"
            if key not in result:
                result[key] = ""

        return result

    def process_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        result = profile_data.copy()
        try:
            query = f"{profile_data.get('Full Name')} {profile_data.get('Host Credential to Verify')} {profile_data.get('Claim Type')}"
            search_results = self.search_web(query)
            verification_result = self.verify_claim_with_llama3(profile_data, search_results)
            result.update(verification_result)
        except Exception as e:
            result.update({
                "Status": "Inconclusive Claim",
                "Verified/Unverified": "",
                "Primary Reason": "Error during verification",
                "Secondary Reason/Comments": str(e),
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
