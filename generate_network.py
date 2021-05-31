import sys
import gurobipy
import random
from graphviz import Digraph
from graphviz import Graph
import matplotlib.pyplot as plt

def PlotNetwork(num_node, edges, filename):
    G = Graph(name="", format="png")
    for node in range(num_node):
        G.node(name=str(node), label=str(node))
    for edge in edges:
        G.edge(str(edge[0]), str(edge[1]))
    G.render(filename=filename)

def CountPairs(num_node, initial, final):
    labels = [0 for i in range(num_node)]
    group = 1

    initial_edges = set()
    final_edges = set()
    for edge in initial:
        initial_edges.add(edge)
    for edge in final:
        final_edges.add(edge)
    common_edges = initial_edges & final_edges

    for edge in common_edges:
        n1 = edge[0]
        n2 = edge[1]
        if (labels[n1] == 0) and (labels[n2] == 0):
            labels[n1] = group
            labels[n2] = group
            group += 1
        elif (labels[n1] == 0) and (labels[n2] != 0):
            labels[n1] = labels[n2]
        elif (labels[n1] != 0) and (labels[n2] == 0):
            labels[n2] = labels[n1]
        else:
            tmp = labels[n1]
            for i in range(num_node):
                if labels[i] == tmp:
                    labels[i] = labels[n2]
    
    diff_groups = {}
    for n in range(num_node):
        if labels[n] in diff_groups.keys():
            diff_groups[labels[n]] += 1
        else:
            diff_groups[labels[n]] = 1
    
    count = 0
    for i in diff_groups.keys():
        for j in diff_groups.keys():
            if i != j:
                count += diff_groups[i]*diff_groups[j]
    
    return count/4

def CountPairsFix(num_node, common_edges):
    labels = [0 for i in range(num_node)]
    group = 1

    for edge in common_edges:
        n1 = edge[0]
        n2 = edge[1]
        if (labels[n1] == 0) and (labels[n2] == 0):
            labels[n1] = group
            labels[n2] = group
            group += 1
        elif (labels[n1] == 0) and (labels[n2] != 0):
            labels[n1] = labels[n2]
        elif (labels[n1] != 0) and (labels[n2] == 0):
            labels[n2] = labels[n1]
        else:
            tmp = labels[n1]
            for i in range(num_node):
                if labels[i] == tmp:
                    labels[i] = labels[n2]
    
    diff_groups = {}
    for n in range(num_node):
        if labels[n] in diff_groups.keys():
            diff_groups[labels[n]] += 1
        else:
            diff_groups[labels[n]] = 1
    
    count = 0
    for i in diff_groups.keys():
        for j in diff_groups.keys():
            if i != j:
                count += diff_groups[i]*diff_groups[j]
    
    return count/4


def GenerateNetwork(node_degrees):
    num_node = len(node_degrees)
    total_degree = 0
    for degree in node_degrees:
        total_degree += degree
    num_edge = total_degree / 2
    # print (num_edge)

    initial_edges = []
    flag = True
    while flag:
        initial_edges = []
        remaining_nodes = list(range(num_node))
        each_degrees = node_degrees.copy()
        while len(remaining_nodes) > 3:
            n1 = 0
            n2 = 0
            while n1 == n2:
                n1 = random.choice(remaining_nodes)
                n2 = random.choice(remaining_nodes)
            initial_edges.append((n1,n2))
            each_degrees[n1] -= 1
            each_degrees[n2] -= 1
            if each_degrees[n1] == 0:
                remaining_nodes.remove(n1)
            if each_degrees[n2] == 0:
                remaining_nodes.remove(n2)
        if len(remaining_nodes) <= 2:
            continue
        # print(remaining_nodes)
        # print(each_degrees[remaining_nodes[0]], each_degrees[remaining_nodes[1]], each_degrees[remaining_nodes[2]])
        if (    ( (each_degrees[remaining_nodes[0]]+each_degrees[remaining_nodes[1]]-each_degrees[remaining_nodes[2]]) % 2 == 0 )
            and ( (each_degrees[remaining_nodes[0]]+each_degrees[remaining_nodes[2]]-each_degrees[remaining_nodes[1]]) % 2 == 0 )
            and ( (each_degrees[remaining_nodes[1]]+each_degrees[remaining_nodes[2]]-each_degrees[remaining_nodes[0]]) % 2 == 0 ) ):
            e_01 = (each_degrees[remaining_nodes[0]]+each_degrees[remaining_nodes[1]]-each_degrees[remaining_nodes[2]]) / 2
            e_02 = (each_degrees[remaining_nodes[0]]+each_degrees[remaining_nodes[2]]-each_degrees[remaining_nodes[1]]) / 2
            e_12 = (each_degrees[remaining_nodes[1]]+each_degrees[remaining_nodes[2]]-each_degrees[remaining_nodes[0]]) / 2
            if (e_01 > 0) and (e_12 > 0) and (e_02 > 0):
                for i in range(int(e_01)):
                    initial_edges.append((remaining_nodes[0], remaining_nodes[1]))
                for i in range(int(e_02)):
                    initial_edges.append((remaining_nodes[0], remaining_nodes[2]))
                for i in range(int(e_12)):
                    initial_edges.append((remaining_nodes[1], remaining_nodes[2]))
                flag = False
    # print(len(initial_edges))
    return initial_edges


