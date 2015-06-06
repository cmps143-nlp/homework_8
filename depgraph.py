#!/usr/bin/env python
'''
Created on May 14, 2014

@author: reid
'''

import os, re, sys, nltk, operator
from nltk.parse import DependencyGraph
from nltk.stem.wordnet import WordNetLemmatizer
import utils
import baseline as bl
import hw6

# Note: the dependency tags return by Stanford Parser are slightly different than
# what NLTK expects. We tried to change all of them, but in case we missed any, this
# method should correct them for you.
def update_inconsistent_tags(old):
    return old.replace("root", "ROOT")

# Read the lines of an individual dependency parse
def read_dep(fh):
    dep_lines = []
    qid = None
    first = True
    for line in fh:
        #if(first): print (line)
        line = line.strip()
        if len(line) == 0:
            #print("\n".join(dep_lines))
            #input('>')
            return (update_inconsistent_tags("\n".join(dep_lines)), qid)
        elif re.match(r"^QuestionId:\s+(.*)$",line):
            # You would want to get the question id here and store it with the parse
            qid = line[len("QuestionID: "):len(line)]
            continue
        dep_lines.append(line)

    return (update_inconsistent_tags("\n".join(dep_lines)), qid) if len(dep_lines) > 0 else (None,qid)

# Read the dependency parses from a file
def read_dep_parses(depfile):
    fh = open(depfile, 'r')

    # list to store the results
    graphs = []
    qgraphs = {}
    # Read the lines containing the first parse.
    dep,qid = read_dep(fh)

#     print(dep)
#     graph = DependencyGraph("""There   EX      3       expl
# once    RB      3       advmod
# was     VBD     0       ROOT
# a       DT      5       det
# crow    NN      3       nsubj""")
#     graphs.append(graph)

    # While there are more lines:
    # 1) create the DependencyGraph
    # 2) add it to our list
    # 3) try again until we're done
    while dep is not None:
        graph = DependencyGraph(dep)
        if(qid):
            qgraphs[qid] = graph
        else:
            graphs.append(graph)
        dep,qid = read_dep(fh)
    fh.close()

    return graphs if len(qgraphs.items()) < 1 else qgraphs

def get_relation(dgraph, node, rel):
    #node['deps'][rel]
    i = node['deps'][rel][0]
    return node_ati(dgraph, i)


def find_relation(graph, rel, root=None):
    ''' finds nodes related to root with relation rel.
    root defaults to entire graph root.'''
    if root:
        node_list =  root.deps()
    else:
        node_list = graph.nodes.values()
    nodes = []
    for node in node_list:
        if not 'rel' in node.keys():
            continue
        if node['rel'] == rel:
            nodes.append(node)
    return nodes

def node_ati(graph, index):
    ''' returns the node object with address = index if it exists,
    otherwise returns None. '''
    for node in graph.nodes.values():
        if node['address'] == index:
            return node
    return None

def find_main(graph):
    for node in graph.nodes.values():
        if node['rel'] == 'ROOT':
            return node
    return None

def find_nodeByWord(word, graph, overlap=False, tag='VB'):
    nodelist = []
    #print('word: ', word)
    for node in graph.nodes.values():
        if not "word" in node.keys():
            continue
        #if word == 'stood' or word == 'standing':
          #  print(bl.lemmatize(word, tag) , bl.lemmatize(node["word"], node["tag"]))
        w1, t = bl.lemmatize(word, tag)
        w2, t = bl.lemmatize(node["word"], node["tag"])
        if node["word"] == word:
            nodelist.append(node)
        elif w1 == w2:
            '''print(node)
            print(w1, w2)
            print('.')'''
            nodelist.append(node)
        elif overlap:
            #print('w1: ', word, '\tw2: ', node["word"])
            if utils.overlap(word, node["word"], 3):
                #print('overlp: ', node)
                nodelist.append(node)
        '''else:
            synonyms = bl.getSyns(word)
            if node['word'] in synonyms:
                nodelist.append(node) '''
    return nodelist

def good_address(lst, addr):
    size = len(lst)
    return 0<= addr and addr < size

def get_neighbors(lst, a, n):
    res = []
    for i in range(n):
        # range starts at zeor so add 1.
        if good_address(lst, a +i  +1):
            res.append(lst[ a+i  +1])
        if good_address(lst, a -i  -1):
            res.append(lst[ a-i -1])
    return res

def get_dependents_shallow(node, graph, dmax, depth, n):
    results = []
    if depth > dmax:
        return results
    for item in node["deps"]:
        address = node["deps"][item][0]
        results += get_neighbors(graph.nodes, address, n)
        dep = graph.nodes[address]
        results.append(dep)
        results = results + get_dependents_shallow(dep, graph, dmax, depth+1, n)
    return results

