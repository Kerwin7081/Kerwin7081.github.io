#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

REGISTRY = Path('/opt/kerwin-agent/repos/site/registry.json')


def load_registry():
    if not REGISTRY.exists():
        return []
    return json.loads(REGISTRY.read_text(encoding='utf-8'))


def save_registry(items):
    REGISTRY.write_text(json.dumps(items, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def upsert_entry(args):
    items = load_registry()
    items = [x for x in items if x.get('slug') != args.slug]
    entry = {
        'slug': args.slug,
        'title': args.title,
        'date': args.date,
        'deck': args.deck,
        'tag': args.tag,
        'source': args.source,
        'homepage_approved': True,
    }
    if args.published_at:
        entry['published_at'] = args.published_at
    items.append(entry)
    save_registry(items)
    print(f'approved homepage entry: {args.slug}')


def remove_entry(args):
    items = load_registry()
    new_items = [x for x in items if x.get('slug') != args.slug]
    save_registry(new_items)
    print(f'removed homepage entry: {args.slug}')


def status_entry(args):
    items = load_registry()
    for item in items:
        if item.get('slug') == args.slug:
            print(json.dumps(item, ensure_ascii=False, indent=2))
            return
    print('not_on_homepage')


def main():
    parser = argparse.ArgumentParser(description='Manage Enya homepage registry with explicit approval.')
    sub = parser.add_subparsers(dest='cmd', required=True)

    approve = sub.add_parser('approve', help='Add or update a homepage entry after Kerwin confirmation')
    approve.add_argument('--slug', required=True)
    approve.add_argument('--title', required=True)
    approve.add_argument('--date', required=True)
    approve.add_argument('--deck', required=True)
    approve.add_argument('--tag', required=True)
    approve.add_argument('--source', default='enya')
    approve.add_argument('--published-at')
    approve.set_defaults(func=upsert_entry)

    hide = sub.add_parser('hide', help='Remove a page from homepage registry')
    hide.add_argument('--slug', required=True)
    hide.set_defaults(func=remove_entry)

    status = sub.add_parser('status', help='Show homepage registry entry status for a slug')
    status.add_argument('--slug', required=True)
    status.set_defaults(func=status_entry)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
