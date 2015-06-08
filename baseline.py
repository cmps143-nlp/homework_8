#!/usr/bin/env python
'''
Created on May 14, 2014

@author: reid
'''

from nltk.corpus import wordnet as wn
from nltk.stem.wordnet import WordNetLemmatizer as wnl
import sys, nltk, operator, re
import chunk
import collections


def select(sent, word, n):
    ans = []
    i = 0
    for w in sent:
        if w[0].lower() == word:
            i += 1
        if i > 0:
            ans.append(w[0])
            i += 1
        if i >= n:
            break
    return ans

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
    sentences = [[w.lower() for w in sent] for sent in sentences]
    sentences = [nltk.pos_tag(sent) for sent in sentences]
    return sentences

def get_bow(tagged_tokens, stopwords):
	return set([t[0].lower() for t in tagged_tokens if t[0].lower() not in stopwords])

def find_phrase(tagged_tokens, qbow):
    for i in range(len(tagged_tokens) - 1, 0, -1):
        word = (tagged_tokens[i])[0]
        if word in qbow:
            return tagged_tokens[i+1:]

def overlap_score(qbow, sent, stopwords, key_word):
    # A list of all the word tokens in the sentence
    sbow = get_bow(sent, stopwords)
    # Count the # of overlapping words between the Q and the A
    # & is the set intersection operator
    overlap = len(qbow & sbow)
    if key_word:
        if key_word in  sbow:
            overlap += 2
    return overlap

# qtokens: is a list of pos tagged question tokens with SW removed
# sentences: is a list of pos tagged story sentences
# stopwords is a set of stopwords
def baseline(qbow, sentences, stopwords, key_word=None):
    # Collect all the candidate answers
    answers = []
    for sent,i in zip(sentences,range(len(sentences))):
        if key_word:
            v, p = lemmatize(key_word, 'v')
            lmtzed_sent = [lemmatize(w, t) for w, t in sent]
            lmtzed_overlap = overlap_score(qbow, lmtzed_sent, stopwords, v)
            answers.append(( lmtzed_overlap, lmtzed_sent, i ))
        overlap = overlap_score(qbow, sent, stopwords, key_word)
        answers.append((overlap, sent, i))

    # Sort the results by the first element of the tuple (i.e., the count)
    # Sort answers from smallest to largest by default, so reverse it
    answers = sorted(answers, key=operator.itemgetter(0), reverse=True)
	# Return the best answer
    best_answer = (answers[0])[1]
    return best_answer, answers[0][2]

def find_most_common(text, pos1, pos2, n, stopwords):
	stopwords.add('.')
	stopwords.add(',')
	stopwords.add('!')
	tagged_sents = get_sentences(text)
	filtered_words = [w for sent in tagged_sents for w in sent
		if not w[0] in stopwords
		if (pos1 == w[1]) or (pos2 == w[1])]
	d = collections.defaultdict(int)
	for w in filtered_words:
		d[w[0]] += 1
	common = sorted([(n,w) for (w,n) in d.items()], reverse=True)
	common = [w for (c,w) in common]
	return " ".join(common[:n])



################################################################################
#		Nic's Stuff
################################################################################


# word, pos -> (lemmatized word, pos)
def lemmatize(w,p):
    if p.startswith("N"):
        return (wnl.lemmatize(wnl,w,'n'),p)
    elif p.startswith("V"):
        return (wnl.lemmatize(wnl,w,'v'),p)
    else:
        return (w,p)


# qtokens: is a list of pos tagged question tokens with SW removed
# sentences: is a list of pos tagged story sentences
# stopwords is a set of stopwords
def baseline2(qbow, sentences, stopwords):


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

# given a word, use wordnet to return list of similar words
def getSyns(word):
    return list(set([s.name().split('.')[0] for s in wn.synsets(word)])) 

# given a part of speech, return all the words in a list of (word,POS) tuples
# that have the same POS as the one given
def getAllWordsWithPos(sentence, pos):
    return [w for w,p in sentence if pos == p]

# takes the baseline sentence, and returns the determiners and nouns
def baselineNouns(qbow, sentences, stopwords):
    bl = baseline2(qbow, sentences, stopwords)
    # list(set(...)) removes duplicates
    return list(set(
    	[(w,p) for (w,p) in bl
    	if p.startswith('D') or p.startswith('N')]
    		))

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
        locSentences = chunk.find_sentences(words, baselineSent)
        locations = chunk.find_candidates(locSentences, chunk.chunker)
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
    answer = baseline2(qbow, sentences, stopwords)
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

        answer = baseline2(lemmaQBOW, sentences, stopwords)
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
        #print(loc)
        if loc != []:
            return loc
        elif answerNouns != []:
            return answerNouns
    elif qword == "why":
        pass
    elif qword == "how":
        pass
    return answer

if __name__ == '__main__':
	text_file = "fables-01.sch"

	stopwords = set(nltk.corpus.stopwords.words("english"))
	text = read_file(text_file)
	question = "Where was the crow sitting?"

	qsent  = get_sentences(question)[0]
	print('get_sents: ', get_sentences(question))
	qbow = get_bow(qsent, stopwords)

	sentences = get_sentences(text)
	answer,i = baseline(qbow, sentences, stopwords)
	#print('answer: ' , answer)
	print(" ".join(t[0] for t in answer))

