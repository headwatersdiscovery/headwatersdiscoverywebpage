# Deploying headwatersdiscovery.org

The site is a single static page, served by GitHub Pages from the `docs/`
folder on the `main` branch of this repository. Only files inside `docs/` are
published; everything else in the repo (this file, `video/` tooling) is not.

```
docs/
  index.html      the page
  assets/         favicon, background video, poster image
  CNAME           tells GitHub Pages to serve at headwatersdiscovery.org
  .nojekyll       serve files as-is (skip GitHub's Jekyll build)
```

## 1. Turn on GitHub Pages

1. Open the repository on GitHub:
   https://github.com/vhsvhs/headwatersdiscoverywebpage
2. Go to **Settings → Pages**.
3. Under **Build and deployment**, set:
   - **Source:** Deploy from a branch
   - **Branch:** `main`, folder `/docs`
4. Click **Save**.
5. Under **Custom domain**, confirm it shows `headwatersdiscovery.org`
   (it is read from `docs/CNAME`). If it is blank, type it in and save.

Within a minute or two the site will also be reachable at
`https://vhsvhs.github.io/headwatersdiscoverywebpage/`, which is a handy check
before DNS is set up.

> GitHub Pages on a free account requires the repository to be **public**.
> See [Alternative: private repository](#alternative-private-repository) if
> that is a concern.

## 2. Point the domain at GitHub Pages

At the registrar or DNS provider for `headwatersdiscovery.org`, create these
records (delete any existing A/AAAA records for the bare domain first, such as
a registrar "parking" page):

| Type  | Host / Name | Value                 |
|-------|-------------|-----------------------|
| A     | `@`         | `185.199.108.153`     |
| A     | `@`         | `185.199.109.153`     |
| A     | `@`         | `185.199.110.153`     |
| A     | `@`         | `185.199.111.153`     |
| CNAME | `www`       | `vhsvhs.github.io`    |

Optional, for IPv6 visitors:

| Type  | Host / Name | Value                 |
|-------|-------------|-----------------------|
| AAAA  | `@`         | `2606:50c0:8000::153` |
| AAAA  | `@`         | `2606:50c0:8001::153` |
| AAAA  | `@`         | `2606:50c0:8002::153` |
| AAAA  | `@`         | `2606:50c0:8003::153` |

DNS changes usually take effect within minutes but can take up to 24–48 hours.

### Check DNS from a terminal

```sh
dig headwatersdiscovery.org +short       # should list the four 185.199.x.153 addresses
dig www.headwatersdiscovery.org +short   # should show vhsvhs.github.io. then the same addresses
```

## 3. Turn on HTTPS

Once DNS resolves, return to **Settings → Pages**. GitHub issues a free TLS
certificate automatically (this can take up to an hour after DNS is correct).
When the **Enforce HTTPS** checkbox becomes available, tick it.

Then visit https://headwatersdiscovery.org and https://www.headwatersdiscovery.org
— both should load the page.

## 4. (Recommended) Verify the domain with GitHub

This prevents anyone else from claiming `headwatersdiscovery.org` on GitHub
Pages if the repo's Pages setting is ever turned off.

1. Go to your GitHub account **Settings → Pages** (account settings, not the
   repository's), and click **Add a domain**.
2. Enter `headwatersdiscovery.org`. GitHub shows a TXT record to create.
3. Add that TXT record at your DNS provider, then click **Verify**.

## Updating the site

Edit `docs/index.html` (or files in `docs/assets/`), then commit and push to `main`.
GitHub Pages redeploys automatically within a minute or two.

Keep non-site files (drafts, internal documents, source footage) out of
`docs/`. Only `docs/` is served as the website, but if the repository is public
every committed file is still visible on GitHub. Stage
files by name rather than with `git add .`.

## Troubleshooting

- **"Domain's DNS record could not be retrieved" / not yet configured:** DNS
  has not propagated yet. Re-check with `dig` and wait.
- **Enforce HTTPS is greyed out:** the certificate is still being issued.
  Wait up to an hour after DNS is correct. If it stays stuck, remove the
  custom domain in Settings → Pages, save, re-add it, and save again.
- **404 at the custom domain:** confirm Pages is deployed from `main` /
  `/docs` and that `docs/CNAME` still exists.
- **Old version still showing:** hard-refresh the browser (Cmd+Shift+R), or
  check the **Actions** tab for the latest "pages build and deployment" run.

## Alternative: private repository

To keep the source private, use a host that serves static sites from private
repos for free:

- **Netlify:** Add new site → Import from GitHub → pick this repo. Leave the
  build command empty and set the publish directory to `docs`. Then add
  `headwatersdiscovery.org` under Domain management and follow Netlify's DNS
  instructions.
- **Cloudflare Pages:** Workers & Pages → Create → Pages → Connect to Git →
  pick this repo. Use no build command and output directory `docs`. Add the custom
  domain under the project's Custom domains tab.

If you switch hosts, delete `docs/CNAME` (it is only used by GitHub Pages)
and use the DNS records the new host gives you instead of the ones above.
