#!/usr/bin/env python3
"""Generate the large, on-demand demo imports for super-speedy-imports-demo-data.

Deterministic (fixed seed, no timestamps) so re-running produces identical CSVs.
Self-contained: does NOT read anything from the plugin repo.

Produces three demos, each in its own folder (config.json + taxonomies.json +
sample.json committed to git; data.csv is git-ignored and uploaded as a GitHub
Release asset named <slug>.csv):

  posts-100k/              100,000 posts, no images (bulk-speed demo)          [Lite + Pro]
  simple-products-100k/    100,000 simple products, colour-matched EXTERNAL
                           images (no download during import)                  [Lite + Pro]
  variable-products-500k/  100,000 variable products x 5 rows = 500,000 rows,
                           colour + size variations, colour-matched external
                           images                                             [Pro only]

Then writes manifest.json at the repo root (name, rows, size, sha256, requires,
and the URLs the plugin's Demo Data tab fetches).

Usage: python3 generate-demo-data.py
"""
import csv
import hashlib
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
rng = random.Random(20260713)

ORG = 'superspeedyplugins'
REPO = 'super-speedy-imports-demo-data'
RAW_BASE = 'https://raw.githubusercontent.com/%s/%s/main' % (ORG, REPO)
RELEASE_BASE = 'https://github.com/%s/%s/releases/latest/download' % (ORG, REPO)


def write_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)
        f.write('\n')


def ensure(slug):
    d = os.path.join(HERE, slug)
    os.makedirs(d, exist_ok=True)
    return d


def sha256_and_size(path):
    h = hashlib.sha256()
    size = 0
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


# ---------------------------------------------------------------------------
# Taxonomy registrations (inlined so this repo is self-contained)
# ---------------------------------------------------------------------------
def tax(name, label, hierarchical, public, query_var, count_cb, slug_rewrite):
    return {
        'name': name,
        'args': {
            'name': name, 'label': label, 'description': '',
            'public': public, 'publicly_queryable': public,
            'hierarchical': hierarchical,
            'show_ui': True, 'show_in_menu': public, 'show_in_nav_menus': public,
            'show_tagcloud': True, 'show_in_quick_edit': hierarchical,
            'show_admin_column': name == 'product_brand',
            'meta_box_cb': 'post_categories_meta_box' if hierarchical else False,
            'meta_box_sanitize_cb': ('taxonomy_meta_box_sanitize_cb_checkboxes'
                                     if hierarchical else 'taxonomy_meta_box_sanitize_cb_input'),
            'rewrite': ({'with_front': False, 'hierarchical': hierarchical,
                         'ep_mask': 0, 'slug': slug_rewrite} if slug_rewrite else False),
            'query_var': query_var,
            'update_count_callback': count_cb,
            'show_in_rest': public, 'rest_base': False, 'rest_namespace': 'wp/v2' if public else False,
            'rest_controller_class': False, 'rest_controller': None,
            'default_term': None, 'sort': None if hierarchical else False, 'args': None,
            '_builtin': False,
        },
    }


TAX_PRODUCT_CAT = tax('product_cat', 'Product categories', True, True, 'product_cat',
                      '_wc_term_recount', 'product-category')
TAX_PRODUCT_BRAND = tax('product_brand', 'Brands', True, True, 'product_brand',
                        '_update_post_term_count', 'brand')
TAX_PA_COLOR = tax('pa_color', 'Product Color', False, False, False,
                   '_update_post_term_count', None)
TAX_PA_SIZE = tax('pa_size', 'Product Size', False, False, False,
                  '_update_post_term_count', None)


# ---------------------------------------------------------------------------
# Posts (no images — bulk speed)
# ---------------------------------------------------------------------------
POST_CATS = [
    'News > Technology', 'News > Business', 'News > Science',
    'Guides > How-To', 'Guides > Reviews', 'Guides > Buying Advice',
    'Lifestyle > Travel', 'Lifestyle > Food', 'Lifestyle > Fitness',
    'Opinion > Editorials',
]
POST_TAGS = ['wordpress', 'imports', 'performance', 'tutorial', 'analysis', 'trends',
             'productivity', 'tools', 'data', 'automation', 'speed', 'benchmark',
             'review', 'comparison', 'beginners', 'advanced', 'opensource', 'cloud',
             'security', 'design']
TOPICS = ['content migration', 'site performance', 'bulk editing', 'database tuning',
          'product catalogues', 'CSV workflows', 'search indexing', 'image handling',
          'caching strategies', 'schema markup', 'server scaling', 'plugin conflicts',
          'theme development', 'API integrations', 'backup strategies', 'staging sites']