def FindPlan_A(num_node, initial, final):
    num_edge = len(initial)
    old_edges = initial.copy()
    new_edges = final.copy()
    flag = True
    while flag == True:
        flag = False
        for edge in old_edges:
            if edge in new_edges:
                old_edges.remove(edge)
                new_edges.remove(edge)
                flag = True
    # print(old_edges)
    # print(new_edges)

    fix_edges = initial.copy()
    for edge in old_edges:
        fix_edges.remove(edge)
    # print(fix_edges)

    fixed_degrees = [0 for i in range(num_node)]
    updated_degrees = [0 for i in range(num_node)]

    for edge in fix_edges:
        fixed_degrees[edge[0]] += 1
        fixed_degrees[edge[1]] += 1
    for edge in old_edges:
        updated_degrees[edge[0]] += 1
        updated_degrees[edge[1]] += 1
    
    # get the total degree that need to be updated
    total_updated_degree = 0
    for d in updated_degrees:
        total_updated_degree += d

    num_updated_edge = len(old_edges)
    target_edge_number = 0 
    if num_updated_edge % 2 == 0:
        target_edge_number = num_updated_edge / 2
    else:
        target_edge_number = (num_updated_edge+1) / 2

    M = gurobipy.Model()
    x = M.addVars(num_updated_edge, vtype=gurobipy.GRB.BINARY, name="x")
    y = M.addVars(num_updated_edge, vtype=gurobipy.GRB.BINARY, name="y")

    minimize = M.addVar(vtype=gurobipy.GRB.INTEGER, name="minimize")

    M.update()

    M.setObjective(minimize, gurobipy.GRB.MAXIMIZE)

    for node in range(num_node):
        lhs = 0
        rhs = 0
        update1_degree = 0
        for i in range(num_updated_edge):
            if old_edges[i][0] == node or old_edges[i][1] == node:
                lhs += x[i]
                update1_degree += x[i]
        for i in range(num_updated_edge):
            if new_edges[i][0] == node or new_edges[i][1] == node:
                rhs += y[i]
        M.addConstr( lhs == rhs )
        M.addConstr( fixed_degrees[node] + update1_degree >= 1 )
        M.addConstr( fixed_degrees[node] + updated_degrees[node] - update1_degree >= 1 )

    M.addConstr( num_updated_edge - gurobipy.quicksum(x)*2 >= minimize )

    M.optimize()

    # num_solution = M.SolCount
    # for solution in range(num_solution):
    #     M.setParam(gurobipy.GRB.Param.SolutionNumber, solution)
    #     print("Solution %d: " % solution)
    #     for i in range(num_updated_edge):
    #         if x[i].x:
    #             print(old_edges[i], end=" ")
    #     print()
    #     for i in range(num_updated_edge):
    #         if y[i].x:
    #             print(new_edges[i], end=" ")
    #     print()
    return M.Runtime

