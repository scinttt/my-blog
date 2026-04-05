# Renren Zhang's Blog

Personal blog built with Hugo + PaperMod and deployed on Vercel.

Live site: [creaturelove7.com](https://www.creaturelove7.com/)

## Overview

This repository contains the Hugo site for a bilingual personal blog.

Current features:
- English and Chinese content with Hugo multilingual routing
- Full-screen search overlay backed by Hugo JSON indexes
- Related posts based on tags
- Footer email subscribe form with an explicitly configured external API endpoint
- Deploy-triggered post email delivery for newly changed English posts, with the external email service handling dedupe

## Repository Scope

This repository is the blog frontend only.

The subscribe UI in `layouts/partials/subscribe.html` does not hardcode any production email endpoint.

Set `params.subscribe.endpoint` in `hugo.toml` when you want the subscribe form enabled.

If it is left empty, the form stays disabled and shows a configuration message instead of sending requests anywhere.

The email backend is not included in this repository. If it is open-sourced separately, link that repository here and document the API contract, required environment variables, data model, and deployment steps there.

## Local Development

Prerequisites:
- Hugo Extended `>= 0.155.3`

Run locally:

```bash
git clone https://github.com/scinttt/my-blog.git
cd my-blog
hugo server -D
```

Production build:

```bash
hugo --gc --minify
```

Example subscribe endpoint configuration in `hugo.toml`:

```toml
[params.subscribe]
  endpoint = "https://your-email-service.example.com/api/subscribe"
```

## Post Email Delivery

This repository triggers new post emails after `main` deployments.

The workflow in `.github/workflows/notify-new-posts.yml` does the following:

- Detects changed `content/**/*.en.md` files on pushes to `main`
- Skips `draft = true`, `search.en.md`, and `_index.en.md`
- Polls the production RSS feed until the new article is live
- Calls the external email service `POST /api/send` endpoint with the exact post URL

Required GitHub Actions secrets:

- `EMAIL_SEND_API_URL`
- `EMAIL_SEND_API_TOKEN`

The email backend still keeps its cron job as a fallback path, but deployment-triggered delivery is the primary path for new post notifications.

This repository intentionally does not hardcode a production `POST /api/send` endpoint in the workflow. Forks and open-source users must configure their own email service endpoint and token.

## Content Authoring

Create a new post with the project archetype:

```bash
hugo new content/tech/my-post.en.md
```

Use `*.en.md` and `*.zh.md` filename suffixes for bilingual content pairs.

## Open Source Notes

Before publishing the email workflow as open source, make sure the following are documented in the backend repository or linked from here:
- API contract for subscribe requests and responses
- Required environment variables and secret management
- Database schema and migration steps
- Abuse prevention, rate limiting, and bot mitigation
- Double opt-in, unsubscribe, and privacy policy expectations

## License

Code in this repository is licensed under the MIT License.

Written blog content under `content/` is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
