#!/usr/bin/env python

import zipfile, argparse, os, sys, nltk, operator, re
from collections import defaultdict
from nltk.tree import Tree
from nltk.parse import DependencyGraph
from nltk.corpus import wordnet as wn
from nltk.stem.wordnet import WordNetLemmatizer as wnl
from nltk.stem.snowball import SnowballStemmer as stemmer

###############################################################################
## Utility Functions ##########################################################
###############################################################################

# Read the file from disk
def read_file(filename):
    fh = open(filename, 'r')
    text = fh.read()
    fh.close()
    
    return text

# The standard NLTK pipeline for POS tagging a document
def get_sentences(text):
    sentences = nltk.sent_tokenize(text)
    sentences = [nltk.word_tokenize(sent) for sent in sentences]
    sentences = [nltk.pos_tag(sent) for sent in sentences]

    return sentences    
    
# bow = bag of words
# returns a set {}
# take out punctuation
def get_bow(tagged_tokens, stopwords):
    return set([t[0].lower() for t in tagged_tokens if t[0].lower() not in stopwords and t[1] not in '.'])
    
# given a sentence, and question bag of words
# chops off the first part of the sentence (before the qbow)
def find_phrase(tagged_tokens, qbow):
    for i in range(len(tagged_tokens) - 1, 0, -1):
        word = (tagged_tokens[i])[0]
        if word in qbow:
            return tagged_tokens[i+1:]

# This method takes as input the file extension of the set of files you want to open
# and processes the data accordingly
# Assumption: this python program is in the same directory as the training files
def getData(file_extension):
    dataset_dict = {}

    # iterate through all the files in the current directory
    for filename in os.listdir("."):
        if filename.endswith(file_extension):

            # get stories and cumulatively add them to the dataset_dict
            if file_extension == ".story" or file_extension == ".sch":
                dataset_dict[filename[0:len(filename)-len(file_extension)]] = open(filename, 'rU',encoding='latin1').read()

            # question and answer files and cumulatively add them to the dataset_dict
            elif file_extension == ".answers" or file_extension == ".questions":
                getQA(open(filename, 'rU', encoding='utf8'), dataset_dict)

            # return the dependencies as their own objects, not dict
            elif file_extension == ".story.par" or file_extension == ".sch.par":
                return filename, read_con_parses(filename)

            # question dependencies need more work to get since not just one block of text
            # hopefully not necessary

    return dataset_dict

# returns a dictionary where the question numbers are the key
# and its items are another dict of difficulty, question, type, and answer
# e.g. story_dict = {'fables-01-1': {'Difficulty': x, 'Question': y, 'Type':}, 'fables-01-2': {...}, ...}
def getQA(content, dataset_dict):
    qid = ""
    for line in content:
        if "QuestionID: " in line:
            qid = line[len("QuestionID: "):len(line)-1]
            # dataset_dict[qid] = defaultdict()
            dataset_dict[qid] = {}
        elif "Question: " in line: dataset_dict[qid]['Question'] = line[len("Question: "):len(line)-1]
        elif "Answer: " in line: dataset_dict[qid]['Answer'] = line[len("Answer:")+1:len(line)-1]
        elif "Difficulty: " in line: dataset_dict[qid]['Difficulty'] = line[len("Difficult: ")+1:len(line)-1]
        elif "Type: " in line: dataset_dict[qid]['Type'] = line[len("Type:")+1:len(line)-1]
    return dataset_dict

# get lowercased first word from a string
# useful for getting words like: who what when where why how
def getFirstWord(string):
    return string.split()[0].lower()

# word, pos -> (lemmatized word, pos)
def lemmatize(w,p):
    if p.startswith("N"):
        return (wnl.lemmatize(wnl,w,'n'),p)
    elif p.startswith("V"):
        return (wnl.lemmatize(wnl,w,'v'),p)
    else:
        return (w,p)

# given type ("Sch"/"Story") returns the sentences of either
# or both concatenated if "Sch | Story"
def getSentsByType(qtype, storyText, schText):

    # sentences = list of lists of tuples (word,pos)
    storySentences = get_sentences(storyText)

    # also get the same data for the Scheherezade version
    schSentences = get_sentences(schText)

    # both story + sch sentences
    bothSentences = storySentences + schSentences

    # the type of question - Sch or Story
    qtype = questions[q]['Type']
    # print(qtype)
        
    if qtype == "Sch":
        sentences = schSentences
    elif qtype == "Story":
        sentences = storySentences
    else: 
        # "Sch | Story" 
        sentences = bothSentences

    # lowercased sentences
    loweredSents = []
    for s in sentences:
        loweredSents.append([(w.lower(),p) for w,p in s])
    # print(loweredSents)

    return loweredSents

