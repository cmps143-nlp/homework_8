
import sys
import hw6
import baseline as bl

num = 0

class Q(object):
    def __init__(self, qid=None, recall=None, pres=None, F=None, output=None):
        self.qid = qid
        self.recall = recall
        self.pres = pres
        self.F = F
        self.output= None

def read_qout(f):
    line = f.readline()
    #print(line)
    output = []
    while (not 'SCORING' in line and
        not 'FINAL RESULTS' in line):
        line = f.readline()
        #print(line)
        #print('while 1', line)
        #input('>')

    while (not 'F-measure' in line and
        not 'FINAL RESULTS' in line):
        #print('while 2' ,line)
        #input('>')
        if 'SCORING ' in line:
            qid = line[len('SCORING '):]
            l = f.readline()
            l = f.readline()
            while len(l) > 1:
                #print('len: ', len(l))
                #print('while 3', l)
                #input('.')
                output.append(l)
                l = f.readline()
        if 'Recall ' in line:
            recall = line[line.find('=') + 1: ]
            recall = recall.split()
            if 'N/A' in recall[0]:
                recall = 0
            else:
                recall = float(recall[0])
        if 'Precision = ' in line:
            precision = line[len('Precision = '): ]
            pres = precision.split()
            if 'N/A' in pres[0]:
                pres = 0
            else:
                pres = float(pres[0])
        line = f.readline()

    if 'F-measure = ' in line:
        F = line[len('F-measure = '): ]
        if 'N/A' in F:
            F = 0
        else:
            F = float(F)
        return Q(qid, recall, pres, F, ' '.join(output))
    #print(len(line))
    if (len(line) < 2):
        return None

def out(q):
    qid = ''
    f = ''
    if q.qid:
        qid = q.qid
    if q.F:
        f = q.F
    print(qid.strip(), f)


q_list = []

def average(s_list):
    #print(s_list)
    global num
    pt = 0
    rt = 0
    ft = 0
    for s in s_list:
        #print(s)
        #print(type(s))
        num += 1
        rt += s[0]
        pt += s[1]
        ft += s[2]
    l = len(s_list)
    ra = rt / l
    pa = pt / l
    fa = ft / l
    return round(ra, 2), round(pa,2), round(fa, 2)


if __name__ == '__main__':
    scorefile = sys.argv[1]
    score_list = []
    with open(scorefile) as fin:
        q = read_qout(fin)
        #out(q)

        while q:
            score_list.append(q)
            q = read_qout(fin)
            #print('while 4')

    #for q in q_list:
        #out(q)

    questions = hw6.load_questions()

    measure = {}
    #print(len(score_list))
    for qscore in score_list:
        qindex = hw6.find_q(questions, qscore.qid.strip())
        q = questions[qindex]
        qsent  = bl.get_sentences(q.question)[0]

        first_word = qsent[0][0]
        #second_word = qsent[1][0]

        if not first_word in measure.keys():
            measure[first_word] = []
        #if not second_word in measure.keys():
        #       measure[first_word][second_word] = []

        s = (qscore.recall, qscore.pres, qscore.F)
        #print(s)
        #print(first_word, s)
        measure[first_word].append(s)

    #print(len(questions))
    #print(len(measure))
    print('Word1\tWord2\trec\t pres\tf-score\tnum')
    count = 0
    tot = 0
    for w1 in measure:

        count = len(measure[w1])
        w1r, w1p, w1f = average(measure[w1])
        #print()
        tot += count
        print(w1 +'\t\t'+str(w1r)+'\t'+str(w1p)+'\t'+str(w1f)+'\t'+str(count))
        #for w2 in measure[w1]:
        #   w2r, w2p, w2f = average(measure[w1][w2])
        #print()

    #print(tot)




