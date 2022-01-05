import networkx as nx
import json

from networkx.classes.function import nodes
from pandas.core.indexes import base

get_attr = lambda line, attr : line.split("%s=\"" % attr, 1)[1].split('"', 1)[0]
id = 0
u = 0


def parse_switch(switch_dict, line):
    """Parses all the switch blocks.

    Parameters
    ----------
    lines : List[str]
        Read RR-graph file.

    Returns
    -------
    Dict[int, Dict[int, str]]
        A dictionary of dictionaries, indexed by block ids, block name and ptc nums,
        holding the pin names.
    """

    if line.startswith("<switch "):
        id = int(get_attr(line, "id"))
        name = get_attr(line, "name")
        type = get_attr(line, "type")
        switch_dict.update({id : {'name' : name, 'type' : type}})

def parse_block_pins(pin_dict, line):
    """Parses all the block pins.

    Parameters
    ----------
    lines : List[str]
        Read RR-graph file.

    Returns
    -------
    Dict[int, Dict[int, str]]
        A dictionary of dictionaries, indexed by block ids, block name and ptc nums,
        holding the pin names.
    """
    global bid
    if line.startswith("<block_type "):
        bid = int(get_attr(line, "id"))
        name = get_attr(line, "name")
        pin_dict.update({bid : {'name' : name}})

    if "<pin_class " in line:
        ptc = int(get_attr(line, "ptc"))
        name = line.split("</pin>")[0].split('>')[-1]
        pin_dict[bid].update({ptc : name})

def parse_segments(seg_dict, line):
    """Parses all segment declarations.

    Parameters
    ----------
    lines : List[str]
        Read RR-graph file.

    Returns
    -------
    Dict[int, str]
        A mapping from segment ids to segment names.
    """

    if line.startswith("<segment id"):
        seg_dict.update({int(get_attr(line, "id")) : get_attr(line, "name")})

def parse_grid(grid, line):
    """Parses the grid layout.

    Parameters
    ----------
    lines : List[str]
        Read RR-graph file.

    Returns
    -------
    Dict[Tuple[int], int]
        A dictionary holding block id for each tile.
    """

    if line.startswith("<grid_loc "):
        x = int(get_attr(line, 'x'))
        y = int(get_attr(line, 'y'))
        bid = int(get_attr(line, "block_type_id"))
        grid.update({'%d,%d'%(x, y) : bid})

def parse_edges(line, G):
    """Parses all RR-graph edges.

    Parameters
    ----------
    lines : List[str]
        Read RR-graph file.
    G : nx.DiGraph
        RR-graph with nodes added.

    Returns
    -------
    None
    """

    if line.startswith("<edge "):
        u = int(get_attr(line, "src_node"))
        v = int(get_attr(line, "sink_node"))
        switch = int(get_attr(line, "switch_id"))
        if G.has_node(u) and G.has_node(v):
            G.add_edge(u, v, switch_id = switch)

def edge_direction(type, direction):
    # 0-->Bi_Dir 1-->INC_DIR(?), SINK and IPIN -1-->DEC_DIR(?), SOURCE and OPIN
    if "CHANY" or "CHANX" in type:
        if direction == "BI_DIR":
            return 0
        # else:
        #     return 1 if direction == "INC_DIR" else -1

    if "SINK" or "IPIN" in type:
        return 1
    else:
        return -1


