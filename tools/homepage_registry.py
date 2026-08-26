#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

DEFAULT_REGISTRY = Path(__file__).resolve().parents[1] / 'registry.json'
AXIS_CHOICES = (
    'physical-infrastructure',
    'compute-chain',
    'agent-economy',
    'capital-macro',
    'frontier-infrastructure',
)
CONTENT_TYPE_CHOICES = ('earnings', 'deep-dive', 'brief', 'interactive', 'tracker')
STATUS_CHOICES = ('new', 'updated', 'tracking', 'evergreen')


def load_registry(path):
    if not path.exists():
        return []
    items = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(items, list):
        raise ValueError('registry top-level value must be an array')
    return items


def save_registry(path, items):
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def upsert_entry(args):
    items = load_registry(args.registry)
    index = next((i for i, item in enumerate(items) if item.get('slug') == args.slug), None)
    entry = dict(items[index]) if index is not None else {}
    entry.update({
        'slug': args.slug,
        'title': args.title,
        'date': args.date,
        'deck': args.deck,
        'tag': args.tag,
        'source': args.source,
        'homepage_approved': True,
        'axis': args.axis,
        'content_type': args.content_type,
    })
    if args.published_at:
        entry['published_at'] = args.published_at
    if args.category:
        entry['category'] = args.category
    if args.path:
        entry['path'] = args.path
    if args.featured_rank:
        entry['featured_rank'] = args.featured_rank
    if args.series_id:
        entry['series_id'] = args.series_id
    if args.series_title:
        entry['series_title'] = args.series_title
    if args.series_order is not None:
        entry['series_order'] = args.series_order
    if args.homepage_deck:
        entry['homepage_deck'] = args.homepage_deck
    if args.status:
        entry['status'] = args.status
    if args.updated_at:
        entry['updated_at'] = args.updated_at
    if index is None:
        items.append(entry)
    else:
        items[index] = entry
    if args.featured_rank:
        for item in items:
            if item.get('slug') != args.slug and item.get('featured_rank') == args.featured_rank:
                item.pop('featured_rank')
    save_registry(args.registry, items)
    print(f'approved homepage entry: {args.slug}')


def remove_entry(args):
    items = load_registry(args.registry)
    new_items = [x for x in items if x.get('slug') != args.slug]
    save_registry(args.registry, new_items)
    print(f'removed homepage entry: {args.slug}')


def status_entry(args):
    items = load_registry(args.registry)
    for item in items:
        if item.get('slug') == args.slug:
            print(json.dumps(item, ensure_ascii=False, indent=2))
            return
    print('not_on_homepage')


def validate_registry(args):
    items = load_registry(args.registry)
    errors = []
    seen_slugs = set()
    featured = {}
    site_root = args.site_root.resolve()

    for position, item in enumerate(items, start=1):
        slug = item.get('slug')
        label = slug or f'entry#{position}'
        if not slug:
            errors.append(f'{label}: missing slug')
            continue
        if slug in seen_slugs:
            errors.append(f'{label}: duplicate slug')
        seen_slugs.add(slug)

        if item.get('homepage_approved') is not True:
            continue
        for field in ('title', 'date', 'deck', 'tag', 'published_at', 'axis', 'content_type'):
            if not item.get(field):
                errors.append(f'{label}: missing {field}')
        if item.get('axis') not in AXIS_CHOICES:
            errors.append(f"{label}: invalid axis {item.get('axis')!r}")
        if item.get('content_type') not in CONTENT_TYPE_CHOICES:
            errors.append(f"{label}: invalid content_type {item.get('content_type')!r}")
        if item.get('status') and item.get('status') not in STATUS_CHOICES:
            errors.append(f"{label}: invalid status {item.get('status')!r}")
        if item.get('series_order') is not None and not isinstance(item.get('series_order'), int):
            errors.append(f'{label}: series_order must be an integer')

        rank = item.get('featured_rank')
        if rank is not None:
            if rank not in (1, 2, 3):
                errors.append(f'{label}: featured_rank must be 1, 2 or 3')
            elif rank in featured:
                errors.append(f'{label}: featured_rank {rank} already used by {featured[rank]}')
            else:
                featured[rank] = label

        configured_path = item.get('path')
        if configured_path:
            relative = configured_path.strip('/')
            candidates = [site_root / relative]
        else:
            candidates = [site_root / slug / 'index.html']
        if candidates[0].is_dir():
            candidates.append(candidates[0] / 'index.html')
        if not any(candidate.is_file() for candidate in candidates):
            errors.append(f'{label}: public path does not exist')

    if errors:
        for message in errors:
            print(f'ERROR: {message}')
        raise SystemExit(1)
    print(f'homepage registry valid: {len(items)} entries, {len(seen_slugs)} unique slugs')


def main():
    parser = argparse.ArgumentParser(description='Manage Enya homepage registry with explicit approval.')
    parser.add_argument('--registry', type=Path, default=DEFAULT_REGISTRY)
    sub = parser.add_subparsers(dest='cmd', required=True)

    approve = sub.add_parser('approve', help='Add or update a homepage entry after Kerwin confirmation')
    approve.add_argument('--slug', required=True)
    approve.add_argument('--title', required=True)
    approve.add_argument('--date', required=True)
    approve.add_argument('--deck', required=True)
    approve.add_argument('--tag', required=True)
    approve.add_argument('--source', default='enya')
    approve.add_argument('--published-at', required=True)
    approve.add_argument('--category')
    approve.add_argument('--path')
    approve.add_argument('--featured-rank', type=int, choices=(1, 2, 3))
    approve.add_argument('--axis', required=True, choices=AXIS_CHOICES)
    approve.add_argument('--content-type', required=True, choices=CONTENT_TYPE_CHOICES)
    approve.add_argument('--series-id')
    approve.add_argument('--series-title')
    approve.add_argument('--series-order', type=int)
    approve.add_argument('--homepage-deck')
    approve.add_argument('--status', choices=STATUS_CHOICES, default='new')
    approve.add_argument('--updated-at')
    approve.set_defaults(func=upsert_entry)

    hide = sub.add_parser('hide', help='Remove a page from homepage registry')
    hide.add_argument('--slug', required=True)
    hide.set_defaults(func=remove_entry)

    status = sub.add_parser('status', help='Show homepage registry entry status for a slug')
    status.add_argument('--slug', required=True)
    status.set_defaults(func=status_entry)

    validate = sub.add_parser('validate', help='Validate the structured homepage registry contract')
    validate.add_argument('--site-root', type=Path, default=DEFAULT_REGISTRY.parent)
    validate.set_defaults(func=validate_registry)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
