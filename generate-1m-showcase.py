#!/usr/bin/env python3
"""Generate the 1,000,000-row simple-product SHOWCASE demo for Super Speedy Imports.

Self-contained and deterministic (fixed seed, no timestamps) so re-running produces
an identical CSV. Kept SEPARATE from generate-demo-data.py on purpose: it must not
perturb the RNG state or manifest sha256s of the existing posts-100k /
simple-products-100k / variable-products-500k demos.

Writes simple-products-1m/{data.csv, config.json, taxonomies.json, sample.json}.
data.csv is git-ignored (like the other demos) and published as a Release asset.

Each product carries: hierarchical category (gender > garment), a brand (long-tail
distribution), 2-4 tags, and FIVE attributes - colour, size, material, pattern,
style. Images are EXTERNAL (colour+type matched placehold.co, ~96 unique URLs), so
the import does no image downloading. Attributes are drawn INDEPENDENTLY (with light
per-garment plausibility) so every colour x garment combination exists - e.g. a "red
dress" is really in the data - and the colour is in the title so search finds it.

Usage: python3 generate-1m-showcase.py [row_count]   (default 1,000,000)
"""
import csv
import hashlib
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SLUG = 'simple-products-1m'
COUNT = int(sys.argv[1]) if len(sys.argv) > 1 else 1_000_000
rng = random.Random(20260714)  # own seed - independent of generate-demo-data.py

ORG = 'superspeedyplugins'
REPO = 'super-speedy-imports-demo-data'
RAW_BASE = 'https://raw.githubusercontent.com/%s/%s/main' % (ORG, REPO)
RELEASE_BASE = 'https://github.com/%s/%s/releases/latest/download' % (ORG, REPO)


def write_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)
        f.write('\n')


def sha256_and_size(path):
    h = hashlib.sha256()
    size = 0
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


# ---------------------------------------------------------------------------
# Vocabularies
# ---------------------------------------------------------------------------
# (name, bg hex, text hex) - bg is the true colour so a colour-filtered grid
# looks deliberate; text hex keeps the placeholder label legible.
COLOURS = [
    ('Red', 'E23B3B', 'FFFFFF'), ('Blue', '2E6BE6', 'FFFFFF'),
    ('Green', '2FA84F', 'FFFFFF'), ('Black', '222222', 'FFFFFF'),
    ('White', 'F5F5F5', '333333'), ('Yellow', 'F2C230', '333333'),
    ('Purple', '8E44AD', 'FFFFFF'), ('Orange', 'E67E22', 'FFFFFF'),
]
SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
# Patterns: 'Plain' repeated so most clothes are plain, the rest sprinkled in.
PATTERNS = ['Plain', 'Plain', 'Plain', 'Plain', 'Striped', 'Checked',
            'Floral', 'Polka Dot', 'Geometric', 'Camo']
STYLES = ['Casual', 'Formal', 'Sport', 'Vintage', 'Streetwear', 'Minimal', 'Bohemian']

# (type, category leaf, plausible genders, plausible materials, base price)
TYPES = [
    ('T-Shirt',  'T-Shirts', ['Men', 'Women', 'Kids', 'Unisex'],
     ['Cotton', 'Organic Cotton', 'Linen', 'Bamboo', 'Polyester'], 15),
    ('Shirt',    'Shirts',   ['Men', 'Women', 'Unisex'],
     ['Cotton', 'Linen', 'Polyester', 'Silk'], 30),
    ('Polo',     'Polos',    ['Men', 'Women', 'Unisex'],
     ['Cotton', 'Organic Cotton', 'Polyester'], 28),
    ('Hoodie',   'Hoodies',  ['Men', 'Women', 'Kids', 'Unisex'],
     ['Cotton', 'Polyester', 'Wool'], 35),
    ('Sweater',  'Sweaters', ['Men', 'Women', 'Unisex'],
     ['Wool', 'Cotton', 'Polyester'], 40),
    ('Jacket',   'Jackets',  ['Men', 'Women', 'Unisex'],
     ['Leather', 'Wool', 'Polyester', 'Denim', 'Cotton'], 60),
    ('Coat',     'Coats',    ['Men', 'Women', 'Unisex'],
     ['Wool', 'Polyester', 'Leather'], 80),
    ('Jeans',    'Jeans',    ['Men', 'Women', 'Kids', 'Unisex'],
     ['Denim'], 45),
    ('Trousers', 'Trousers', ['Men', 'Women', 'Unisex'],
     ['Cotton', 'Linen', 'Polyester', 'Wool'], 42),
    ('Shorts',   'Shorts',   ['Men', 'Women', 'Kids', 'Unisex'],
     ['Cotton', 'Linen', 'Denim', 'Polyester'], 25),
    ('Dress',    'Dresses',  ['Women'],
     ['Cotton', 'Linen', 'Silk', 'Polyester', 'Wool'], 50),
    ('Skirt',    'Skirts',   ['Women', 'Kids'],
     ['Cotton', 'Linen', 'Silk', 'Polyester', 'Denim'], 30),
]

