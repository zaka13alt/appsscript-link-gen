
## Requirements

* Python 3
* A Google account
* A Google OAuth2 access token
* Google Apps Script API enabled for the Google Cloud project being used

Install the only Python dependency:

```bash
python3 -m pip install requests
```

## Usage

The basic command is:

```bash
python3 generate.py --codepath /path/to/code.gs --links 30 --token "YOUR_OAUTH2_TOKEN"
```

### Arguments

`--codepath`

Path to the Google Apps Script source file.

```bash
--codepath /home/user/myapp/code.gs
```

`--links`

Number of separate web apps to create.

```bash
--links 30
```

`--token`

Google OAuth2 access token with the required Apps Script permissions.

```bash
--token "ya29.example..."
```

## Example

Suppose the files look like this:

```text
project/
├── generate.py
└── code.gs
```

Run:


python3 generate.py --codepath ./code.gs --links 10 --token "YOUR_TOKEN"


The script will create 10 separate Apps Script projects, upload `code.gs` to each one, create a version, and deploy each project as a web app.

At the end, the URLs will be printed:

```text
================================================================================
WEB APP /exec LINKS
================================================================================
https://script.google.com/macros/s/AKfycbxxxxxxxxxxxxxxxx/exec
https://script.google.com/macros/s/AKfycbxxxxxxxxxxxxxxxx/exec
https://script.google.com/macros/s/AKfycbxxxxxxxxxxxxxxxx/exec
...
================================================================================
Created 10 / 10 web apps successfully.
Metadata saved to: generated_apps_script_links.json
```

## Output

The script creates:

```text
generated_apps_script_links.json
```

This contains the project IDs, deployment IDs, version numbers, and `/exec` URLs.

Example:

```json
[
  {
    "number": 1,
    "title": "Generated Web App 1",
    "scriptId": "1AbCdEfGhIj...",
    "versionNumber": 1,
    "deploymentId": "AKfycb...",
    "url": "https://script.google.com/macros/s/AKfycb.../exec"
  }
]
```

## OAuth permissions

The access token needs permission to create and deploy Apps Script projects.

The relevant scopes are:

```text
https://www.googleapis.com/auth/script.projects
https://www.googleapis.com/auth/script.deployments
```

Make sure the Apps Script API is enabled before running the script.

## `code.gs`

Your source file can contain normal Apps Script code. For a web app, it will generally need a `doGet()` or `doPost()` function.

For example:

```javascript
function doGet() {
  return ContentService
    .createTextOutput("Hello world");
}
```

