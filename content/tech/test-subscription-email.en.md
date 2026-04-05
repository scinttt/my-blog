+++
date = '2026-04-04T10:30:00-04:00'
draft = false
title = 'Test Post: Checking the Subscription Email Layout'
summary = "A short test article created to preview how this blog appears inside the subscription email, including the title, summary, and opening paragraphs."
tags = ['Test', 'Newsletter', 'Tech']
categories = ['tech']
+++

This is a test post for the blog subscription flow.

The goal is simple: once the email pipeline picks up a newly published article, this post should make it easy to inspect what subscribers actually receive in their inbox.

If the email template is working well, you should expect three things to look clean:

- The subject line or headline should use the post title.
- The preview text should come from the summary.
- The body excerpt should render short paragraphs without broken formatting.

That is all this post needs to do. It is not trying to be insightful. It is trying to be predictable.

If this email looks odd, the likely places to inspect next are the email service template, the RSS parsing logic, and how the summary field is mapped into the outgoing payload.
