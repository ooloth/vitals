# Auth Strategies by Provider

Vitals runs locally as a single-user app. Auth is handled at the process level via
`op run --env-file=secrets.env -- next dev`, which injects secrets as env vars before
the app starts. The app itself never handles user auth.

Non-secret params (project IDs, base URLs, datasource UIDs, log selectors) are stored
plainly in `vitals.config.toml`. Only tokens and keys go in `secrets.env`.

---

## Google Cloud Logging

**Strategy: Application Default Credentials (ADC)**

GCP client libraries resolve credentials automatically via a chain:

1. `GOOGLE_APPLICATION_CREDENTIALS` env var (path to a service account key file)
2. `gcloud auth application-default login` credentials (`~/.config/gcloud/`)
3. Workload identity / metadata server (when running on GCP infrastructure)

For local use, #2 applies. Run once:

```bash
gcloud auth application-default login
```

After that, all GCP client libraries (including the Node.js `@google-cloud/logging`
package) authenticate transparently. No token in config, no env var needed.

**Config**: only non-secret params required.

```toml
[projects.panels.params]
project_id = "my-gcp-project-123"   # not a secret
# log_name = "projects/my-project/logs/app"  # optional filter
```

**Multiple GCP projects**: each has its own `project_id` in config. ADC credentials
cover all projects your account has access to — no per-project auth needed.

---

## Grafana Loki

**Strategy: TBD — depends on your Grafana instance setup**

Two likely cases:

### Case A: SSO / OAuth (most likely for work instances)

Your terminal session works because a company-managed credential (browser session,
CLI token, or credential helper) is tied to your identity. These are short-lived and
not suitable for storing in 1Password.

In this case, generate a **personal service account token** in Grafana:
`Profile → Service Accounts → Create token`

Store it in 1Password and reference it via `secrets.env`:

```
GRAFANA_TOKEN=op://Work/Grafana/token
```

Config references the env var for the token, stores everything else plainly:

```toml
[projects.panels.params]
base_url    = "https://grafana.yourcompany.com"
datasource_uid = "abc123"
selector    = '{app="my-api", env="prod"}'
token       = "${GRAFANA_TOKEN}"
```

### Case B: Anonymous / network-trusted access

No token needed. Just the base URL and datasource details in config.

```toml
[projects.panels.params]
base_url       = "https://grafana.yourcompany.com"
datasource_uid = "abc123"
selector       = '{app="my-api", env="prod"}'
```

### How to determine which case applies

```bash
# Try without auth — if this returns data, Case B applies
curl "https://grafana.yourcompany.com/api/datasources"

# If 401, you need a token (Case A)
```

Also check whether `Profile → Service Accounts` is available in your Grafana instance.
If it is, generating a token is the cleanest path regardless of how your terminal
currently authenticates.