###############################################################################
## Chunking Functions #########################################################
###############################################################################

# Our simple grammar from class (and the book)
GRAMMAR =   """
            N: {<PRP>|<NN.*>}
            V: {<V.*>}
            ADJ: {<JJ.*>}
            NP: {<DT>? <ADJ>* <N>+}
            PP: {<IN> <NP>}
            VP: {<TO>? <V> (<NP>|<PP>)*}
            """

LOC_PP = set(["in", "on", "at"])

chunker = nltk.RegexpParser(GRAMMAR)

def read_file(filename):
    fh = open(filename, 'r')
    text = fh.read()
    fh.close()
    
    return text

def get_sentences(text):
    sentences = nltk.sent_tokenize(text)
    sentences = [nltk.word_tokenize(sent) for sent in sentences]
    sentences = [nltk.pos_tag(sent) for sent in sentences]
    
    return sentences

def pp_filter(subtree):
    return subtree.label() == "PP"

def is_location(prep):
    return prep[0] in LOC_PP

def find_locations(tree):
    # Starting at the root of the tree
    # Traverse each node and get the subtree underneath it
    # Filter out any subtrees who's label is not a PP
    # Then check to see if the first child (it must be a preposition) is in
    # our set of locative markers
    # If it is then add it to our list of candidate locations
    
    # How do we modify this to return only the NP: add [1] to subtree!
    # How can we make this function more robust?
    # Make sure the crow/subj is to the left
    locations = []
    for subtree in tree.subtrees(filter=pp_filter):
        if is_location(subtree[0]):
            locations.append(subtree)
    
    return locations

def find_candidates(sentences, chunker):
    candidates = []
    for sent in sentences:
        tree = chunker.parse(sent)
        # print(tree)
        locations = find_locations(tree)
        candidates.extend(locations)
        
    return candidates

def find_sentences(patterns, sentences):
    # Get the raw text of each sentence to make it easier to search using
    # regexes
    raw_sentences = [" ".join([token[0] for token in sent]) for sent in sentences]
    
    result = []
    for sent, raw_sent in zip(sentences, raw_sentences):
        for pattern in patterns:
            if not re.search(pattern, raw_sent):
                matches = False
            else:
                matches = True
        if matches:
            result.append(sent)
            
    return result


###############################################################################
## Parsing Functions ##########################################################
###############################################################################

# Read the constituency parse from the line and construct the Tree
def read_con_parses(parfile):
    fh = open(parfile, 'r')
    lines = fh.readlines()
    fh.close()
    return [Tree.fromstring(line) for line in lines]

# Read the lines of an individual dependency parse
def read_dep(fh):
    dep_lines = []
    for line in fh:
        line = line.strip()
        if len(line) == 0:
            return "\n".join(dep_lines)
        dep_lines.append(line)
        
    return "\n".join(dep_lines) if len(dep_lines) > 0 else None
            

# Read the dependency parses from a file
def read_dep_parses(depfile):
    fh = open(depfile, 'r')

    # list to store the results
    graphs = []
    
    # Read the lines containing the first parse.
    dep = read_dep(fh)
    
    # While there are more lines:
    # 1) create the DependencyGraph
    # 2) add it to our list
    # 3) try again until we're done
    while dep is not None:
        graph = DependencyGraph(dep)
        graphs.append(graph)
        
        dep = read_dep(fh)
    fh.close()
    
    return graphs 

def matches(pattern, root):
    if root is None and pattern is None: return root
    elif pattern is None:                return root
    elif root is None:                   return None
    
    plabel = pattern if isinstance(pattern, str) else pattern.label()
    rlabel = root if isinstance(root, str) else root.label()
    
    if plabel == "*":
        return root
    elif plabel == rlabel:
        for pchild, rchild in zip(pattern, root):
            match = matches(pchild, rchild) 
            if match is None:
                return None
        return root
    
    return None
    

