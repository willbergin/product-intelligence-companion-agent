# Product Intelligence Companion User Guide

Use this guide to set up your first brief, choose what the agent reads and decide how you want the report delivered.

## 1. Start with what you want to follow

Give the agent your company or product name and official website if you have it. If the company has several products or brands, say which ones belong in the brief. Include any markets or languages that matter to your work.

| If you want to follow | Choose |
| --- | --- |
| One area, such as onboarding | **Focused** (`focused`) |
| One area, with a short note on important changes elsewhere | **Focused plus outside highlights** (`focused_plus`) |
| The full product or portfolio | **All areas** (`all`) |

For all areas, ask the agent to suggest a list of areas from your product site. You can edit that list before the first run.

## 2. Choose competitors and feedback sources

Make three choices independently: **which competitors to track**, **where to read their customer feedback**, and **where to read feedback about your own product**.

| Option | Competitors | Feedback sources |
| --- | --- | --- |
| **Use my list** (`manual`) | Track the competitors you supply. | Read only the sources you supply. |
| **Use my list and discover others** (`augment`) | Start with your list and suggest other relevant competitors. | Check your sources and look for other relevant places to read. |
| **Discover for me** (`discover`) | Suggest a watchlist based on product, customer and market overlap. | Find relevant forums, communities, app-store listings and review sites. |

Specific links help when a brand has several app listings or forums. For example, you might ask the agent to discover competitor feedback but limit feedback about your product to your support community and UK app-store listing.

Review the competitor watchlist during setup. Later briefs can suggest additions when discovery is enabled, and you can decide which ones to track. The feedback source choices apply to reviews and discussions. The agent checks official sources for competitor releases separately.

In the config file, set `scope.competitor_mode` and `scope.competitors` for the watchlist. Set `scope.feedback_sources.competitors` and `scope.feedback_sources.own` separately. Each feedback group takes a mode and a list of source names or URLs. Supply at least one source for `manual` and leave the list empty for `discover`. Omitted feedback groups default to discovery.

## 3. Run a first brief

Copy [the example config](../config.example.json) to `config.json` and add your settings. Open the project in an AI tool with web access and try:

> Use WORKFLOW.md and my config.json. Show me the proposed watchlist and feedback sources. Once we've agreed the setup, run a brief for the last seven complete days.

Look at the linked evidence and the source coverage note. If a product name is ambiguous or a review source mainly shows old posts, use a more specific name or listing. Once the first brief looks right, schedule it weekly in your host's time zone. Pick a delivery destination your host supports.

## 4. Read the report

The brief opens with up to three findings and why they matter. It then covers competitor releases, competitor customer feedback and feedback about your own product. A release can be announced, in beta, rolling out or available, depending on what its source confirms.

Open the links when a finding could affect a product decision. One customer post can point to something worth investigating. A recurring theme requires independent reports, and a comparison with last week requires comparable evidence. Use the coverage note to see which sources were checked and where access or dates were unclear.

## Run from a terminal

Use Python 3.10 or later with IANA time zone data. Replace the placeholder research and model commands in your local config with working adapters. Each adapter reads one JSON value from stdin and returns one JSON value on stdout. [WORKFLOW.md](../WORKFLOW.md) describes what each adapter receives and returns. Keep credentials in environment variables and send adapter diagnostics to stderr.

```sh
python3 agent.py discover config.json
python3 agent.py run config.json
```

The discovery command prints proposals. Update the config with the areas and competitors you want to track. The run command prints and saves a dated Markdown brief in the configured report directory. Add `--as-of YYYY-MM-DD` to set a test date. The report covers the seven calendar days before that date.

Once a test run works, configure your scheduler to run the weekly command from the project directory. For example, use this in cron when the scheduler is set to your intended local time zone:

```cron
0 9 * * 1 cd /path/to/product-intelligence-companion && python3 agent.py run config.json
```

For delivery beyond the local report, configure a delivery adapter. It receives the Markdown and period end date and returns a JSON acknowledgement.

### Send the brief by email or Slack

Set `adapters.delivery` in your local `config.json` to one of these command arrays:

| Destination | Command array |
| --- | --- |
| Email | `["python3", "deliver.py", "email"]` |
| Slack | `["python3", "deliver.py", "slack"]` |

For email, set `PIC_SMTP_HOST`, `PIC_EMAIL_FROM` and `PIC_EMAIL_TO` in the environment
of the process running the brief. Separate multiple recipients with commas. If your SMTP
provider requires authentication, also set `PIC_SMTP_USERNAME` and `PIC_SMTP_PASSWORD`.
The default is STARTTLS on port 587. For implicit TLS, set `PIC_SMTP_SECURITY=ssl`
to use port 465. Set `PIC_SMTP_PORT` if your provider uses a different port.

For Slack, create an incoming webhook for the channel you want and set its URL as
`PIC_SLACK_WEBHOOK_URL` in the scheduled process's environment. The webhook determines
the channel. Keep the URL and SMTP credentials out of GitHub and the agent config.

Run the CLI once with a test destination before enabling the weekly schedule. The CLI
saves the Markdown report before calling the delivery adapter. If a send fails, you can
retry delivery from the saved report without repeating the research. Check the destination
first if the outcome is unclear to avoid sending duplicates:

```sh
python3 -c 'import json, pathlib, sys; p = pathlib.Path(sys.argv[1]); print(json.dumps(dict(report=p.read_text(encoding="utf-8"), period_end=p.stem)))' reports/YYYY-MM-DD.md | python3 deliver.py email
```

Use `slack` at the end of the command to retry Slack delivery. If you're running directly
inside an AI tool, use its own mail or Slack integration if available. The bundled adapter
runs through the Python CLI.
