"""CLI: python -m tools.index_visual2d meta.json nodes.jsonl edges.jsonl out.m2d.sqlite"""
import argparse
from server.visual2d_index_import import build


def main():
    parser = argparse.ArgumentParser(description='Index real, attributed 2D neural topology')
    for field in ('metadata', 'nodes', 'edges', 'output'):
        parser.add_argument(field)
    args = parser.parse_args()
    info = build(args.metadata, args.nodes, args.edges, args.output)
    print('Indexed', info['id'], info['nodes_total'], 'neurons,',
          info['edges_total'], 'connections')


if __name__ == '__main__':
    main()
