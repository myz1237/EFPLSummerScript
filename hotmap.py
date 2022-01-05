from io import DEFAULT_BUFFER_SIZE
from math import isnan, nan
from typing import Counter
import networkx as nx
import json
from numpy import NaN, source
from pandas.core.indexes.datetimes import date_range
import seaborn as sn
import matplotlib.pyplot as plt
import pandas as pd
import math
import numpy as np 



G = nx.DiGraph()
get_attr = lambda line, attr : line.split("%s=\"" % attr, 1)[1].split('"', 1)[0]
seg_enum_s1 = ["SL1BEG", "SR1BEG"]
seg_enum_w1 = ["WL1BEG", "WR1BEG"]
seg_enum_n1 = ["NL1BEG", "NR1BEG"]
seg_enum_e1 = ["EL1BEG", "ER1BEG"]

def test():
    ab = {1:{23:34},2:"23"}
    print(ab)
    G.add_node(1, str1='sdf1')
    G.add_node(2, str2='sdf2')
    G.add_node(3, str2='sdf2')
    G.add_node(4, str2='sdf2')
    G.add_edge(1,2,w = "2123")
    G.add_edge(2,3)
    G.add_edge(3,2)
    G.add_edge(4,2)
    print(G.nodes[1])
    print(ab)
    print(G.edges[1,2]["w"])
    for a in G.predecessors(2):
        print(a)
    for i in range(10):
        print("switch_id_%d" %(i))
    i += 1
    print(ab[2])


def parse_segments(seg_dict, line):

    if line.startswith("</segments>"):
        return
    if line.startswith("<segment id"):
        seg_dict.update({int(get_attr(line, "id")) : get_attr(line, "name")})

def generate_statistic_form(source_column, destin_index):
    
    form = {}
    for column in source_column:
        form.update({column : {}})
        for index in destin_index:
            form[column].update({index : 0})
    return form

def statistic(source, destin, statistic_form: dict):
    if not source in statistic_form:
        statistic_form.update({source: {}})
    elif not destin in statistic_form[source]:
        statistic_form[source].update({destin: 1})
    else:
        statistic_form[source][destin] += 1

def handle_seg(source, destin, sorted_seg_enum_source_column, form: dict):

    sorted_seg_enum = sorted_seg_enum_source_column + seg_enum_e1 + seg_enum_n1 + seg_enum_w1 + seg_enum_w1
    
    if source in seg_enum_e1 and destin in sorted_seg_enum:
        handle_seg_assist("E1BEG", destin, sorted_seg_enum_source_column, form)
    elif source in seg_enum_w1 and destin in sorted_seg_enum:
        handle_seg_assist("W1BEG", destin, sorted_seg_enum_source_column, form)
    elif source in seg_enum_s1 and destin in sorted_seg_enum:
        handle_seg_assist("S1BEG", destin, sorted_seg_enum_source_column, form)
    elif source in seg_enum_n1 and destin in sorted_seg_enum:
        handle_seg_assist("N1BEG", destin, sorted_seg_enum_source_column, form)
    elif source in sorted_seg_enum_source_column and destin in sorted_seg_enum:
        handle_seg_assist(source, destin, sorted_seg_enum_source_column, form)


def handle_seg_assist(source, destin, sorted_seg_enum_source_column, form : dict):
    
    if destin in seg_enum_n1:
        form[source]["N1BEG"] += 1
    elif destin in seg_enum_s1:
        form[source]["S1BEG"] += 1
    elif destin in seg_enum_e1:
        form[source]["E1BEG"] += 1
    elif destin in seg_enum_w1:
        form[source]["W1BEG"] += 1
    elif destin in sorted_seg_enum_source_column: 
        form[source][destin] += 1


