# DNS walkthrough — what really happens when you visit `ahmed-eldasoky.pages.dev`

*Written for a non-technical reader. This is the DNS section of the PF-04 assignment: "Personal Website Live on the FlyRank Domain".*

## Why DNS exists

Computers don't talk to each other by names. Every server on the internet has a numeric address called an **IP address** (something like `104.21.x.x`), and that is the only thing a browser can actually connect to. But nobody wants to memorise numbers — we want to type `ahmed-eldasoky.pages.dev` and get the site.

**DNS (Domain Name System) is the internet's phonebook.** It translates human-friendly names into machine-friendly IP addresses. When you ask for a name, the phonebook answers with the address to connect to.

## The name itself: subdomain → domain

A name like `ahmed-eldasoky.pages.dev` reads right-to-left as the hierarchy bottoms-out:

- `dev` is a **top-level domain** (like `.com`).
- `pages` is a subdomain of `dev`, owned by Cloudflare — it hosts all of Cloudflare Pages' free URLs.
- `ahmed-eldasoky` is a subdomain of `pages.dev` — **my** little slice of it, pointing at my site.

## A CNAME record — what it is and why it's here

The phonebook stores *records*. Each record is a line that says "this name maps to that thing". The two most common ones:

- **A record** — maps a name directly to an IP address (e.g. `example.com → 104.21.2.3`).
- **CNAME record** — maps a name to *another name* (an alias). e.g. `www → example.com`.

My site has no custom domain yet, so it just lives on Cloudflare's infrastructure. But if I later buy a domain like `ahmed-eldasoky.com`, I don't need to know Cloudflare's current IP addresses at all. I simply add one **CNAME** record at my registrar:

```
ahmed-eldasoky.com  CNAME  ahmed-eldasoky.pages.dev
```

That says: "whatever `ahmed-eldasoky.pages.dev` resolves to, `ahmed-eldasoky.com` should resolve to the same thing." Cloudflare keeps the actual IPs updated behind the scenes, so my alias never points at a stale address. That indirection is the whole point of a CNAME — **you alias a name, and the owner of the real name manages the address.**

## The full journey (resolver → nameserver → record → response)

When I type the URL and hit Enter:

1. **Check what we already know.** The browser and the operating system look in their local caches first — DNS answers are cached to avoid re-asking every time.
2. **The resolver.** The request goes to a *recursive resolver* — a server that does the legwork, usually one from my ISP or a public one like Cloudflare's `1.1.1.1`. The resolver asks: "what is the IP for `ahmed-eldasoky.pages.dev`?"
3. **Climbing the tree of nameservers.** The resolver doesn't know, so it walks the hierarchy. It asks the root servers for `.dev`, which reply "ask the `dev` nameservers"; it asks the `dev` nameservers for `pages.dev`, which reply "ask Cloudflare's nameservers". Cloudflare's servers are the **authoritative nameservers** for `pages.dev` — meaning *they* have the real records.
4. **The record.** The authoritative server finds the matching record for `ahmed-eldasoky` and answers with the actual IP address (in my case it's a CNAME-style answer that resolves to the Cloudflare edge).
5. **The response.** The resolver hands the IP back to the browser, caches it, and the browser opens a connection to that address.
6. **HTTPS on top.** The connection is secured with TLS, and Cloudflare Pages automatically issues a free SSL certificate for the URL, so everything arrives encrypted.

So: **you ask a name → resolvers walk the DNS hierarchy → an authoritative nameserver answers with the record → your browser connects to the IP → the site loads over HTTPS.** The whole round trip usually takes a few milliseconds because of caching.