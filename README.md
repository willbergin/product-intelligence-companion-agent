# Product Intelligence Companion

I built this agent for a job that tends to slip down the product team's list: keeping up with competitor releases and reading what customers are saying across reviews, forums and social posts. It brings those findings together in one weekly brief.

## What you can do with it

- **Track competitor releases.** See what shipped, where it's available and which official source confirms it.
- **See what customers say about competitors.** Look for recurring complaints, praise and requests in the sources that matter to your team.
- **See what customers say about your own product.** Follow the same themes in your own reviews and communities.

You can cover the whole product, focus on one area such as onboarding, or keep that focus and include major developments elsewhere. Choose your competitors and your feedback sources separately. The agent can work from your lists, add to them or suggest a starting point.

## Give it a try

Open the project in an AI tool with web access and point it to [WORKFLOW.md](WORKFLOW.md). Then tell it what you're interested in:

> Set up a weekly brief for a team scheduling app. Focus on onboarding and flag major changes elsewhere. Suggest competitors for the UK market. Discover where people discuss those competitors, but use only our community forum and app-store listing for feedback about us. Show me the proposed setup first.

See the [user guide](docs/USER-GUIDE.md) for a walkthrough from setup to your first weekly report.

## Running it in your setup

| If you're using | Start here |
| --- | --- |
| An AI tool with web access | Give it [WORKFLOW.md](WORKFLOW.md) and a copy of [config.example.json](config.example.json) with your settings. Use its scheduler if it has one. |
| A terminal or external scheduler | Run [agent.py](agent.py) with your own research and model adapters. The [user guide](docs/USER-GUIDE.md#run-from-a-terminal) covers the commands and adapter requirements. |

The workflow is shared across tools. Web access, background runs and delivery depend on the host or adapters you use. The example config contains placeholder adapter commands.
