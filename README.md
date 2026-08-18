# Super Speedy Imports — demo data

Large, on-demand demo imports for the [Super Speedy Imports](https://www.superspeedyplugins.com/)
plugin. The plugin's **Demo Data** tab fetches `manifest.json` from this repo when the user clicks
"Browse demo data from GitHub", lists the demos, and downloads the one they pick (CSV + config)
into their site — nothing is downloaded until the user asks for it.

## What's here

| Demo | Rows | CSV | Requires |
|---|---|---|---|
| `posts-100k` | 100,000 posts, no images | ~34 MB | — |
| `simple-products-100k` | 100,000 simple products, colour-matched external images | ~29 MB | WooCommerce |
| `variable-products-55k` | 5,000 variable parents + 50,000 variations, ten variations per parent | ~14 MB | WooCommerce, **Pro** |
| `variable-products-500k` | 100,000 variable products × 5 rows, colour + size variations | ~144 MB | WooCommerce, **Pro** |

Each demo folder holds the small, committed files:

```
<slug>/
  config.json        # SSI import config (mappings) — pure data, no PHP functions
  taxonomies.json    # taxonomy registrations (products only)
  sample.json        # display metadata (name, description, rows, features)
  data.csv           # the demo CSV — GIT-IGNORED, published as a Release asset
```

`manifest.json` (repo root) is the catalogue the plugin reads: per demo it lists the name,
row count, `requires`, the raw URLs for the JSON, and the **Release-asset URL + size + sha256**
for the CSV. The plugin verifies the sha256 after downloading.

## Publishing

Small JSON is served **raw from `main`**; the big CSVs are **GitHub Release assets** (CDN-backed,
no repo bloat). After regenerating:

```sh
# 1. commit the small files (CSVs are git-ignored)
git add -A && git commit -m "regenerate demo data" && git push

# 2. stage the CSVs under their asset names (the asset filename = the file basename,
#    and manifest.json expects <slug>.csv), then publish as Release assets:
tmp=$(mktemp -d)
for slug in posts-100k simple-products-100k variable-products-55k variable-products-500k; do
  cp "$slug/data.csv" "$tmp/$slug.csv"
done
gh release create v1 "$tmp"/*.csv \
  --title "Demo data v1" --notes "Demo CSVs for Super Speedy Imports."
# (to refresh an existing release instead: gh release upload v1 "$tmp"/*.csv --clobber)
```

The manifest's `release_base` points at `releases/latest/download/`, so re-uploading assets to the
`latest` release keeps the URLs stable.

**The repo must be PUBLIC** for end-user sites to fetch the manifest (raw) and the CSVs (release
assets) without authentication.

## Regenerating

`python3 generate-demo-data.py` — deterministic (fixed seed `20260713`), self-contained, rewrites
every folder + `manifest.json` (recomputing sizes and sha256). Edit `ORG`/`REPO` at the top if the
repo ever moves.

## Notes

- Configs are **pure data** — no `functions` key, no `{function: …}` mappings — so they are safe to
  download into the wp.org (Lite) edition. The plugin rejects any config that violates this.
- Product demos use **external image URLs** (colour-matched `placehold.co`), so importing 100k–500k
  items does not download 100k–500k images.