ANGLES = ['A practical look at', 'What nobody tells you about', 'Getting started with',
          'The complete guide to', 'Five lessons from', 'Rethinking', 'A deep dive into',
          'Common mistakes in', 'The future of', 'Benchmarking']


def gen_posts_100k(slug, count):
    d = ensure(slug)
    header = ['Reference', 'Title', 'Content', 'Excerpt', 'Categories', 'Tags', 'Date']
    with open(os.path.join(d, 'data.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        for i in range(1, count + 1):
            topic = TOPICS[i % len(TOPICS)]
            angle = ANGLES[(i // len(TOPICS)) % len(ANGLES)]
            title = '%s %s #%d' % (angle, topic, i)
            content = ('%s %s, written as demo post number %d for Super Speedy Imports. '
                       'It exists so you can watch a very large post import run at full '
                       'speed, then safely undo it.' % (angle, topic, i))
            excerpt = 'Demo post %d about %s.' % (i, topic)
            cats = POST_CATS[i % len(POST_CATS)]
            tags = ', '.join(rng.sample(POST_TAGS, rng.randint(2, 4)))
            day = i % 1950
            date = '%04d-%02d-%02d %02d:%02d:00' % (
                2021 + day // 365, 1 + (day % 365) // 31 % 12, 1 + day % 28, i % 24, i % 60)
            w.writerow(['POST-%06d' % i, title, content, excerpt, cats, tags, date])
    write_json(os.path.join(d, 'config.json'), {
        'base_template': 'SSI_PostTemplate',
        'template_mappings': {
            'post_title': 'Title', 'post_content': 'Content',
            'post_excerpt': 'Excerpt', 'post_date': 'Date',
            'taxonomies': {
                'category': {'separator': '>', 'source': 'Categories', 'is_variable': False},
                'post_tag': {'source': 'Tags', 'is_variable': ''},
            },
            'post_meta': {'demo_reference': 'Reference'},
            'media': {'featured_image': ''},
        },
        'functions': None,
        'additional_options': {
            'unique_id_components': ['meta:demo_reference'],
            'delete_items': False, 'keep_sold_items': True,
            'force_delete': False, 'continue_on_error': False,
        },
    })
    write_json(os.path.join(d, 'sample.json'), {
        'name': 'Posts (100,000, no images)',
        'description': 'One hundred thousand blog posts with hierarchical categories, '
                       'tags and dates but no images - the bulk-speed demo.',
        'post_type': 'post', 'rows': count,
        'features': ['Bulk speed demo', 'Categories', 'Tags', 'Post dates'],
    })
    return count


# ---------------------------------------------------------------------------
# Colour-matched external images (placehold.co, no download during import)
# ---------------------------------------------------------------------------
COLOURS = [
    ('Red', 'E23B3B', 'FFFFFF'), ('Blue', '2E6BE6', 'FFFFFF'),
    ('Green', '2FA84F', 'FFFFFF'), ('Black', '222222', 'FFFFFF'),
    ('White', 'F5F5F5', '333333'), ('Yellow', 'F2C230', '333333'),
    ('Purple', '8E44AD', 'FFFFFF'), ('Orange', 'E67E22', 'FFFFFF'),
]
SIZES = ['Small', 'Medium', 'Large', 'XL']
PRODUCT_TYPES = [
    ('T-Shirt', 'Clothing > T-Shirts', 15), ('Hoodie', 'Clothing > Hoodies', 35),
    ('Jacket', 'Clothing > Jackets', 60), ('Jeans', 'Clothing > Jeans', 45),
    ('Shorts', 'Clothing > Shorts', 25), ('Dress', 'Clothing > Dresses', 50),
    ('Sweater', 'Clothing > Sweaters', 40), ('Polo', 'Clothing > Polos', 28),
    ('Vest', 'Clothing > Vests', 22), ('Cardigan', 'Clothing > Cardigans', 38),
    ('Skirt', 'Clothing > Skirts', 30), ('Coat', 'Clothing > Coats', 80),
]
BRANDS = ['Acme', 'Globex', 'Initech', 'Umbrella', 'Soylent', 'Stark', 'Wayne', 'Wonka']
ADJECTIVES = ['Classic', 'Premium', 'Urban', 'Vintage', 'Sport', 'Casual', 'Modern',
              'Deluxe', 'Essential', 'Signature']


def colour_image(colour, ptype):
    name, bg, fg = colour
    label = ('%s %s' % (name, ptype)).replace(' ', '+')
    return 'https://placehold.co/600x600/%s/%s.png?text=%s' % (bg, fg, label)


def gen_simple_100k(slug, count):
    d = ensure(slug)
    header = ['SKU', 'Name', 'Description', 'Regular_Price', 'Sale_Price', 'Stock',
              'Weight', 'Manage_Stock', 'Categories', 'Brand', 'Color', 'External_Image']
    with open(os.path.join(d, 'data.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        for i in range(1, count + 1):
            ptype, cat, base = PRODUCT_TYPES[i % len(PRODUCT_TYPES)]
            adj = ADJECTIVES[i % len(ADJECTIVES)]
            colour = COLOURS[i % len(COLOURS)]
            brand = BRANDS[i % len(BRANDS)]
            name = '%s %s %s %06d' % (adj, colour[0], ptype, i)
            desc = ('The %s %s is a %s-quality %s in %s. Simple demo product #%d for '
                    'Super Speedy Imports, with a colour-matched external image.'
                    % (adj.lower(), ptype.lower(), adj.lower(), ptype.lower(),
                       colour[0].lower(), i))
            price = base + (i % 10)
            sale = '%.2f' % (price * 0.8) if i % 5 == 0 else ''
            w.writerow(['SIMPLE-%06d' % i, name, desc, '%.2f' % price, sale,
                        str(5 + i % 40), '%.2f' % (0.2 + (i % 20) / 10.0), 'yes',
                        cat, brand, colour[0], colour_image(colour, ptype)])
    write_json(os.path.join(d, 'config.json'), {
        'base_template': 'SSI_WooCommerceProductTemplate',
        'template_mappings': {
            'post_title': 'Name', 'post_content': 'Description', 'post_status': '',
            'parent_sku': '',
            'taxonomies': {
                'product_cat': {'separator': '>', 'source': 'Categories', 'is_variable': False},
                'product_brand': {'separator': '>', 'source': 'Brand', 'is_variable': False},
                'pa_color': {'source': 'Color', 'is_variable': ''},
            },
            'post_meta': {
                '_sku': 'SKU', '_regular_price': 'Regular_Price', '_sale_price': 'Sale_Price',
                '_stock': 'Stock', '_manage_stock': 'Manage_Stock', '_weight': 'Weight',
                'external_image_url': 'External_Image',
            },
            'media': {'featured_image': '', 'gallery_images': ''},
        },
        'functions': None,
        'additional_options': {
            'delete_items': False, 'keep_sold_items': True,
            'force_delete': False, 'continue_on_error': False,
        },
    })
    write_json(os.path.join(d, 'taxonomies.json'),
               {'post_type': 'product', 'taxonomies': [TAX_PRODUCT_CAT, TAX_PRODUCT_BRAND, TAX_PA_COLOR]})
    write_json(os.path.join(d, 'sample.json'), {
        'name': 'Simple Products (100,000)',
        'description': 'One hundred thousand simple WooCommerce products with categories, '
                       'brands, colours, prices and stock. Colour-matched external images '
                       '(no image download during the import). Requires WooCommerce.',
        'post_type': 'product', 'rows': count,
        'features': ['Simple products', 'Categories', 'Brands', 'Colour attribute',
                     'External images (no download)'],
    })
    return count


def gen_variable_500k(slug, parents):
    d = ensure(slug)
    header = ['SKU', 'Name', 'Type', 'Description', 'Short_Description',
              'Regular_Price', 'Sale_Price', 'Stock', 'Manage_Stock',
              'Categories', 'Color', 'Size', 'Parent_SKU', 'External_Images']
    rows = 0
    with open(os.path.join(d, 'data.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        for i in range(1, parents + 1):
            ptype, cat, base = PRODUCT_TYPES[i % len(PRODUCT_TYPES)]
            adj = ADJECTIVES[i % len(ADJECTIVES)]
            name = '%s %s %06d' % (adj, ptype, i)
            sku = 'VAR-%06d' % i
            c1 = COLOURS[i % len(COLOURS)]
            c2 = COLOURS[(i + 3) % len(COLOURS)]
            s1, s2 = SIZES[i % 3], SIZES[i % 3 + 1]
            desc = ('The %s %s comes in %s or %s, sizes %s and %s. Demo variable product '
                    '#%d for Super Speedy Imports, colour-matched external images.'
                    % (adj.lower(), ptype.lower(), c1[0].lower(), c2[0].lower(), s1, s2, i))
            gallery = '|'.join([colour_image(c1, ptype), colour_image(c2, ptype)])
            w.writerow([sku, name, 'variable', desc, 'A %s %s.' % (adj.lower(), ptype.lower()),
                        '', '', '', '', cat, '%s, %s' % (c1[0], c2[0]),
                        '%s, %s' % (s1, s2), '', gallery])
            rows += 1
            price = base + (i % 10)
            for colour in (c1, c2):
                for size in (s1, s2):
                    vsku = '%s-%s-%s' % (sku, colour[0][:3].upper(), size[:1])
                    sale = '%.2f' % (price * 0.8) if (i + len(size)) % 5 == 0 else ''
                    w.writerow([vsku, '%s %s %s' % (name, colour[0], size), 'variation',
                                '%s in %s, size %s.' % (name, colour[0].lower(), size),
                                '%s %s.' % (colour[0], size), '%.2f' % price, sale,
                                str(5 + (i + rows) % 40), 'yes', cat, colour[0], size,
                                sku, colour_image(colour, ptype)])
                    rows += 1
    write_json(os.path.join(d, 'config.json'), {
        'base_template': 'SSI_WooCommerceProductTemplate',
        'template_mappings': {
            'post_title': 'Name', 'post_content': 'Description',
            'post_excerpt': 'Short_Description',
            '_parent_ssi_unique_item_id': 'Parent_SKU',
            'taxonomies': {
                'product_cat': {'separator': '>', 'source': 'Categories', 'is_variable': False},
                'pa_color': {'source': 'Color', 'is_variable': '1'},
                'pa_size': {'source': 'Size', 'is_variable': '1'},
            },
            'post_meta': {
                'external_image_url': 'External_Images',
                '_sku': 'SKU', '_regular_price': 'Regular_Price', '_sale_price': 'Sale_Price',
                '_stock': 'Stock', '_manage_stock': 'Manage_Stock',
            },
            'media': {'featured_image': '', 'gallery_images': ''},
        },
        'functions': None,
        'additional_options': {
            'variation_import_type': 'mixed',
            'delete_items': False, 'keep_sold_items': True,
            'force_delete': False, 'continue_on_error': False,
        },
    })
    write_json(os.path.join(d, 'taxonomies.json'),
               {'post_type': 'product', 'taxonomies': [TAX_PRODUCT_CAT, TAX_PA_COLOR, TAX_PA_SIZE]})
    write_json(os.path.join(d, 'sample.json'), {
        'name': 'Variable Products (500,000 rows)',
        'description': '100,000 variable products x 5 rows (colour and size variations), '
                       'with colour-matched external images. Requires WooCommerce. '
                       'Pro only: the Lite edition does not import variable products.',
        'post_type': 'product', 'rows': rows,
        'features': ['Variable products', 'Colour + size attributes',
                     'External images (no download)', 'Categories'],
    })
    return rows


# ---------------------------------------------------------------------------
# Generate + manifest
# ---------------------------------------------------------------------------
DEMOS = [
    ('posts-100k', [], gen_posts_100k, ('posts-100k', 100000)),
    ('simple-products-100k', ['woocommerce'], gen_simple_100k, ('simple-products-100k', 100000)),
    ('variable-products-500k', ['woocommerce', 'pro'], gen_variable_500k,
     ('variable-products-500k', 100000)),
]

manifest_demos = []
for slug, requires, fn, args in DEMOS:
    print('generating %s ...' % slug)
    rows = fn(*args)
    csv_path = os.path.join(HERE, slug, 'data.csv')
    digest, size = sha256_and_size(csv_path)
    meta = json.load(open(os.path.join(HERE, slug, 'sample.json')))
    has_tax = os.path.exists(os.path.join(HERE, slug, 'taxonomies.json'))
    manifest_demos.append({
        'slug': slug,
        'name': meta['name'],
        'description': meta['description'],
        'post_type': meta['post_type'],
        'rows': rows,
        'requires': requires,
        'min_plugin_version': '2.71.0',
        # Large CSV: uploaded as a flat GitHub Release asset named <slug>.csv.
        'csv_asset': '%s.csv' % slug,
        'csv_url': '%s/%s.csv' % (RELEASE_BASE, slug),
        'csv_size_bytes': size,
        'csv_sha256': digest,
        # Small JSON: committed to the repo, served raw.
        'config_url': '%s/%s/config.json' % (RAW_BASE, slug),
        'sample_url': '%s/%s/sample.json' % (RAW_BASE, slug),
        'taxonomies_url': ('%s/%s/taxonomies.json' % (RAW_BASE, slug)) if has_tax else None,
    })
    print('  %s rows, %.1f MB' % (rows, size / 1048576.0))

write_json(os.path.join(HERE, 'manifest.json'), {
    'schema': 1,
    'generated_seed': 20260713,
    'repo': '%s/%s' % (ORG, REPO),
    'note': ('Demo catalogue for Super Speedy Imports. Large CSVs are GitHub Release '
             'assets (git-ignored here); small JSON is served raw from main. If the '
             'org/repo differs, re-run after editing ORG/REPO at the top of the generator.'),
    'raw_base': RAW_BASE,
    'release_base': RELEASE_BASE,
    'demos': manifest_demos,
})
print('manifest.json written.')