def graph2sent(sgraph):
    ''' returns a pos tagged and lower()ed sentence. '''
    words = []
    words = [ ((node['word']).lower(), node['tag']) for node in sgraph.nodes.values()
                    if 'word' in node.keys() if 'tag' in node.keys() if node['word'] ]
    #for node in sgraph.nodes.values():
     #   if 'word' in node.keys() and 'tag' in node.keys():
       #     words.append(((node['word']).lower(), node['tag']))
    return words

def get_segment_after_word( vnode, sent):
    # sch sentences are short so return everthing following the verb.
    #if qtype == 'sch':
    ans = [w[0] for w in sent]
    addr = vnode['address'] +1
    wanted = set(['DT', 'TO', 'IN'])
    # also add the previous word if it is a determinr
    if sent[addr-1][1] in wanted:
        addr -= 1
    ans = ans[addr : addr+10]
    return " ".join(ans).rstrip(' .,!\n?')

def get_dependents(node, graph):
    results = []
    for item in node["deps"]:
        address = node["deps"][item][0]
        dep = graph.nodes[address]
        results.append(dep)
        results = results + get_dependents(dep, graph)

    return results

def get_relatives(graph, rel, i=0, pos=None):
    relatives = find_relation(graph, rel)
    if pos:
        for r_node in relatives:
            n = node_ati(graph, r_node['address'] -i)
            if n['tag'] == pos:
                relatives.append(n)
    return [r["word"] for r in relatives]

def get_all_byWord(glist, target_word):
    targlist = []
    length = len(glist)
    for g in range(length):
        nodes = find_nodeByWord(target_word, glist[g])
        if len(nodes) > 0:
            targlist.append((nodes, g))
    return targlist

def find_answer(qgraph, sgraph):
    #print('qgraph: \n', qgraph, '\n')
    qmain = find_main(qgraph)
    assert qmain
    #print('qmain: \n',qmain, '\n')
    qword = qmain["word"]
    #print('qword: ', qword)
    #print(type(sgraph))

    #print('sgraph: \n', sgraph)
    snode = None
    try:
        snode = find_nodeByWord(qword, sgraph)
    except KeyError:
        #print('qgraph: ', qgraph)
        #print()
        #print('sgraph: ', sgraph)
        #input('>')
        pass

    if not snode:
        print('error: find_answer() not snode')
        return None
    for node in sgraph.nodes.values():
        #print("node in nodelist:", node)
        #print(type(node))
        if node.get('head', None) == snode["address"]:
            #print("Our parent is:", snode)
            #print("Our relation is:", node['rel'])
            if node['rel'] == "prep":
                deps = get_dependents(node, sgraph)
                deps = sorted(deps, key=operator.itemgetter("address"))

                return " ".join(dep["word"] for dep in deps)


def find_answer2(qgraph, sgraph):
    qmain = find_main(qgraph)
    deps = get_dependents_shallow(qmain, sgraph, 3, 0, 0)
    #deps = sorted(deps, key=operator.itemgetter("address"))
    deps = set(dep['word'].lower() for dep in deps if 'word' in dep.keys() if dep['word'])
    return " ".join( w for w  in deps )#if dep['word'])

def load_dep_files(file_extension):
    dep_graphs = {}
    for filename in os.listdir("."):
        if filename.endswith(file_extension):
            graphs = read_dep_parses(filename)
            if file_extension == ".questions.dep":
                dep_graphs.update(graphs)
            else:
                dep_graphs[filename[:-len(file_extension)]]= graphs
    #print(dep_graphs)
    #input('>')
    return dep_graphs

def load_all_deps():
    sch_deps_extension = ".sch.dep"
    story_deps_extension = ".story.dep"
    q_deps_extension = ".questions.dep"
    sdeps = {}
    sdeps['sch'] = load_dep_files(sch_deps_extension)
    sdeps['story'] = load_dep_files(story_deps_extension)
    qdeps = load_dep_files(q_deps_extension)
    return sdeps, qdeps

def find_q(qlist, target):
    for q, i in zip(qlist, range(len(qlist))):
        if q.qid == target:
            return i
    return None













if __name__ == '__main__':
    text_file = "fables-01.story"
    dep_file = "fables-01.story.dep"
    q_file = "fables-01.questions.dep"

    # dict
    sgraphs = read_dep_parses(dep_file)
    # list
    qgraphs = read_dep_parses(q_file)

    # Get the question
    questions = hw6.load_questions()
    i = find_q(questions, 'fables-01-2')

    question = questions[i]
    assert question
    print('question: ')
    print(question)
    # qgraph is a dict not a list
    qgraph = qgraphs['fables-01-2']
    #print("qgraph: ",qgraph)

    # find the sentence containing the answer
    #qsent  = bl.get_sentences(question)[0]
    """
    sgraph = sgraphs[1]
    lmtzr = WordNetLemmatizer()
    for node in sgraph.nodes.values():
        tag = node["tag"]
        word = node["word"]
        if word is not None:
            if tag.startswith("V"):
                print(lmtzr.lemmatize(word, 'v'))
            else:
                print(lmtzr.lemmatize(word, 'n'))
    print()

    answer = find_answer(qgraph, sgraph)
    print(answer)
    """