def find_edge(G, connection_graph, switch_dict):
    """
    1.Extract ID from connection_graph
    2.Search all edge information of this ID, only as the source. Record Source, Sink, and Switch ID
    """
    edge_graph = {}
    history =[]
    for key in connection_graph:
        if key == 'counter': 
            break

        i = 1
        
        if not key in edge_graph:
            edge_graph.update({key:{}})
        
        direct = edge_direction(connection_graph[key]["base_type"], connection_graph[key]["direction"]) 

        #No need to find predecessors
        if direct == 1:
            edge_graph[key].update({'destin' : connection_graph[key]})

            for predecessor in G.predecessors(key):
                if '(%d, %d)'%(predecessor, key) in history:
                    continue
                else:
                    history.append('(%d, %d)'%(predecessor, key))
                    edge_graph[key].update({'switch_id_%d' %(i) : G.edges[predecessor,key]['switch_id'], 
                                    'switch_name_%d' %(i) : switch_dict[G.edges[predecessor,key]['switch_id']]})
                    edge_graph[key].update({'source_%d' %(i): G.nodes[predecessor]})
                    i += 1

            edge_graph[key].update({'counter' : "%d" %(i-1), 'direction' : "1"})
            continue
        
        if direct == -1:
            edge_graph.update({key:{'source' : connection_graph[key]}})

            for successor in G.successors(key):
                if '(%d, %d)'%(key, successor) in history:
                    continue
                else:
                    history.append('(%d, %d)'%(key, successor))
                    edge_graph[key].update({'switch_id_%d' %(i) : G.edges[key,successor]['switch_id'], 
                                    'switch_name_%d' %(i) : switch_dict[G.edges[key,successor]['switch_id']]})
                    edge_graph[key].update({'destin_%d' %(i) : G.nodes[successor]})
                    i += 1

            edge_graph[key].update({'counter' : "%d" %(i-1), 'direction' : "-1"})
            continue
        
        if direct == 0:
            edge_graph.update({key:{'source&destin' : connection_graph[key]}})
            
            for predecessor in G.predecessors(key):
                if '(%d, %d)'%(predecessor, key) in history:
                    continue
                else:
                    history.append('(%d, %d)'%(predecessor, key))
                    edge_graph[key].update({'switch_id_4source_%d' %(i) : G.edges[predecessor,key]['switch_id'], 
                                    'switch_name_4source_%d' %(i) : switch_dict[G.edges[predecessor,key]['switch_id']]})
                    edge_graph[key].update({'source_%d' %(i): G.nodes[predecessor]})
                    i += 1
                    txt = "<edge source_id=%s source_seg=%s source_coord=(%s, %s)-(%s, %s) destin_id=%s destin_seg=%s destin_coord=(%s, %s)-(%s, %s) switch_name=%s\n>"\
                        %(predecessor, G.nodes[predecessor]["seg"],G.nodes[predecessor]["xlow"], G.nodes[predecessor]["ylow"], G.nodes[predecessor]["xhigh"], G.nodes[predecessor]["yhigh"],
                        key, connection_graph[key]["seg"], connection_graph[key]["xlow"], connection_graph[key]["ylow"], connection_graph[key]["xhigh"], connection_graph[key]["yhigh"], switch_dict[G.edges[predecessor,key]['switch_id']])
                    with open(r'/home/myz1237/Desktop/node.txt', 'a') as f:
                        print(txt, file=f)
            edge_graph[key].update({'counter_4source' : "%d" %(i-1)})

            i = 1

            for successor in G.successors(key):
                if '(%d, %d)'%(key, successor) in history:
                    continue
                else:
                    history.append('(%d, %d)'%(key, successor))
                edge_graph[key].update({'switch_id_4destin_%d' %(i) : G.edges[key,successor]['switch_id'], 
                                'switch_name_4destin_%d' %(i) : switch_dict[G.edges[key,successor]['switch_id']]})
                edge_graph[key].update({'destin_%d' %(i) : G.nodes[successor]})
                i += 1
                txt = "<edge source_id=%s source_seg=%s source_coord=(%s, %s)-(%s, %s) destin_id=%s destin_seg=%s destin_coord=(%s, %s)-(%s, %s) switch_name=%s\n>"\
                    %(key, connection_graph[key]["seg"], connection_graph[key]["xlow"], connection_graph[key]["ylow"], connection_graph[key]["xhigh"], connection_graph[key]["yhigh"],
                    successor, G.nodes[successor]["seg"],G.nodes[successor]["xlow"], G.nodes[successor]["ylow"], G.nodes[successor]["xhigh"], G.nodes[successor]["yhigh"],switch_dict[G.edges[key,successor]['switch_id']])
                
                with open(r'/home/myz1237/Desktop/node.txt', 'a') as f:
                        print(txt, file=f)

            edge_graph[key].update({'counter_4destin' : "%d" %(i-1), 'direction' : "0"})
                
    return edge_graph


