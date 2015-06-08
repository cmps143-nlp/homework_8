#!/usr/bin/env python
"""
Davan Harrison
05/20/15
CS143
Spring
Dr. Walkers class
assignment 7

This is a Question Answering module.
"""

from nltk.stem.wordnet import WordNetLemmatizer as wnl
import zipfile, argparse, os
from collections import defaultdict
import nltk
import re
from nltk.stem.wordnet import WordNetLemmatizer
import chunk
import depgraph
import constgraph
import baseline as bl
import sys
import utils
import csv
from nltk.corpus import wordnet as wn

###############     Globals     #######################
global all_texts
###############################################################################
## Utility Functions ##########################################################
###############################################################################

def starts_with_vowel(word):
    vowels = ['a', 'i', 'e', 'o', 'u']
    for v in vowels:
        if word.lower().startswith(v):
            return True
    return False

def basename(q_ident):
    return q_ident[:q_ident.rfind('-')]

# This method takes as input the file extension of the set of files you want
# to open and processes the data accordingly.
#Assumption:this python program is in the same directory as the training files
def getData(file_extension):
    """returns  dataset_dict    -- k: filename in filename.file_extension
                                -- v: file contents         """
    dataset_dict = {}
    # iterate through all the files in the current directory
    for filename in os.listdir("."):
        if filename.endswith(file_extension):
            # get stories and cumulatively add them to the dataset_dict
            if file_extension == ".story" or file_extension == ".sch":
                target_dataset = filename[:len(filename)-len(file_extension)]
                dataset_dict[target_dataset] = open(filename, 'rU').read()
            # question and answer files and cumulatively add them to
            # the dataset_dict
            elif file_extension == ".questions":
                getQA(open(filename, 'rU', encoding="latin1"), dataset_dict)
    return dataset_dict

# returns a dictionary where the question numbers are the key
# and its items are another dict of difficulty, question, type, and answer
# e.g. story_dict = {'fables-01-1': {'Difficulty': x, 'Question': y, 'Type':},
#                       'fables-01-2': {...}, ...}
def getQA(content, dataset_dict):
    qid = ""
    for line in content:
        if "QuestionID: " in line:
            qid = line[len("QuestionID: "):len(line)-1]
            # dataset_dict[qid] = defaultdict()
            dataset_dict[qid] = {}
        elif "Question: " in line:
            dataset_dict[qid]['Question'] = line[len("Question: "):len(line)-1]
        elif "Answer: " in line:
            dataset_dict[qid]['Answer'] = line[len("Answer:")+1:len(line)-1]
        elif "Difficulty: " in line:
            dataset_dict[qid]['Difficulty'] = line[
                                            len("Difficult: ")+1:len(line)-1]
        elif "Type: " in line:
            dataset_dict[qid]['Type'] = line[len("Type:")+1:len(line)-1]
    return dataset_dict

def load_questions():
    """ returns a list of question objects. """
    file_extension = '.questions'
    q_dict = {}
    # iterate through all the files in the current directory
    for filename in os.listdir("."):
        if filename.endswith(file_extension):
            getQ(open(filename, 'rU', encoding="latin1"), q_dict)
    return [ v for (k,v) in q_dict.items() ]

# returns a dictionary where the question numbers are the key
def getQ(content,  q_list):
    for line in content:
        if "QuestionID: " in line:
            qident = line[len("QuestionID: "):len(line)-1]
            q_list[qident] = Question(qid=qident)
            q_list[qident].text_name = basename(qident)
        elif "Question: " in line:
            q_list[qident].question = line[len("Question: "):len(line)-1]
        elif "Difficulty: " in line:
            q_list[qident].difficulty = line[len("Difficult: ")+1:len(line)-1]
        elif "Type: " in line:
            q_list[qident].set_type(line[len("Type:")+1:len(line)-1] )
    return q_list

def load_text():
    dataset_dict = {}
    dataset_dict["sch"] = {}
    dataset_dict["story"] = {}
    dataset_dict["noun_ids"] = load_wordnet_ids("Wordnet_nouns.csv")
    dataset_dict["verb_ids"] = load_wordnet_ids("Wordnet_verbs.csv")
    # iterate through all the files in the current directory
    for filename in os.listdir("."):
        if filename.endswith(".story"):
            target_dataset = filename[0:len(filename)-len("story")].strip(' .')
            dataset_dict["story"][target_dataset] = open(filename, 'rU').read()
        elif filename.endswith(".sch"):
            target_dataset = filename[0:len(filename)-len("sch")].strip(' .')
            dataset_dict["sch"][target_dataset] = open(filename, 'rU').read()
    # print(dataset_dict["noun_ids"])
    return dataset_dict