def process_con(trees):
    tree = trees[1]
    
    pattern = nltk.ParentedTree.fromstring("(VP (*) (PP))")
    
    # get the first child of the tree because there
    # is a dummy ROOT node in there
    for subtree in tree[0].subtrees():
        node = matches(pattern, subtree)
        if node is not None:
            print(node)

    
def process_dep(graphs):
    graph = graphs[1]
    
    # TODO

###############################################################################
## Constituency Functions #####################################################
###############################################################################

# Read the constituency parse from the line and construct the Tree
def read_con_parses(parfile):
    fh = open(parfile, 'r')
    lines = fh.readlines()
    fh.close()
    return [Tree.fromstring(line) for line in lines]

# See if our pattern matches the current root of the tree
def matches(pattern, root):
    # Base cases to exit our recursion
    # If both nodes are null we've matched everything so far
    if root is None and pattern is None: 
        return root
        
    # We've matched everything in the pattern we're supposed to (we can ignore the extra
    # nodes in the main tree for now)
    elif pattern is None:                
        return root
        
    # We still have something in our pattern, but there's nothing to match in the tree
    elif root is None:
        return None

    # A node in a tree can either be a string (if it is a leaf) or node
    plabel = pattern if isinstance(pattern, str) else pattern.label()
    rlabel = root if isinstance(root, str) else root.label()
    
    # If our pattern label is the * then match no matter what
    if plabel == "*":
        return root
    # Otherwise they labels need to match
    elif plabel == rlabel:
        # If there is a match we need to check that all the children match
        # Minor bug (what happens if the pattern has more children than the tree)
        for pchild, rchild in zip(pattern, root):
            match = matches(pchild, rchild) 
            if match is None:
                return None
                
        return root
    
    return None
    
def pattern_matcher(pattern, tree):
    for subtree in tree.subtrees():
        node = matches(pattern, subtree)
        if node is not None:
            return node
    return None


###############################################################################
## Dependency Functions #######################################################
###############################################################################

# Read the lines of an individual dependency parse
def read_dep(fh):
    dep_lines = []
    for line in fh:
        line = line.strip()
        if len(line) == 0:
            return "\n".join(dep_lines)
        elif re.match(r"^QuestionId:\s+(.*)$", line):
            # You would want to get the question id here and store it with the parse
            continue
        dep_lines.append(line)
        
    return "\n".join(dep_lines) if len(dep_lines) > 0 else None
            

# Read the dependency parses from a file
def read_dep_parses(depfile):
    fh = open(depfile, 'r')

    # list to store the results
    graphs = []
    
    # Read the lines containing the first parse.
    dep = read_dep(fh)
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
        graphs.append(graph)
        
        dep = read_dep(fh)
    fh.close()
    
    return graphs 
    
def find_main(graph):
    for node in graph.nodes.values():
        if node['rel'] == 'ROOT':
            return node
    return None
    
def find_node(word, graph):
    for node in graph.nodes.values():
        if node["word"] == word:
            return node
    return None
    
def get_dependents(node, graph):
    results = []
    for item in node["deps"]:
        address = node["deps"][item][0]
        dep = graph.nodes[address]
        results.append(dep)
        results = results + get_dependents(dep, graph)
        
    return results

def find_answer(qgraph, sgraph):
    qmain = find_main(qgraph)
    qword = qmain["word"]
    
    snode = find_node(qword, sgraph)
    
    for node in sgraph.nodes.values():
        #print("node in nodelist:", node)
        if node.get('head', None) == snode["address"]:
            #print("Our parent is:", snode)
            #print("Our relation is:", node['rel'])
            if node['rel'] == "prep":
                deps = get_dependents(node, sgraph)
                deps = sorted(deps, key=operator.itemgetter("address"))
                
                return " ".join(dep["word"] for dep in deps)



# if __name__ == '__main__':
#     text_file = "fables-01.sch"
#     dep_file = "fables-01.sch.dep"
#     q_file = "fables-01.questions.dep"
    
#     # Read the dependency graphs into a list 
#     sgraphs = read_dep_parses(dep_file)
#     qgraphs = read_dep_parses(q_file)

#     # Get the first question
#     qgraph = qgraphs[0]    
    
