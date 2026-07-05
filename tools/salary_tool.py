import os
from tavily import TavilyClient

class SalaryTool:
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        if self.api_key:
            try:
                self.client = TavilyClient(api_key=self.api_key)
            except Exception as e:
                print(f"[Warning] Failed to initialize Tavily client: {e}")
                self.client = None
        else:
            self.client = None

    def search_salary_data(self, role: str, location: str) -> str:
        """Queries Tavily API to fetch current market salary benchmarks for a role and location."""
        if not self.client:
            return (
                "Tavily API client is not configured. "
                "Please configure a valid TAVILY_API_KEY in your environment (.env file)."
            )
            
        # Target search query
        query = f"average salary range {role} {location} market rate benchmark"
        try:
            # Run simple search
            response = self.client.search(query=query, max_results=3, topic="general")
            results = response.get("results", [])
            
            if not results:
                return "No market data found on the web for this role and location."
                
            formatted_data = []
            for i, item in enumerate(results):
                title = item.get("title", "Web Source")
                url = item.get("url", "")
                content = item.get("content", "")
                formatted_data.append(f"- **{title}**\n  *Source: {url}*\n  {content}\n")
                
            return "\n".join(formatted_data)
        except Exception as e:
            return f"Failed to retrieve salary benchmark from Tavily: {e}"