# ~40 fake brands, drawn with a long-tail (Zipf-ish) weight so a handful dominate.
BRANDS = [
    'Acme', 'Globex', 'Initech', 'Umbrella', 'Soylent', 'Stark', 'Wayne', 'Wonka',
    'Hooli', 'Pied Piper', 'Vandelay', 'Gekko', 'Oscorp', 'Cyberdyne', 'Tyrell',
    'Aperture', 'BlackMesa', 'Massive Dynamic', 'Wentworth', 'Nakatomi', 'Dunder',
    'Prestige', 'Monarch', 'Vault', 'Ollivander', 'Zorg', 'Weyland', 'Buy n Large',
    'Gringotts', 'Sterling', 'Bluth', 'Paper St', 'Los Pollos', 'Krusty',
    'Wernham', 'Spectre', 'Tessier', 'Abstergo', 'Rekall', 'Omni',
]
BRAND_WEIGHTS = [1.0 / (i + 1) for i in range(len(BRANDS))]

TAGS = ['new-in', 'bestseller', 'sale', 'summer', 'winter', 'autumn', 'spring',
        'eco-friendly', 'limited-edition', 'classic', 'trending', 'essentials',
        'workwear', 'weekend', 'party', 'organic', 'premium', 'everyday',
        'lightweight', 'warm']


def colour_image(colour, ptype):
    name, bg, fg = colour
    label = ('%s %s' % (name, ptype)).replace(' ', '+')
    return 'https://placehold.co/600x600/%s/%s.png?text=%s' % (bg, fg, label)