def get_connection_graph(G, x, y):
    """Get all connections of (x, y) coordinate.

    Parameters
    ----------
    G : nx.DiGraph
        Parsed RR-graph.
    x : int
        x-coordinate of the requested tile.
    y : int
        y-coordinate of the requested tile.

    Returns
    -------
    connection
    """

    connection = {}
    tmp = {'counter' : {}}
    for u, attrs in G.nodes(data = True):
        #Get all nodes starting, ending at this tile, or pin of this tile
        if (attrs["xlow"] == x and attrs["ylow"] == y) or (attrs["xhigh"] == x and attrs["yhigh"] == y):
            connection.update({u : {'base_type' : attrs["base_type"], 'direction' : attrs["direction"], 'ptc' : attrs["ptc"], 
                'xlow' : attrs["xlow"],'xhigh' : attrs["xhigh"],'ylow' : attrs["ylow"],'yhigh' : attrs["yhigh"],'seg' : attrs["seg"]}})    
            
            if attrs['seg'] != "None":
                if attrs["seg"] not in tmp['counter']:
                    tmp['counter'].update({attrs["seg"] : 1})
                else:
                    tmp['counter'][attrs["seg"]] += 1
            txt = "<node direction=%s id=%s type=%s coordinate=(%s, %s)-(%s, %s) segment_name=%s>\n"\
                    %(attrs["direction"], u, attrs["base_type"], attrs["xlow"], attrs["ylow"], attrs["xhigh"], attrs["yhigh"], attrs["seg"])
            with open(r'/home/myz1237/Desktop/node.txt', 'a') as f:
                print(txt, file=f)
                    
    connection.update(tmp)

    return connection


def generate_graph_node(G, seg_dict, line): 
    global u
    if line.startswith("<node "):
        u = int(get_attr(line, "id"))
        base_type = get_attr(line, "type")
        ptc = int(get_attr(line, "ptc"))
        xlow = int(get_attr(line, "xlow"))
        xhigh = int(get_attr(line, "xhigh"))
        ylow = int(get_attr(line, "ylow"))
        yhigh = int(get_attr(line, "yhigh"))

        if base_type == "CHANY" or base_type == "CHANX":
            direction = get_attr(line, "direction")
        else:
            direction = '0'

        G.add_node(u, base_type = base_type, direction = direction, ptc = ptc, xlow = xlow, xhigh = xhigh, ylow = ylow, yhigh = yhigh, seg = "None")

    try:
        G.nodes[u]["seg"] = seg_dict[int(get_attr(line, "segment_id"))]
    except:
        pass

def main():
    
    x1 = 40
    y1 = 15

    x2 = 41
    y2 = 15

    rr = r"/home/myz1237/Desktop/test_full_size/test_full_size.xml"

    switch_dict = {}
    seg_dict = {}
    pin_dict = {}
    grid_dict = {}
    edge = {}
    G = nx.DiGraph()
    with open(rr, "r") as inf:
        for line in inf:
            parse_switch(switch_dict, line)
            parse_segments(seg_dict, line)
            parse_block_pins(pin_dict, line)
            parse_grid(grid_dict, line)
            generate_graph_node(G, seg_dict, line)
            parse_edges(line, G)

    # with open(r'/home/myz1237/Desktop/output.txt', 'w') as f:
    #     print(json.dumps(switch_dict, indent=4), file=f)
    #     print(json.dumps(seg_dict, indent=4), file=f)
    #     print(json.dumps(pin_dict, indent=4), file=f)
    #     print(json.dumps(grid_dict, indent=4), file=f)

    connection_graph = get_connection_graph(G, x2, y2)
    with open(r'/home/myz1237/Desktop/output2.json', 'w') as f:
         print(json.dumps(connection_graph, indent=4), file=f)
    edge = find_edge(G, connection_graph, switch_dict)
    with open(r'/home/myz1237/Desktop/edge2.json', 'w') as f:
         print(json.dumps(edge, indent=4), file=f)




if __name__ == "__main__":
    main()