#     # The answer is in the second sentence
#     # You would have to figure this out like in the chunking demo
#     sgraph = sgraphs[1]
#     lmtzr = WordNetLemmatizer()
#     for node in sgraph.nodes.values():
#         tag = node["tag"]
#         word = node["word"]
#         if word is not None:
#             if tag.startswith("V"):
#                 print(lmtzr.lemmatize(word, 'v'))
#             else:
#                 print(lmtzr.lemmatize(word, 'n'))
#     print()

#     answer = find_answer(qgraph, sgraph)
#     print(answer)


###############################################################################
## Question Answering Functions ###############################################
###############################################################################
    
# qtokens: is a list of pos tagged question tokens with SW removed
# sentences: is a list of pos tagged story sentences
# stopwords is a set of stopwords
def baseline(qbow, sentences, stopwords):


    # Collect all the candidate answers
    answers = []
    for sent in sentences:
        # A list of all the word tokens in the sentence
        sbow = get_bow(sent, stopwords)
        
        # Count the # of overlapping words between the Q and the A
        # & is the set intersection operator
        overlap = len(qbow & sbow)

        if overlap > 0:
            answers.append((overlap, sent))
        
    # Sort the results by the first element of the tuple (i.e., the count)
    # Sort answers from smallest to largest by default, so reverse it
    answers = sorted(answers, key=operator.itemgetter(0), reverse=True)

    # Return the best answer
    if len(answers) > 0:
        best_answer = (answers[0])[1]
    # return empty string if no overlap found
    else:
        best_answer = []

    # trim qbow words, likely not in answer
    best_answer = [(w,p) for w,p in best_answer if w not in qbow]

    return best_answer

# given a word, use wordnet to return list of similar words
def getSyns(word):
    return [s.name().split('.')[0] for s in wn.synsets(word)]

# given a part of speech, return all the words in a list of (word,POS) tuples
# that have the same POS as the one given
def getAllWordsWithPos(sentence, pos):
    return [w for w,p in sentence if pos == p]

# takes the baseline sentence, and returns the determiners and nouns
def baselineNouns(qbow, sentences, stopwords):
    bl = baseline(qbow, sentences, stopwords)
    # list(set(...)) removes duplicates
    return list(set([(w,p) for w,p in bl if p.startswith('D') or p.startswith('N')]))

# given a word(string) in a sentence[(word,pos)], 
# finds the nearest nouns
# if word not in sentence, just returns []
def getNounsNearWord(sentence, word):
    # max distance from word
    diff = 3
    wIndex = 0
    for i in range(len(sentence)):
        if sentence[i][0] == word:
            wIndex = i
    nIndices = []
    for i in range(len(sentence)):
        if sentence[i][1].startswith('N') and sentence[i][0] != word:
            nIndices.append(i)
            if i>0:
                # get the determiner as well if there is one
                if sentence[i-1][1].startswith('D'):
                    nIndices.append(i-1)
    # only return the found words that are close to the given word
    return [sentence[i] for i in nIndices if abs(i-wIndex) < diff]

# return nouns/dets near qbow words
def getNounsNearQBOW(sentence, qbow):
    result = []
    for w in list(qbow):
        result += getNounsNearWord(sentence, w)
    # trim duplicates
    return list(set(result))

# get location for "where" questions using chunking
# use baseline answer sentence in this
def getLocationFromBaseline(qsent, baselineSent):
    words = []
    for w,p in qsent:
        if p.startswith('N') or p.startswith('V'):
            words.append(lemmatize(w,p)[0])
    if len(words)>0:
        locSentences = find_sentences(words, baselineSent)
        locations = find_candidates(locSentences, chunker)
        if locations != []:
            # print([loc for loc in locations])
            return [loc.leaves() for loc in locations][0]
    return []