def form(q):
    return (idtoint(q.qid), q.qid, q.answer)

def out_list(q_list, start, order_list=None):
    if False: #order_list:
        names = order_list
    else:
        names = [q.text_name for q in q_list if q.text_name.startswith(start)]
        names = [ n for n in set(names) ]
        names.sort()
    sorted_questions = []
    i = 1
    for name in names:
        #print(i,' ', name)
        story_qlist = []
        for q in q_list:
            if q.text_name == name:
                story_qlist.append(form(q))
        story_qlist.sort()
        sorted_questions.extend(story_qlist)
        i +=1
    return sorted_questions

def output_response(out_file, q_list,  ans_output_order=None):

    sorted_list = []
    if ans_output_order:
        order = [name.rstrip(' \t\n') for name in ans_output_order]
        for name in order:
            sorted_list += out_list(q_list, name)

    else:
        sorted_list = list(out_list(q_list,'fable', ans_output_order) + out_list(q_list, 'blog', ans_output_order))

    with open(out_file, 'w') as fout:
        for q in sorted_list:
            fout.write("QuestionID: " + q[1]+ '\n')
            fout.write("Answer: ")
            if(q[2]):
                fout.write(q[2])
            fout.write('\n\n')

def idtoint(qid):
    i = qid.rfind('-')
    Id = qid[i+1:]
    return int(Id)

def find_q(qlist, target):
    for q,i in zip(qlist, range(len(qlist))):
        if q.qid == target:
            return i
    return None

# for loading wordnet CSVs
def load_wordnet_ids(filename):
    file = open(filename, 'r')
    if "noun" in filename: type = "noun"
    else: type = "verb"
    csvreader = csv.DictReader(file, delimiter=",", quotechar='"')
    word_ids = defaultdict()
    for line in csvreader:
        word_ids[line['synset_id']] = {'synset_offset': line['synset_offset'], 'story_'+type: line['story_'+type], 'stories': line['stories']}
    return word_ids

# uses the wordnet dicts given for HW8 to get the correct synset for a word
# returns a list of words in that synset
# or just the word if no synset was matched
def get_synset(word):
    word_synsets = wn.synsets(word)
    for c in word_synsets:
        if c.name() in all_texts['noun_ids'] or c.name() in all_texts['verb_ids']:
            # return c.name()
            return (bl.getSyns(c.name().split('.')[0]))
            # print(c.name())
            # print(all_texts['noun_ids'][c.name()])
            # print(c.hypernyms())
            
    # if we didn't find the word in the wordnet dicts given in hw8
    # just return the default synonyms
    return bl.getSyns(word)

###############################################################################
## Question Answering Functions ###############################################
###############################################################################