def FindPlan_B(num_node, initial, final):
    num_edge = len(initial)
    old_edges = initial.copy()
    new_edges = final.copy()
    flag = True
    while flag == True:
        flag = False
        for edge in old_edges:
            if edge in new_edges:
                old_edges.remove(edge)
                new_edges.remove(edge)
                flag = True
    # print(old_edges)
    # print(new_edges)

    fix_edges = initial.copy()
    for edge in old_edges:
        fix_edges.remove(edge)
    # print(fix_edges)

    fixed_degrees = [0 for i in range(num_node)]
    updated_degrees = [0 for i in range(num_node)]

    for edge in fix_edges:
        fixed_degrees[edge[0]] += 1
        fixed_degrees[edge[1]] += 1
    for edge in old_edges:
        updated_degrees[edge[0]] += 1
        updated_degrees[edge[1]] += 1
    
    # get the total degree that need to be updated
    total_updated_degree = 0
    for d in updated_degrees:
        total_updated_degree += d

    num_updated_edge = len(old_edges)
    target_edge_number = 0 
    if num_updated_edge % 2 == 0:
        target_edge_number = num_updated_edge / 2
    else:
        target_edge_number = (num_updated_edge+1) / 2

    M = gurobipy.Model()
    x = M.addVars(num_updated_edge, vtype=gurobipy.GRB.BINARY, name="x")
    y = M.addVars(num_updated_edge, vtype=gurobipy.GRB.BINARY, name="y")
    maximum = M.addVar(vtype=gurobipy.GRB.INTEGER, name="maximum")

    M.update()

    M.setObjective(maximum - target_edge_number, gurobipy.GRB.MINIMIZE)

    for node in range(num_node):
        lhs = 0
        rhs = 0
        update1_degree = 0
        for i in range(num_updated_edge):
            if old_edges[i][0] == node or old_edges[i][1] == node:
                lhs += x[i]
                update1_degree += x[i]
        for i in range(num_updated_edge):
            if new_edges[i][0] == node or new_edges[i][1] == node:
                rhs += y[i]
        M.addConstr( lhs == rhs )
        M.addConstr( fixed_degrees[node] + update1_degree >= 1 )
        M.addConstr( fixed_degrees[node] + updated_degrees[node] - update1_degree >= 1 )

    M.addConstr( gurobipy.quicksum(x) <= maximum )
    M.addConstr( num_updated_edge - gurobipy.quicksum(x) <= maximum )

    M.optimize()

    num_solution = M.SolCount
    updated_set = set()
    for solution in range(num_solution):
        M.setParam(gurobipy.GRB.Param.SolutionNumber, solution)
        print("Solution %d: " % solution)
        for i in range(num_updated_edge):
            if x[i].x:
                # print(old_edges[i], end=" ")
                updated_set.add(old_edges[i])
        print()
        break
        # for i in range(num_updated_edge):
        #     if y[i].x:
        #         print(new_edges[i], end=" ")
        # print()

    return M.Runtime

    # for edge in fix_edges:
    #     updated_set.add(edge)
    
    # return CountPairsFix(num_node, updated_set)

if __name__ == "__main__":
    # num_node = 6
    # initial_edge_list = [   (0,1),(0,1),(0,5),(0,5),
    #                         (1,2),(1,4),
    #                         (2,3),(2,3),(2,5),
    #                         (3,4),(3,4),
    #                         (4,5)]
    # final_edge_list = [ (0,3),(0,3),(0,4),(0,4),
    #                     (1,2),(1,2),(1,3),(1,4),
    #                     (2,5),(2,5),
    #                     (3,5),
    #                     (4,5)]

    # PlotNetwork(6, initial_edge_list, "initial")
    # PlotNetwork(6, final_edge_list, "final")

    # FindPlan_A(num_node, initial_edge_list, final_edge_list)

    # times = {}
    # for num_node in [10, 50, 100, 500, 1000]:
    #     for degree in [2, 4, 6, 8, 10]:
    #         total_time = 0
    #         for time in range(10):
    #             node_degree = [degree for i in range(num_node)]
    #             initial_edge_list = GenerateNetwork(node_degree)
    #             final_edge_list = GenerateNetwork(node_degree)

    #             total_time += FindPlan_B(num_node, initial_edge_list, final_edge_list)
    #         times[(num_node, degree)] = total_time/10
    # for key in times.keys():
    #     print(key[0], key[1], times[key])

    for num_node in [10, 50, 100,500, 1000]:
        for degree in [2, 4, 6, 8, 10]:
            total_count = 0
            for time in range(20):
                node_degree = [degree for i in range(num_node)]
                initial_edge_list = GenerateNetwork(node_degree)
                final_edge_list = GenerateNetwork(node_degree)

                total_count += CountPairs(num_node, initial_edge_list, final_edge_list)
            print("%.4f, %.4f, %.4f, %.4f" % (num_node, degree, total_count/20/(num_node*num_node/2), total_count/20,))
