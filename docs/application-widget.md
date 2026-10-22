# Public application widget

The widget is a small HTML/JavaScript form in [`widget/`](../widget/). It loads the tracks for an embed token, accepts an applicant's name/email/track, and submits to the public API. Applicants do not need an account.

## Configure the API

Set `CORS_ALLOWED_ORIGINS` in the API environment to the exact origin where `apply.html` is hosted. Include the scheme and port when present, with no path. Separate multiple origins with commas:

```dotenv
CORS_ALLOWED_ORIGINS=https://apply.example.org,http://localhost:8080
```

An empty setting allows no cross-origin browser requests. The API does not allow credentials or wildcard origins. CORS controls browser access; the embed token is public intake configuration and is not an authorization credential.

## Preview locally

Start the API, configure `CORS_ALLOWED_ORIGINS=http://localhost:8080`, and serve the widget directory from the repository root:

```sh
python -m http.server 8080 --directory widget
```

Open `http://localhost:8080/apply.html?apiBase=http%3A%2F%2Flocalhost%3A8000%2Fapi%2Fv1&embedToken=YOUR_COHORT_TOKEN` to preview the form. The API must be running at the supplied base URL.

## Embed on a site

Host `apply.html`, `apply.js`, and `loader.js` together on a static site. Add this snippet where the form should appear, replacing the API URL and cohort token:

```html
<div id="ctms-application"></div>
<script
  src="https://apply.example.org/loader.js"
  data-container="#ctms-application"
  data-widget-url="https://apply.example.org/apply.html"
  data-api-base="https://api.example.org/api/v1"
  data-embed-token="YOUR_COHORT_TOKEN"
  async
></script>
```

The loader adds an iframe for the form. The form page makes cross-origin requests to the CTMS API, so configure CORS for the static widget site's origin (the origin serving `apply.html`). The optional `data-height` attribute sets the iframe height; it defaults to `540px`.

The widget fetches `GET /cohorts/{embedToken}/application-tracks` to populate the track selector and posts to `POST /cohorts/{embedToken}/apply`. It displays loading, success, validation, duplicate, closed-intake, and network-error states. Duplicate email submissions and applications at or after the cohort's UTC start time are rejected by the API.

Rate limiting and bot protection are outside the scope of this project.