#########   class Question  ####################
class Question:
    """ A question to be answered by my Question Answerer.
    Static Attributes:
        text_depgraphs -- A dictionary of the story dependency graphs.
                            k = 'fables-01'|'fables-02 | 'blogs-01'
                            v = list of dependency graphs for that file
        q_depgraphs -- A dictionary of the question dependency graphs.
                        k = question id.
                        v = dependency graph for the question.

        text_constgraphs -- A dictionary of the story constituency graphs.
                            k = 'fables-01'|'fables-02 | 'blogs-01'
                            v = list of constituency graphs for that file
        q_constgraphs -- A dictionary of the question constituency graphs.
                        k = question id.
                        v = constituency graph for the question.
    Attributes:
        qid -- question id.
        question -- The question to be answered.
        answer -- The answer to the question.
        difficulty -- The difficulty of the question.
        qtype   -- The places where the anser can be found.
        text_name   -- name of text corpus.
        score   -- tuple of (recall, precision, f-measure)
    Methods:
        solve_question  -- looks for the answer to question in the
                            appropriate text.
        text_name       -- returns the text where the question can be found.
        solve_depgraph  -- looks for an answer to the question using
                            dependancey graphs.
        get_text        -- gets the tagged and tokenized text associated with
                            the question.
        solve_basline   -- Looks for an answer to the question using the
                            basline methods.
        solve_constragh -- looks for an answer to the question using the
                            constituency graph methods.
    """
    text_depgraphs = {}
    q_depgraphs = {}
    text_constgraphs = {}
    q_constgraphs = {}

    def set_type(self, qtype):
        ''' Sometimes the last letter of the type is striped off
            so this functions repairs the incomplete type label.
        '''
        tlist = []
        for qt in qtype.split('|'):
            qt = qt.strip().lower()
            if qt == 'sc':
                qt = 'sch'
            elif qt == 'stor':
                qt = 'story'
            tlist.append(qt)
        self.qtype = tlist

    def __init__(self, qid='none', question='none', answer='none',
                    difficulty='none', qtype=[] ):
        """ stub """
        self.qid = qid
        self.question = question
        self.answer = answer
        self.answer_sch = "none"
        self.answer_story = "none"
        self.difficulty = difficulty
        self.qtype = qtype
        self.score = ()
        if(len(qtype) > 0):
            set_type(qtype)
        self.text_name = str()
        #set_qtype(qtype)

        # load dep graphs if needed
        if len(Question.text_depgraphs) < 1:
            (Question.text_depgraphs,
            Question.q_depgraphs) = depgraph.load_all_deps()
        # load con graphs if needed
        if len(Question.text_constgraphs) < 1:
            (Question.text_constgraphs,
            Question.q_constgraphs) = constgraph.load_all_graphs()

        assert len(Question.text_depgraphs) > 0
        assert len(Question.q_depgraphs) > 0
        assert len(Question.text_constgraphs) > 0
        assert len(Question.q_constgraphs) > 0

    def __str__(self):
        s = 'id: '+self.qid +'\n'+'Question: '+self.question
        s =s+'\n'+'Story Ans: '+self.answer_story+'\n'+'Text: '+self.text_name
        s = s + '\n' + 'Type: '  + ' or '.join(self.qtype)
        return s

    def story_deps(self, stype):
        return Question.text_depgraphs[stype][self.text_name]

    def best_sent(self, keyword=None):
        stopwords = set(nltk.corpus.stopwords.words("english"))
        # use sch whenever possible
        if 'sch' in self.qtype:
            qtype = 'sch'
        else:
            qtype = 'story'
        # find sentence with answer
        qsent = bl.get_sentences(self.question)[0]
        qbow = bl.get_bow(qsent, stopwords)
        #sents = bl.get_sentences(all_texts[qtype][self.text_name])

        sgraphs = Question.text_depgraphs[qtype][self.text_name]

        sents = [ depgraph.graph2sent(g) for g in sgraphs ]

        #print(len(sents))
        best_sent,index = bl.baseline(qbow, sents, stopwords, keyword)
        return best_sent, index, qtype

    def solve_depgraph(self):
        stopwords = set(nltk.corpus.stopwords.words("english"))
        base_ans = self.solve_baseline(stopwords)
        # find sentence with answer
        qsent = bl.get_sentences(self.question)[0]
        qbow = bl.get_bow(qsent, stopwords)
        sents = bl.get_sentences(all_texts[self.qtype[0]][self.text_name])
        best_sent,index = bl.baseline(qbow, sents, stopwords)
        self.answer = " ".join(t[0] for t in best_sent)
        qtype = self.qtype[0]

        # find answer in sentence
        sgraph = self.get_dgraph(qtype,index)
        qgraph = Question.q_depgraphs[self.qid]
        working_ans = depgraph.find_answer2(qgraph, sgraph)
        self.answer = working_ans

        baseans = set(w for w in base_ans.split())
        depans = set(w for w in working_ans.split())
        for entry in baseans:
            depans.add(entry)
        alist = [ a for a in depans if a in baseans]
        self.answer = " ".join(alist)
        return self.answer

    def get_text(self, qtype=None):
        ''' Returns the tokenized and taggeed text associated with qtype
            (sch or story).
            If no qtype is given then it returns whichever is first in
            the list of types.
        '''
        text = ""
        #for t in self.qtype:
         #   text += all_texts[t][self.text_name]
        if not qtype:
            qtype = self.qtype[0]
        text = all_texts[qtype][self.text_name]
        return text

    def solve_nic_baseline(self, stopwords):
        # print(self.difficulty,self.qid, self.question)
        sentences = bl.get_sentences(self.get_text())
        myStopWords = stopwords
        if self.qtype == 'sch':
            myStopWords.add('narrator')
        ans = bl.answerQ(self.question, sentences, myStopWords)
        self.answer = " ".join(w[0] for w in ans)
        #self.answer += ' ?'

    def get_dgraph(self, stype, sent_index):
        return Question.text_depgraphs[stype][self.text_name][sent_index]

    def solve_baseline(self, stopwords, keyWord=None):
        print(self.qid)
        # question is only one sentence so list has one item.
        qsent  = bl.get_sentences(self.question)[0]
        # bag of words
        qbow = bl.get_bow(qsent, stopwords)
        sentences = bl.get_sentences(self.get_text())
        answer,i = bl.baseline(qbow, sentences, stopwords, keyWord)
        #print('answer: ' , answer)
        key = set(['NN' , 'NNP', 'JJ'])#, 'JJ', 'VBN', 'VB'])
        ans = set([ t[0] for t in answer if t[1] in key] )
        ans.add('a')
        ans.add('the')
        self.answer = " ".join(w for w in ans)
        return self.answer

    def solve_constgraph(self):
        pass

    def solve_who(self):
        #return
        global all_texts
        stopwords = set(nltk.corpus.stopwords.words("english"))
        last = utils.last_word(self.question.rstrip(' !?.;\"n'))
        #if False:
        if 'sch' in self.qtype:
            qtype = 'sch'
        else:
            qtype = 'story'
        if (last.lower() == 'about'):
            self.answer = bl.find_most_common(
                all_texts[qtype][self.text_name],'NN', 'JJ', 3, stopwords)
            self.answer += ' a'

        else:
            #return
            # find sentence with answer
            qsent = bl.get_sentences(self.question)[0]
            # the question word is not so signigicant so remove it.
            qsent.pop(0)
            qbow = bl.get_bow(qsent, stopwords)

            # for w in qbow:
            #     print(bl.getSyns(w))

            sents = bl.get_sentences(all_texts[qtype][self.text_name])
            best_sent,index = bl.baseline(qbow, sents, stopwords)
            self.answer = " ".join(t[0] for t in best_sent)

            # find answer in sentence
            sgraph = self.get_dgraph(qtype,index)
            words = depgraph.get_relatives(sgraph, 'nsubj', 1, 'det')
            words = set(words)
            # add some words depending on type of question
            w = next(iter(words))
            if(len(words) == 1 and starts_with_vowel(w)):
                words.add('an')
            elif qtype == 'sch':
                words.add('the')
            else:
                words.add('a')
            self.answer = ' '.join(words)

    def solve_where(self):
        """
        start1 = "where was the "
        start2 = "where did the"
        qstring = self.question.lower()
        if qstring.startswith(start1) or qstring.startswith(start2):
            sent = self.question.split()
            print()
            print(self.question)
            if len(sent) > 4:
                subj = sent[3].rstrip(' !?.;\"n')
                verb = sent[4].rstrip(' !?.;\"n')
                print('subject: ', subj)
                print('verb: ', verb)

                # find verb in text sentence
                i = 0
                text_sents = nltk.sent_tokenize(all_texts[self.qtype[0]][self.text_name])
                num_sents = len(text_sents)
                verb_nodes = []
                for g in range(num_sents):
                    print('g: ', g)
                    sgraph = self.get_dgraph(self.qtype[0], g)
                    nlist = depgraph.find_nodeByWord(verb, sgraph, True, "VB")
                    print(nlist)
                    if len(nlist) > 0:

                        verb_nodes += [(nlist, g)]

                length = len(verb_nodes)
                answer = ""
                for n_list, sent_num in verb_nodes:
                    print('sent_num: ', sent_num)
                    #n_list, sent_num = match[0], match[1]
                    sgraph = self.get_dgraph(self.qtype[0], sent_num)
                    sent = text_sents[sent_num]
                    #print('sent num:', sent_num)
                    for n in n_list:
                        print('n: ', n)
                        if 'nmod' in n['deps'].keys():
                            #print('n: ', n)
                            nmod = depgraph.get_relation(sgraph, n, 'nmod')
                            case = depgraph.get_relation(sgraph, nmod, 'case')
                            det = depgraph.get_relation(sgraph, nmod, 'det')
                            answer += case['word'] + ' ' + det['word'] + ' ' + nmod['word']
                        elif n['rel'] == 'conj':
                            i = n['head']
                            parent = depgraph.node_ati(sgraph, i)
                            print('parent: ', parent)
                            if 'nmod' in parent['deps'].keys():
                                nmod = depgraph.get_relation(sgraph, parent, 'nmod')
                                print('nmod: ', nmod)
                                if 'case' in nmod['deps'].keys():
                                    case = depgraph.get_relation(sgraph, nmod, 'case')
                                    answer += ' '+ case['word']
                                if 'det' in nmod['deps'].keys():
                                    det = depgraph.get_relation(sgraph, nmod, 'det')
                                    answer += ' ' + det['word']
                                answer += ' ' + nmod['word']
                                print(answer)
                        print(answer)
                    #print(self.answer)
                self.answer = answer
                print(self.answer)
               # else:
                 #   pass
                   # print("solve_where() error: length != 1")

            else:
                # no verb
                subj = sent[3]
                print("solve_where() error: no verb")
                pass
        else:
            pass
        """
        stopwords = set(nltk.corpus.stopwords.words("english"))
        self.solve_nic_baseline(stopwords)
        #self.answer += ' !'
        #print('end solve_where')

    def solve_why(self):
        #return
        stopwords = set(nltk.corpus.stopwords.words("english"))
        # find sentence with answer
        qsent = bl.get_sentences(self.question)[0]
        # the question word is not so significant, so remove it.
        qsent.pop(0)
        qbow = bl.get_bow(qsent, stopwords)
        sents = bl.get_sentences(all_texts[self.qtype[0]][self.text_name])
        best_sent,index = bl.baseline(qbow, sents, stopwords, 'because')
        self.answer = " ".join(t[0] for t in best_sent)
        qtype = self.qtype[0]
        ans = bl.select(best_sent, 'because', 30)
        if len(ans) < 4:
            ''' not very accurate. needs improvement. '''
            self.solve_baseline(stopwords, 'because')
            #self.answer += ' &'
        else:
            # accurate
            self.answer = " ".join(ans)
            #self.answer += ' %'

    def solve_do(self,qsent, vindex, qtype, verb ):
        answer = ""
        # look for nouns folling verb
        dobj, i = utils.first(qsent, 'NN', vindex+1)
        if (dobj and i):
            # we found a noun
            # find all instances of the noun in the story
            num_sents = len(nltk.sent_tokenize(all_texts[qtype][self.text_name]))
            for g in range(num_sents):
                dobj_nodes = []
                sgraph = self.get_dgraph(qtype,g)
                dobj_nodes += depgraph.find_nodeByWord(dobj, sgraph)
                if len(dobj_nodes) > 0:
                    # if the noun has a direct object relationship with it head
                    # then we save the head word
                    for n in dobj_nodes:
                        if n['rel'] == 'dobj':
                            parent = depgraph.node_ati(sgraph,n['head'])
                            if (parent and 'word' in parent.keys()):
                                answer += parent['word'] + ' '
                        elif 'acl:relcl' in n['deps'].keys():
                            rels = n['deps']['acl:relcl']
                            addr = None
                            if (rels and len(rels) == 1):
                                addr = rels[0]
                            child = depgraph.node_ati(
                                sgraph,addr)
                            if (child and 'word' in child.keys()):
                                    answer += child['word'] + ' '
            self.answer = answer
        else:
            stopwords = set(nltk.corpus.stopwords.words("english"))
            self.solve_nic_baseline(stopwords)
            #print('do')
            #print('verb: ', verb)
            #print('qid: ' , self.qid)
            pass

    def solve_what(self):
        stopwords = set(nltk.corpus.stopwords.words("english"))
        unwanted = " \t\n.!?,"
        start1 = 'what did the '
        start2 = 'what was the '
        qsent = self.question.lower()

        if qsent.startswith(start1) or qsent.startswith(start2):
            # find subject and verb in question
            sent = qsent.split()
            qsent = bl.get_sentences(self.question)[0]
            subj, sindex = utils.first(qsent, 'NN')

            if sindex + 1 >= len(sent) :
                return self.solve_nic_baseline(stopwords)
            '''
            print()
            print('qid: ', self.qid)
            print('qsent: ', qsent)
            print('sent: ', sent)
            print('sindex: ', sindex)
            print('subj: ', subj)
            '''
            verb = sent[sindex+1].rstrip(unwanted)

            
            print(get_synset(verb))

            if verb == 'say':
                verb = 'said'
            #print('verb: ', verb)
            # find verb in text sentence
            bsent, index, qtype = self.best_sent(verb)
            '''print('bsent: ', bsent)
            print('bsent index: ', index)
            print(qtype)'''
            sgraph = self.get_dgraph(qtype,index)
            #print('sgraph: ', sgraph)
            #print(qtype)
            nodes = depgraph.find_nodeByWord(verb, sgraph, overlap=True)

            # extract answer from text
            length = len(nodes)
            if length <1:
                lemVerb = wnl.lemmatize(wnl, verb,'v')
                if lemVerb == 'do':
                    self.solve_do(qsent, sindex+1, qtype, verb)
                else:
                    #print('<1', verb)
                    #self.solve_nic_baseline(stopwords)
                    # use sch whenever possible
                    if 'sch' in self.qtype:
                        qtype = 'sch'
                    else:
                        qtype = 'story'
                    sents = self.get_text(self.qtype[0]).lower()
                    #sents = bl.get_sentences(sents)

                    start = sents.find(verb)
                    if (start >= 0):
                        end1 = sents.find('.', start)
                        answer = sents[start+len(verb) +2 : end1]
                        end2 = answer.find(',')
                        if end2 > 0:
                            answer = answer[:end2]
                        #print(answer)
                        self.answer = answer
                    else:
                        self.solve_nic_baseline(stopwords)
            elif length == 1:
                self.answer = depgraph.get_segment_after_word(nodes[0], bsent)
            else:
                self.solve_nic_baseline(stopwords)
                print('error in solve_what(): verb appears more than once')
                #print([n['word'] for n in nodes])
                #print()
                #return
        else:
            self.solve_nic_baseline(stopwords)
        #self.answer += '..'


    def solve(self):
        # question is only one sentence so list has one item.
        qsent  = bl.get_sentences(self.question)[0]
        w1 = qsent[0][0].lower()
        if w1== 'what':
            self.solve_what()
            #stopwords = set(nltk.corpus.stopwords.words("english"))
            #self.solve_nic_baseline(stopwords)

        elif w1 == 'who':
            self.solve_who()

        elif w1 == 'where':
            self.solve_where()
            pass
        elif w1 == 'why':
            self.solve_why()
            pass
        elif w1 == 'how':
            stopwords = set(nltk.corpus.stopwords.words("english"))
            self.solve_nic_baseline(stopwords)
            pass
        elif w1 == 'when':
            stopwords = set(nltk.corpus.stopwords.words("english"))
            self.solve_nic_baseline(stopwords)
            pass
        #print(qsent)
        #return self.answer

