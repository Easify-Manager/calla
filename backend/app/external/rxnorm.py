"""RxNorm API client for drug information"""

import httpx
from typing import List
from pydantic import BaseModel


RXNORM_BASE_URL = "https://rxnav.nlm.nih.gov/REST"


class DrugSearchResult(BaseModel):
    rxcui: str
    name: str
    synonym: str = None
    strengths: List[str] = []


class RxNormClient:
    @staticmethod
    async def search_drugs(query: str, max_results: int = 10) -> List[DrugSearchResult]:
        """Search for drugs by name using RxNorm API"""
        try:
            async with httpx.AsyncClient() as client:
                # Use approximate term search
                response = await client.get(
                    f"{RXNORM_BASE_URL}/approximateTerm.json",
                    params={"term": query, "maxEntries": max_results},
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                results = []
                candidates = data.get("approximateGroup", {}).get("candidate", [])
                
                for candidate in candidates[:max_results]:
                    rxcui = candidate.get("rxcui")
                    name = candidate.get("name", "")
                    
                    if rxcui:
                        # Get additional details
                        details = await RxNormClient.get_drug_details(rxcui)
                        results.append(DrugSearchResult(
                            rxcui=rxcui,
                            name=name,
                            strengths=details.get("strengths", [])
                        ))
                
                return results
        except Exception as e:
            print(f"RxNorm search error: {e}")
            return []
    
    @staticmethod
    async def get_drug_details(rxcui: str) -> dict:
        """Get detailed drug information by RxCUI"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{RXNORM_BASE_URL}/rxcui/{rxcui}/allrelated.json",
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                strengths = []
                
                concept_groups = data.get("allRelatedGroup", {}).get("conceptGroup", [])
                
                for group in concept_groups:
                    tty = group.get("tty", "")
                    concepts = group.get("conceptProperties", [])
                    
                    if tty == "SCDC":  # Semantic Clinical Drug Component
                        strengths.extend([c.get("name", "") for c in concepts])
                
                return {
                    "strengths": list(set(strengths))[:5]
                }
        except Exception as e:
            print(f"RxNorm details error: {e}")
            return {}