def main():
    
    rr = r"/home/myz1237/Desktop/test_full_size/test_full_size.xml"
    edge_int = r"/home/myz1237/Desktop/edge2.json"

    seg_dict = {}
    seg_enum = []

    #Follow the paper
    sorted_seg_enum_source_column = ["SS6BEG", "WW4BEG", "NN6BEG", "EE4BEG", "SW6BEG", "NW6BEG", "NE6BEG", "SE6BEG", "SS2BEG", "WW2BEG", "NN2BEG", "EE2BEG", "SW2BEG", "NW2BEG", "NE2BEG", "SE2BEG", "S1BEG", "W1BEG", "N1BEG", "E1BEG"]
    sorted_seg_enum_destin_index = ["NN6BEG","EE4BEG", "SS6BEG", "WW4BEG", "NE6BEG", "SE6BEG", "SW6BEG", "NW6BEG", "NN2BEG", "EE2BEG", "SS2BEG", "WW2BEG", "NE2BEG", "SE2BEG", "SW2BEG", "NW2BEG", "N1BEG", "E1BEG", "S1BEG", "W1BEG"]
    
    with open(rr, "r") as inf:
        for line in inf:
            if line.startswith("</segments>"):
                break
            if line.startswith("<segment id"):
                seg_dict.update({int(get_attr(line, "id")) : get_attr(line, "name")})
    
    for key in seg_dict:
        seg_enum.append(seg_dict[key])
    
    print(seg_enum)
    with open(edge_int, "r") as inf:
        edge_load = json.load(inf)

    form = {}
    valid_seg_enum = ['WW2BEG', 'NN2BEG', 'WW4BEG', 'SR1BEG_S', 'ER1BEG_S', 'NR1BEG',  'EL1BEG', 'EE2BEG', 'SS6BEG', 'SW2BEG', 'WR1BEG', 'SL1BEG', 'NL1BEG', 'SS2BEG', 'NE6BEG', 'SE6BEG', 'SR1BEG', 'EE4BEG', 'NE2BEG', 'NW2BEG', 'WL1BEG', 'ER1BEG', 'WR1BEG_S', 'NN6BEG', 'SE2BEG', 'SW6BEG', 'EL1BEG_N', 'NW6BEG', 'WL1BEG_N', 'NL1BEG_N']
    valid_seg_enum_without_sn_segement = ['WW2BEG', 'NN2BEG', 'WW4BEG', 'NR1BEG', 'EL1BEG', 'EE2BEG', 'SS6BEG', 'SW2BEG', 'WR1BEG', 'SL1BEG', 'NL1BEG', 'SS2BEG', 'NE6BEG', 'SE6BEG', 'SR1BEG', 'EE4BEG', 'NE2BEG', 'NW2BEG', 'WL1BEG', 'ER1BEG', 'NN6BEG', 'SE2BEG', 'SW6BEG', 'NW6BEG']

    form = generate_statistic_form(sorted_seg_enum_source_column, sorted_seg_enum_destin_index)
    # #Count the number of edge
    # for key in edge_load:
    #     counter = int(edge_load[key]["counter"])
    #     if int(edge_load[key]["direction"]):
    #         #Source -> Multiple Destin
    #         for i in range(1, counter+1):
    #             destin = edge_load[key]["destin_%d" %i]["seg"]
    #             source = edge_load[key]["source"]["segment_info"]
    #             if destin in valid_seg_enum_without_sn_segement and source in valid_seg_enum_without_sn_segement:
    #                 statistic(source, destin, form)

    #     else:
    #         #Multiple Source -> Destin
    #         for i in range(1, counter+1):
    #             source = edge_load[key]["source_%d" %i]["seg"]
    #             destin = edge_load[key]["destin"]["segment_info"]
    #             if destin in valid_seg_enum_without_sn_segement and source in valid_seg_enum_without_sn_segement:
    #                 statistic(source, destin, form)

    #Count the number of edge
    for key in edge_load:
        counter = int(edge_load[key]["counter"])
        if int(edge_load[key]["direction"]):
            #Source -> Multiple Destin
            for i in range(1, counter+1):
                destin = edge_load[key]["destin_%d" %i]["seg"]
                source = edge_load[key]["source"]["segment_info"]
                handle_seg(source, destin, sorted_seg_enum_source_column, form)

        else:
            #Multiple Source -> Destin
            for i in range(1, counter+1):
                source = edge_load[key]["source_%d" %i]["seg"]
                destin = edge_load[key]["destin"]["segment_info"]
                handle_seg(source, destin, sorted_seg_enum_source_column, form)
        
    with open(r'/home/myz1237/Desktop/statistics.json', 'w') as f:
         print(json.dumps(form,indent = 4), file = f)

    data = pd.DataFrame(form)
    pd.set_option('display.width', None)
    # for index, row in data.iterrows():
    #     for valid in valid_seg_enum_without_sn_segement:
    #         if isnan(data.at[index, valid]):
    #             data.at[index, valid] = 0
    with open(r'/home/myz1237/Desktop/statistics.csv', 'w') as f:
         print(data,file=f)



    # sn.set(font_scale=1.5)
    sn.heatmap(data=data, cmap='hot', square=True) 
    #Column is the source
    plt.xticks(np.arange(0.5, len(data.index), 1), data.index)
    #Index is the destin
    plt.yticks(np.arange(0.5, len(data.columns), 1), data.columns)
    ax = plt.gca()
    #ax.invert_xaxis()
    #ax.invert_yaxis()   
    plt.show()
    



if __name__ == "__main__":
    main()