import requests
import time

BASE_URL = "https://api.openalex.org"


def search_authors(author_name, per_page=100):
    """
    Search OpenAlex authors using the first name only.
    """

    parts = author_name.strip().split()

    if not parts:
        return {
            "results": [],
            "error": "Author name is empty"
        }

    search_term = parts[0]

    url = f"{BASE_URL}/authors"

    params = {
        "search": search_term,
        "per-page": per_page
    }

    for attempt in range(3):

        try:

            response = requests.get(
                url,
                params=params,
                timeout=60
            )

            response.raise_for_status()

            data = response.json()

            target_name = " ".join(
                author_name.lower().strip().split()
            )

            filtered_results = []

            for author in data.get("results", []):

                display_name = (
                    author.get("display_name") or ""
                )

                candidate_name = " ".join(
                    display_name.lower().strip().split()
                )

                if candidate_name == target_name:
                    filtered_results.append(author)

            data["results"] = filtered_results

            return data

        except requests.exceptions.RequestException as error:

            if attempt == 2:

                return {
                    "results": [],
                    "error": (
                        f"OpenAlex request failed: {error}"
                    )
                }

            time.sleep(2)


def get_author_works(
    author_id: str,
    per_page=25,
    page=1
):

    author_id = author_id.replace(
        "https://openalex.org/",
        ""
    )

    url = f"{BASE_URL}/works"

    params = {
        "filter": f"author.id:{author_id}",
        "per-page": per_page,
        "page": page,
        "sort": "publication_date:desc"
    }

    for attempt in range(3):

        try:

            response = requests.get(
                url,
                params=params,
                timeout=60
            )

            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as error:

            if attempt == 2:

                return {
                    "results": [],
                    "error": (
                        "OpenAlex works request failed: "
                        f"{error}"
                    )
                }

            time.sleep(2)