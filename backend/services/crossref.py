import requests


BASE_URL = "https://api.crossref.org"


def search_works(author_name, rows=5):
    """
    Search Crossref works by author name.
    """

    url = f"{BASE_URL}/works"

    params = {
        "query.author": author_name,
        "rows": rows
    }

    response = requests.get(
        url,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    return response.json()

def get_work_by_doi(doi: str):
    """
    Get detailed Crossref metadata for a DOI.
    """

    if not doi:
        return None

    doi = doi.replace(
        "https://doi.org/",
        ""
    ).strip()

    url = f"{BASE_URL}/works/{doi}"

    response = requests.get(
        url,
        timeout=20
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    return response.json()