###### end class Question   #########

def get_questions():
    return load_questions()

def run_depQA():
    questions = load_questions()
    for q in questions:
        q.solve_depgraph()
    output_response("train_my_answers.txt", questions)

def run_conQA():
    questions = load_questions()
    stopwords = set(nltk.corpus.stopwords.words("english"))
    for q in questions:
        if not q.solve_constgraph():
            q.solve_baseline(stopwords)
    output_response("train_my_answers.txt", questions)

def run_baselineQA():
    questions = load_questions()
    stopwords = set(nltk.corpus.stopwords.words("english"))
    for q in questions:
        q.solve_baseline(stopwords)
        #q.solve_nic_baseline(stopwords)
    output_response("train_my_answers.txt", questions)

def run_QA(output_list):
    questions = load_questions()
    stopwords = set(nltk.corpus.stopwords.words("english"))
    for q in questions:
        #if not q.qid == 'blogs-05-14': #'fables-01-5':
         #   continue
        q.solve()
    output_response("train_my_answers.txt", questions, output_list)



###############################################################################
## Program Entry Point ########################################################
###############################################################################
if __name__ == '__main__':
    output_order = sys.argv[1]
    qid_list = []
    with open(output_order, 'r') as fin:
        for line in fin:
            qid_list.append(line)
    global all_texts
    all_texts = load_text()
    #run_conQA()
    #run_depQA()
    #run_baselineQA()
    run_QA(qid_list)

