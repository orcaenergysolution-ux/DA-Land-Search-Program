# Putting the Property Finder online (Streamlit)

The app is ready and committed to git. Three steps: create a GitHub repo, push,
then point Streamlit at it.

---

## 1. Create an empty repo on GitHub

1. Go to <https://github.com/new>
2. **Repository name:** `land-search` (any name is fine)
3. **Private** is recommended (see the warning at the bottom)
4. Do **not** tick "Add a README", "Add .gitignore", or "Choose a license" —
   the repo must start empty or the first push will be rejected
5. Click **Create repository**

GitHub then shows a URL like `https://github.com/YOURNAME/land-search.git`.

## 2. Push this project

In the project folder, run these two commands (replace the URL with yours):

```bash
git remote add origin https://github.com/YOURNAME/land-search.git
git push -u origin main
```

The first push asks you to sign in to GitHub — a browser window opens, or you
paste a Personal Access Token. About 18 MB uploads.

If it says "remote origin already exists", run
`git remote set-url origin https://github.com/YOURNAME/land-search.git` instead.

## 3. Deploy on Streamlit

1. Go to <https://share.streamlit.io> and sign in **with GitHub**
2. Click **Create app** → **Deploy a public app from a repository**
3. Fill in:
   - **Repository:** `YOURNAME/land-search`
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
4. Click **Deploy**

First build takes 2–5 minutes. You then get a permanent URL like
`https://land-search.streamlit.app` that you can send to your client.

---

## Optional: enable the paid listings search

The deployed app shows **only the free cadastre search** unless you give it an
Apify key. To turn on the "properties for sale" mode:

1. In Streamlit, open your app → **⋮ (menu)** → **Settings** → **Secrets**
2. Paste this and save:

   ```toml
   APIFY_TOKEN = "apify_api_xxxxxxxxxxxxxxxxxxxx"
   ```

The app restarts and the listings option appears.

### ⚠ Read this before adding the key

**Streamlit Community Cloud apps are public by default — anyone with the link
can use them.** If you add your Apify key, any visitor can run scrapes that
spend *your* credit. Options, safest first:

- **Don't add the key.** The free parcel search is fully functional without it.
  This is the default and needs no decisions.
- **Restrict who can view the app** (app **Settings → Sharing**), then add the key.
- **Set a spending cap** at <https://console.apify.com/billing> → Limits.

---

## Keeping it updated

Whenever you change the code:

```bash
git add -A
git commit -m "describe what changed"
git push
```

Streamlit redeploys automatically within a minute.

---

## What is and isn't uploaded

**Uploaded** (~18 MB): the app, the search code, and
`data/intermediate/transmission_lines.geojson` (the power line map the app needs).

**Never uploaded**, via `.gitignore`:

- `data/apify_token.txt` — your API key
- `data/inputs/` — ~600 MB of permit PDFs the web app doesn't use
- `outputs/` — generated reports and scraped data

These all stay on your computer. `.gitignore` only controls what goes to GitHub;
it never deletes anything.

---

## Running it locally

The browser version still works exactly as before:

```
Start Property Finder.bat
```

Or the Streamlit version locally:

```bash
python -m streamlit run streamlit_app.py
```
