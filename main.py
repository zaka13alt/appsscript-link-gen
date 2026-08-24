#!/usr/bin/env python3

import argparse
import json
import sys
import time
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
            error = response.json()
            message = json.dumps(error, indent=2)
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
        json={
            "description": "Automated web app deployment",
        },
    )


def create_deployment(token, script_id, version_number):
    return api_request(
        "POST",
        f"{BASE_URL}/{script_id}/deployments",
        token,
        json={
            "versionNumber": version_number,
            "manifestFileName": "appsscript",
            "description": "Automated web app deployment",
        },
    )


def get_webapp_url(deployment):
    for entry_point in deployment.get("entryPoints", []):
        if entry_point.get("entryPointType") == "WEB_APP":
            web_app = entry_point.get("webApp", {})
            url = web_app.get("url")

            if url:
                return url

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Create and deploy multiple Google Apps Script web apps."
    )

    parser.add_argument(
        "--codepath",
        required=True,
        help="Path to code.gs",
    )

    parser.add_argument(
        "--links",
        required=True,
        type=int,
        help="Number of web apps to create",
    )

    parser.add_argument(
        "--token",
        required=True,
        help="Google OAuth2 access token",
    )

    args = parser.parse_args()

    if args.links < 1:
        parser.error("--links must be at least 1")

    code_path = Path(args.codepath)

    if not code_path.is_file():
        print(
            f"ERROR: code file does not exist: {code_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        code = code_path.read_text(encoding="utf-8")
    except Exception as exc:
        print(
            f"ERROR: could not read {code_path}: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    results = []

    print(f"Creating {args.links} Google Apps Script web apps...")
    print()

    for i in range(1, args.links + 1):
        title = f"Generated Web App {i}"

        try:
            print(f"[{i}/{args.links}] Creating project...")

            project = create_project(args.token, title)
            script_id = project["scriptId"]

            print(f"    Script ID: {script_id}")

            print("    Uploading code...")
            upload_project(
                args.token,
                script_id,
                code,
            )

            print("    Creating version...")
            version = create_version(
                args.token,
                script_id,
            )

            version_number = version["versionNumber"]

            print(f"    Version: {version_number}")

            print("    Deploying web app...")
            deployment = create_deployment(
                args.token,
                script_id,
                version_number,
            )

            url = get_webapp_url(deployment)

            if not url:
                raise RuntimeError(
                    "Deployment succeeded, but Google did not return a WEB_APP URL."
                )

            results.append(
                {
                    "number": i,
                    "title": title,
                    "scriptId": script_id,
                    "versionNumber": version_number,
                    "deploymentId": deployment.get("deploymentId"),
                    "url": url,
                }
            )

            print(f"    /exec URL: {url}")
            print()

        except Exception as exc:
            print(
                f"    ERROR: {exc}",
                file=sys.stderr,
            )
            print()

        if i < args.links:
            time.sleep(0.5)

    print()
    print("=" * 80)
    print("WEB APP /exec LINKS")
    print("=" * 80)

    for result in results:
        print(result["url"])

    print("=" * 80)
    print(
        f"Created {len(results)} / {args.links} web apps successfully."
    )

    output_file = Path("generated_apps_script_links.json")

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Metadata saved to: {output_file}")


if __name__ == "__main__":
    main()
