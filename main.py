import sys
import yaml
import io
import argparse
import networkx as nx
import pygraphviz as pgv

# Product to color mapping
product_color_map = {
    'chair': 'green',
    'table': 'blue'
}

def parse_args():
    parser = argparse.ArgumentParser(description="Process a graph based on YAML input.")
    parser.add_argument('-p', '--precedents', action='store_true',
                        help='Transform all edges to precedents.')
    parser.add_argument('-d', '--dependents', action='store_true',
                        help='Transform all edges to dependents.')
    return parser.parse_args()

# Load YAML data from stdin and construct the initial graph
def load_graph_from_yaml():
    data = yaml.safe_load(sys.stdin)
    G = nx.DiGraph()

    for item in data:
        node_id = item['id']
        node_attrs = {k: v for k, v in item.items() if k not in ['id', 'precedents', 'dependents']}
        G.add_node(node_id, **node_attrs)

        process_edges(item, G, node_id)

    return G

def process_edges(item, G, node_id):
    for edge_type in ['precedents', 'dependents']:
        if edge_type in item:
            connections = item[edge_type]
            is_dependent = (edge_type == 'dependents')
            if isinstance(connections, list):
                for connection in connections:
                    if isinstance(connection, dict):
                        target_id = connection['node']
                        edge_attrs = {k: v for k, v in connection.items() if k != 'node'}
                    else:
                        target_id = connection
                        edge_attrs = {}
                    add_graph_edge(G, node_id, target_id, edge_attrs, is_dependent)
            else:
                add_graph_edge(G, node_id, connections, {}, is_dependent)

def add_graph_edge(G, node_id, target_id, edge_attrs, is_dependent):
    src, dst = (node_id, target_id) if is_dependent else (target_id, node_id)
    if not G.has_edge(src, dst):
        G.add_edge(src, dst, **edge_attrs)

# Modify graph nodes based on the product attribute
def modify_graph_for_products(G):
    for node, data in G.nodes(data=True):
        if 'product' in data:
            product_type = data.pop('product')
            data['color'] = product_color_map.get(product_type, 'gray')

def output_yaml_graph(G, use_dependents=False):
    output = []
    for node, data in G.nodes(data=True):
        node_data = {'id': node}
        node_data.update(data)
        edges = G.out_edges(node, data=True) if use_dependents else G.in_edges(node, data=True)
        edge_list = []
        for src, dst, edata in edges:
            edge_entry = {'node': dst if use_dependents else src}
            edge_entry.update(edata)
            edge_list.append(edge_entry)
        if edge_list:
            key = 'dependents' if use_dependents else 'precedents'
            node_data[key] = edge_list
        output.append(node_data)
    print(yaml.dump(output))

def main():
    args = parse_args()
    G = load_graph_from_yaml()

    if args.precedents:
        output_yaml_graph(G, use_dependents=False)
    elif args.dependents:
        output_yaml_graph(G, use_dependents=True)
    else:
        modify_graph_for_products(G)  # Apply color modification only for SVG output
        # Convert to PyGraphviz AGraph
        A = nx.nx_agraph.to_agraph(G)
        A.graph_attr['rankdir'] = 'LR'
        svg_output = io.BytesIO()
        A.draw(svg_output, format='svg', prog='dot')
        svg_output.seek(0)
        print(svg_output.read().decode('utf-8'))

if __name__ == '__main__':
    main()
