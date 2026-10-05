import requests
from config.settings import SEMANTIC_SCHOLAR_API_KEY


BASE_URL = "https://api.semanticscholar.org/graph/v1"


def search_authors(name: str, limit: int = 5):

    params = {
        "query": name,
        "limit": limit,
        "fields": "name,affiliations,paperCount,citationCount,hIndex,externalIds,url"
    }

    headers = {}

    if SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = SEMANTIC_SCHOLAR_API_KEY

    response = requests.get(
        f"{BASE_URL}/author/search",
        params=params,
        headers=headers,
        timeout=20
    )

    if response.status_code == 429:
        return {
            "data": [],
            "error": "Semantic Scholar rate limit reached"
        }

    response.raise_for_status()

    return response.json()

def get_author_papers(
    author_id: str,
    limit: int = 100,
    offset: int = 0
):
    """
    Get publications belonging to a selected
    Semantic Scholar author.
    """

    params = {
        "limit": limit,
        "offset": offset,
        "fields": (
            "paperId,"
            "corpusId,"
            "title,"
            "year,"
            "authors,"
            "venue,"
            "publicationDate,"
            "citationCount,"
            "externalIds,"
            "url"
        )
    }

    headers = {}

    if SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = SEMANTIC_SCHOLAR_API_KEY

    response = requests.get(
        f"{BASE_URL}/author/{author_id}/papers",
        params=params,
        headers=headers,
        timeout=20
    )

    if response.status_code == 429:
        return {
            "data": [],
            "error": "Semantic Scholar rate limit reached"
        }

    response.raise_for_status()

    return response.json()