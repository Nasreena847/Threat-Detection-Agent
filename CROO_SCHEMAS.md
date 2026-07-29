# CROO Dashboard Schemas

Use these schemas for the Threat Detection Agent service in the CROO dashboard.

## Agent

- **Agent ID:** `threat-detection-agent`
- **Name:** `Threat Detection Agent`
- **Service:** `website-risk-analysis`
- **Description:** `Deterministic browser security service that analyzes a URL and optional page metadata for phishing and suspicious activity, then returns an explainable risk report.`

## Input Schema

### Input Fields

| fieldName | type | required | description |
|---|---|---:|---|
| `url` | `string` | Yes | Website URL to analyze. |
| `title` | `string` | No | Page title collected from the browser tab. |
| `page_text` | `string` | No | Visible text extracted from the page. |
| `html` | `string` | No | Raw page HTML, if available. |
| `domain` | `string` | No | Current page domain. |
| `https` | `boolean` | No | Whether the page uses HTTPS. |
| `forms` | `integer` | No | Number of forms detected on the page. |
| `scripts` | `integer` | No | Number of script elements detected on the page. |
| `password_fields` | `integer` | No | Number of password fields detected on the page. |
| `iframes` | `integer` | No | Number of iframe elements detected on the page. |

```json
{
  "fieldName": "input",
  "type": "object",
  "required": ["url"],
  "properties": {
    "url": {
      "fieldName": "url",
      "required": true,
      "type": "string",
      "description": "Website URL to analyze."
    },
    "title": {
      "fieldName": "title",
      "required": false,
      "type": "string",
      "description": "Optional page title."
    },
    "page_text": {
      "fieldName": "page_text",
      "required": false,
      "type": "string",
      "description": "Optional visible text extracted from the page."
    },
    "html": {
      "fieldName": "html",
      "required": false,
      "type": "string",
      "description": "Optional raw page HTML."
    },
    "domain": {
      "fieldName": "domain",
      "required": false,
      "type": "string",
      "description": "Optional current page domain."
    },
    "https": {
      "fieldName": "https",
      "required": false,
      "type": "boolean",
      "description": "Whether the page uses HTTPS."
    },
    "forms": {
      "fieldName": "forms",
      "required": false,
      "type": "integer",
      "minimum": 0,
      "description": "Number of forms detected on the page."
    },
    "scripts": {
      "fieldName": "scripts",
      "required": false,
      "type": "integer",
      "minimum": 0,
      "description": "Number of script elements detected on the page."
    },
    "password_fields": {
      "fieldName": "password_fields",
      "required": false,
      "type": "integer",
      "minimum": 0,
      "description": "Number of password fields detected on the page."
    },
    "iframes": {
      "fieldName": "iframes",
      "required": false,
      "type": "integer",
      "minimum": 0,
      "description": "Number of iframe elements detected on the page."
    }
  }
}
```

## Output Schema

### Output Fields

| fieldName | type | required | description |
|---|---|---:|---|
| `url` | `string` | Yes | Analyzed URL. |
| `risk_score` | `integer` | Yes | Risk score where `0` is safest and `100` is highest risk. |
| `risk_level` | `string` | Yes | Human-readable level: `Safe`, `Medium`, or `High`. |
| `reasons` | `string[]` | Yes | Evidence behind the risk score. |
| `recommendation` | `string` | Yes | Recommended user action. |
| `explanation` | `string` | Yes | Plain-language explanation of the assessment. |
| `components` | `object` | No | Component-level scores used to calculate the final score. |
| `components.url` | `integer` | No | URL analyzer score from `0` to `100`. |
| `components.page` | `integer` | No | Page-content analyzer score from `0` to `100`. |
| `components.reputation` | `integer` | No | Local reputation score from `0` to `100`. |

```json
{
  "fieldName": "output",
  "type": "object",
  "required": ["url", "risk_score", "risk_level", "reasons", "recommendation", "explanation"],
  "properties": {
    "url": {
      "fieldName": "url",
      "required": true,
      "type": "string",
      "description": "Analyzed URL."
    },
    "risk_score": {
      "fieldName": "risk_score",
      "required": true,
      "type": "integer",
      "minimum": 0,
      "maximum": 100,
      "description": "Risk score where 0 is safest and 100 is highest risk."
    },
    "risk_level": {
      "fieldName": "risk_level",
      "required": true,
      "type": "string",
      "enum": ["Safe", "Medium", "High"],
      "description": "Human-readable risk level."
    },
    "reasons": {
      "fieldName": "reasons",
      "required": true,
      "type": "array",
      "items": {
        "fieldName": "reason",
        "required": true,
        "type": "string"
      },
      "description": "Evidence behind the risk score."
    },
    "recommendation": {
      "fieldName": "recommendation",
      "required": true,
      "type": "string",
      "description": "Recommended user action."
    },
    "explanation": {
      "fieldName": "explanation",
      "required": true,
      "type": "string",
      "description": "Plain-language explanation of the assessment."
    },
    "components": {
      "fieldName": "components",
      "required": false,
      "type": "object",
      "properties": {
        "url": {
          "fieldName": "url",
          "required": false,
          "type": "integer",
          "minimum": 0,
          "maximum": 100
        },
        "page": {
          "fieldName": "page",
          "required": false,
          "type": "integer",
          "minimum": 0,
          "maximum": 100
        },
        "reputation": {
          "fieldName": "reputation",
          "required": false,
          "type": "integer",
          "minimum": 0,
          "maximum": 100
        }
      },
      "description": "Component scores used to calculate the final score."
    }
  }
}
```

## Example Input

```json
{
  "url": "https://example.com/login",
  "title": "Example Login",
  "page_text": "Please verify your account and enter your password.",
  "forms": 1,
  "scripts": 8,
  "password_fields": 1,
  "iframes": 0
}
```

## Example Output

```json
{
  "url": "https://example.com/login",
  "risk_score": 41,
  "risk_level": "Medium",
  "reasons": [
    "The URL contains the suspicious keyword 'login'.",
    "Detected phishing phrase: 'verify your account'.",
    "The page contains 1 form(s).",
    "The page contains 1 password field(s)."
  ],
  "recommendation": "Exercise caution and avoid sharing sensitive information unless you trust the site.",
  "explanation": "This site is classified as Medium risk with a risk score of 41.",
  "components": {
    "url": 5,
    "page": 63,
    "reputation": 8
  }
}
```