# ---------------------------------------------------------------------------
# Taxonomy registrations (inlined, mirrors generate-demo-data.py's tax())
# ---------------------------------------------------------------------------
def tax(name, label, hierarchical, public, query_var, count_cb, slug_rewrite,
        admin_col=False):
    return {
        'name': name,
        'args': {
            'name': name, 'label': label, 'description': '',
            'public': public, 'publicly_queryable': public,
            'hierarchical': hierarchical,
            'show_ui': True, 'show_in_menu': public, 'show_in_nav_menus': public,
            'show_tagcloud': True, 'show_in_quick_edit': hierarchical,
            'show_admin_column': admin_col,
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


TAXONOMIES = [
    tax('product_cat', 'Product categories', True, True, 'product_cat',
        '_wc_term_recount', 'product-category'),
    tax('product_brand', 'Brands', True, True, 'product_brand',
        '_update_post_term_count', 'brand', admin_col=True),
    tax('pa_color', 'Product Color', False, False, False,
        '_update_post_term_count', None),
    tax('pa_size', 'Product Size', False, False, False,
        '_update_post_term_count', None),
    tax('pa_material', 'Product Material', False, False, False,
        '_update_post_term_count', None),
    tax('pa_pattern', 'Product Pattern', False, False, False,
        '_update_post_term_count', None),
    tax('pa_style', 'Product Style', False, False, False,
        '_update_post_term_count', None),
]


# ---------------------------------------------------------------------------
# Generate
# ---------------------------------------------------------------------------
def generate():
    d = os.path.join(HERE, SLUG)
    os.makedirs(d, exist_ok=True)
    header = ['SKU', 'Name', 'Description', 'Regular_Price', 'Sale_Price', 'Stock',
              'Manage_Stock', 'Categories', 'Brand', 'Tags', 'Color', 'Size',
              'Material', 'Pattern', 'Style', 'External_Image']
    seen_pairs = set()
    with open(os.path.join(d, 'data.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        for i in range(1, COUNT + 1):
            ptype, leaf, genders, materials, base = rng.choice(TYPES)
            colour = rng.choice(COLOURS)
            cname = colour[0]
            gender = rng.choice(genders)
            material = rng.choice(materials)
            pattern = rng.choice(PATTERNS)
            style = rng.choice(STYLES)
            size = rng.choice(SIZES)
            brand = rng.choices(BRANDS, weights=BRAND_WEIGHTS, k=1)[0]
            tags = ', '.join(rng.sample(TAGS, rng.randint(2, 4)))
            seen_pairs.add((cname, ptype))

            # Colour + garment are in the title so "red dress" search works.
            name = '%s %s %s %s %s' % (brand, style, cname, material, ptype)
            desc = ('A %s %s %s in %s. %s pattern, size %s, by %s. Demo product for '
                    'Super Speedy Imports.'
                    % (style.lower(), cname.lower(), ptype.lower(), material.lower(),
                       pattern, size, brand))
            category = '%s > %s' % (gender, leaf)
            price = base + rng.randint(0, 15) + round(rng.random(), 2)
            regular = '%.2f' % price
            sale = '%.2f' % (price * 0.8) if rng.random() < 0.2 else ''
            stock = str(rng.randint(0, 200))
            w.writerow(['SS1M-%08d' % i, name, desc, regular, sale, stock, 'yes',
                        category, brand, tags, cname, size, material, pattern,
                        style, colour_image(colour, ptype)])

    write_json(os.path.join(d, 'config.json'), {
        'base_template': 'SSI_WooCommerceProductTemplate',
        'template_mappings': {
            'post_title': 'Name', 'post_content': 'Description', 'post_status': '',
            'parent_sku': '',
            'taxonomies': {
                'product_cat': {'separator': '>', 'source': 'Categories', 'is_variable': False},
                'product_brand': {'source': 'Brand', 'is_variable': False},
                'product_tag': {'source': 'Tags', 'is_variable': ''},
                'pa_color': {'source': 'Color', 'is_variable': ''},
                'pa_size': {'source': 'Size', 'is_variable': ''},
                'pa_material': {'source': 'Material', 'is_variable': ''},
                'pa_pattern': {'source': 'Pattern', 'is_variable': ''},
                'pa_style': {'source': 'Style', 'is_variable': ''},
            },
            'post_meta': {
                '_sku': 'SKU', '_regular_price': 'Regular_Price', '_sale_price': 'Sale_Price',
                '_stock': 'Stock', '_manage_stock': 'Manage_Stock',
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
               {'post_type': 'product', 'taxonomies': TAXONOMIES})
    write_json(os.path.join(d, 'sample.json'), {
        'name': 'Simple Products (1,000,000) - Showcase',
        'description': ('One million simple WooCommerce products with hierarchical '
                        'categories, brands, tags and five filterable attributes '
                        '(colour, size, material, pattern, style). Colour-matched '
                        'external images (no image download during the import). '
                        'Requires WooCommerce.'),
        'post_type': 'product', 'rows': COUNT,
        'features': ['Simple products', 'Categories', 'Brands', 'Tags',
                     'Colour / Size / Material / Pattern / Style attributes',
                     'External images (no download)'],
    })

    digest, size = sha256_and_size(os.path.join(d, 'data.csv'))
    print('%s: %d rows, %.1f MB' % (SLUG, COUNT, size / 1048576.0))
    print('sha256: %s' % digest)
    print('distinct colour x garment pairs present: %d of %d'
          % (len(seen_pairs), len(COLOURS) * len(TYPES)))
    print("'Red' x 'Dress' present: %s" % (('Red', 'Dress') in seen_pairs))
    return digest, size


if __name__ == '__main__':
    generate()
