
import nltk



def last_word(sentence):
    words = nltk.word_tokenize(sentence)
    if len(words) > 0:
        return words[len(words) -1]
    return None

def first_word(sentence):
    if len(words) > 0:
        return words[0]
    return None

def get_sice(word, start, length):
    return word[start: start+length]

def overlap(a, b, n):
    if not b:
        return False
    '''if 'fear' in a:
        print('w1: ', a)
    if 'fear' in b:
        print('w2:', b)'''
    start = 0
    while start+n < len(a)+1:
        piece = a[start: start+n]
        if piece == 'ing' :
            start+= 1
            continue
        if b.find(piece) >= 0:
            return True
        start += 1
    return False

def first(sent, pos, start=0):
    ''' finds first occurance of pos in sentence.
        sent is a taged sentence. '''
    i = start
    while i < len(sent) :
        if pos in sent[i][1]:
            return sent[i][0], i
        i +=1
    return None, None
