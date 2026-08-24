#!/usr/bin/env python3

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests


BASE_URL = "https://script.googleapis.com/v1/projects"


def api_request(method, url, token, **kwargs):
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    headers["Content-Type"] = "application/json"

    response = requests.request(
        method,
        url,
        headers=headers,
        timeout=60,
        **kwargs,
    )

    if not response.ok:
        try:
            message = json.dumps(response.json())
        except Exception:
            message = response.text
        raise RuntimeError(
            f"HTTP {response.status_code}: {message}"
        )

    if not response.text:
        return {}

    return response.json()


def create_project(token, title):
    return api_request(
        "POST",
        BASE_URL,
        token,
        json={"title": title},
    )


def upload_project(token, script_id, code):
    manifest = {
        "timeZone": "America/New_York",
        "exceptionLogging": "STACKDRIVER",
        "webapp": {
            "executeAs": "USER_DEPLOYING",
            "access": "ANYONE_ANONYMOUS",
        },
    }

    return api_request(
        "PUT",
        f"{BASE_URL}/{script_id}/content",
        token,
        json={
            "files": [
                {
                    "name": "code",
                    "type": "SERVER_JS",
                    "source": code,
                },
                {
                    "name": "appsscript",
                    "type": "JSON",
                    "source": json.dumps(manifest),
                },
            ]
        },
    )


def create_version(token, script_id):
    return api_request(
        "POST",
        f"{BASE_URL}/{script_id}/versions",
        token,
        json={"description": "Web app deployment"},
    )


def create_deployment(token, script_id, version_number):
    return api_request(
        "POST",
        f"{BASE_URL}/{script_id}/deployments",
        token,
        json={
            "versionNumber": version_number,
            "manifestFileName": "appsscript",
            "description": "Web app deployment",
        },
    )


def get_webapp_url(deployment):
    for entry_point in deployment.get("entryPoints", []):
        if entry_point.get("entryPointType") == "WEB_APP":
            url = entry_point.get("webApp", {}).get("url")
            if url:
                return url

    raise RuntimeError("No web app URL returned")


def generate_one(token, code, number):
    project = create_project(
        token,
        f"Generated Web App {number}",
    )

    script_id = project["scriptId"]

    upload_project(
        token,
        script_id,
        code,
    )

    version = create_version(
        token,
        script_id,
    )

    deployment = create_deployment(
        token,
        script_id,
        version["versionNumber"],
    )

    return get_webapp_url(deployment)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--codepath",
        required=True,
    )

    parser.add_argument(
        "--links",
        required=True,
        type=int,
    )

    parser.add_argument(
        "--token",
        required=True,
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=8,
    )

    args = parser.parse_args()

    if args.links < 1:
        parser.error("--links must be at least 1")

    if args.workers < 1:
        parser.error("--workers must be at least 1")

    code_path = Path(args.codepath)

    if not code_path.is_file():
        sys.exit(1)

    code = code_path.read_text(encoding="utf-8")

    with ThreadPoolExecutor(
        max_workers=args.workers
    ) as executor:

        futures = [
            executor.submit(
                generate_one,
                args.token,
                code,
                i,
            )
            for i in range(1, args.links + 1)
        ]

        for future in as_completed(futures):
            try:
                url = future.result()
                print(url, flush=True)
            except Exception:
                pass


if __name__ == "__main__":
    main()