# chooses which method to use, based on the type of question being asked
# default to baseline
# TODO: get synsets of qbow words
# TODO: parsing - like in dependency-demo-stub.py
# TODO: refine qword categories: "what happened" (event) vs. "what was smashed" (object)
#   1. get all synonyms of qbow words
#   2. use these + baseline() to find which sentence has the answer
#   3. use parsing to extract exact answer
def answerQ(qtext, sentences, stopwords):

    qsent = get_sentences(qtext)[0]
    qbow = get_bow(qsent, stopwords)
    qword = qsent[0][0].lower()

    # start with the baseline answer
    answer = baseline(qbow, sentences, stopwords)
    # the determiners and nouns of the baseline sentence
    answerNouns = baselineNouns(qbow, sentences, stopwords)

    # if only one word in qbow, return the nouns near that word
    if len(list(qbow)) == 1:
        nounsNearWord = getNounsNearWord(answer,list(qbow)[0])
        if nounsNearWord != []:
            return nounsNearWord

    # get nouns near qbow words
    nounsNearQBOW = getNounsNearQBOW(answer, qbow)

    # if baseline failed, use lemmatized qbow
    if answer == []:
        # print("trying lemmatized")
        # if empty string, try lemmatized qbow
        qbowTagged = nltk.pos_tag(list(qbow))
        lemmaQBOW = set([lemmatize(w,p)[0] for w,p in qbowTagged])

        answer = baseline(lemmaQBOW, sentences, stopwords)
        answerNouns = baselineNouns(lemmaQBOW, sentences, stopwords)

    # split into cases of qwords
    if qword == "who":
        if 'story' in qbow:
            return list(set(getNounsNearWord(sentences[0],'a')+getNounsNearWord(sentences[0],'the')))
        else:
            if answerNouns != []: 
                return answerNouns
    elif qword == "what":
        if 'do' in [w for w,p in qsent]:
            # TODO: function to find verb phrases
            pass
        if 'happened' not in qbow:
            if answerNouns != []: 
                return answerNouns
        else:
            pass
    elif qword == "when":
        pass
    elif qword == "where":
        loc = getLocationFromBaseline(qsent, sentences)
        print(loc)
        if loc != []:
            return loc
        elif answerNouns != []: 
            return answerNouns
    elif qword == "why":
        pass
    elif qword == "how":
        pass
    
    return answer


###############################################################################
## Program Entry Point ########################################################
###############################################################################
if __name__ == '__main__':

    # optional functions for opening and organizing some of the data
    # if you do not understand how the data is being returned,
    # you can write your own methods; these are to help you get started

    stories = getData(".story") # returns a list of stories
    sch = getData(".sch") # returns a list of scheherazade realizations
    questions = getData(".questions") # returns a dict of questionIds
    answers = getData(".answers") # returns a dict of questionIds
    # read in other data, ".story.par", "story.dep", ".sch.par", ".sch.dep", ".questions.par", ".questions.dep"
    storiesPar = getData(".story.par")
    storiesDep = getData(".story.dep")
    schPar = getData(".sch.par")
    schDep = getData(".sch.dep")
    # TODO: write function to get the below to work
    # questionsPar = getData(".questions.par")
    # questionsDep = getData(".questions.dep")


    stopwords = set(nltk.corpus.stopwords.words("english"))

    # get the correct order to do questions in
    storyOrderFile = open("process_stories.txt",'r')
    storyOrder = storyOrderFile.read().split("\n")

    qids = []
    for story in storyOrder:
        storyqids = []
        # populate qids with sorted qids
        for i in range(1,len(questions)):
            qid = story+"-"+str(i)
            if qid in questions:
                storyqids.append(qid)
        qids += storyqids

    # actually process each question, print and write to file q+a's

    outfile = open("train_my_answers.txt",'w')

    for q in qids:
        for story in stories:
            # if the story name is in the question name
            if story in q:
                # write questions to stdout (not same format as file output)
                print("QuestionID: "+q)
                print("Difficulty: "+questions[q]['Difficulty'])
                print("Question: "+questions[q]['Question'])

                # raw text of question
                qtext = questions[q]['Question']

                # given the question type and both story, sch texts,
                # return the list of sentences of tagged (word,pos) tuples
                # concatenates both if type == "Story | Sch"
                sentences = getSentsByType(questions[q]['Type'], stories[story], sch[story])

                myStopWords = stopwords
                if 'Sch' not in questions[q]['Type']:
                    print('adding narrator')
                    myStopWords.add('narrator')

                # answerQ = choose which method to use, default to baseline, return answer
                answer = answerQ(qtext, sentences, myStopWords)

                # write answer to stdout
                print("Answer: "+(" ".join(t[0] for t in answer))+"\n")

                # write questionid, answer to file
                outfile.write("QuestionID: "+q+"\n")
                outfile.write("Answer: "+(" ".join(t[0] for t in answer))+"\n\n")

    outfile.close()