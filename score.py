

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
    output = []
    while (not 'SCORING' in line and
        not 'FINAL RESULTS' in line):
        line = f.readline()
    while (not 'F-measure' in line and
        not 'FINAL RESULTS' in line):
        if 'SCORING ' in line:
            qid = line[len('SCORING '):]
            l = f.readline()
            l = f.readline()
            while len(l) > 1:
                output.append(l)
                l = f.readline()
        if 'Recall ' in line:
            recall = line[line.find('=') + 1: ]
            recall = recall.split()
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
    global num
    pt = 0
    rt = 0
    ft = 0
    for s in s_list:
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
    # read scores from file
    score_list = []
    with open(scorefile) as fin:
        q = read_qout(fin)
        while q:
            score_list.append(q)
            q = read_qout(fin)
    questions = hw6.load_questions()
    # calculate averages
    measure = {}
    first_difficulty = {}
    for qscore in score_list:
        # get question object by qid
        qindex = hw6.find_q(questions, qscore.qid.strip())
        qobj = questions[qindex]
        
        # average by first word of question 
        qsent  = bl.get_sentences(qobj.question)[0]
        first_word = qsent[0][0]
        if not first_word in measure.keys():
            measure[first_word] = []
        qobj.score = (qscore.recall, qscore.pres, qscore.F)
        measure[first_word].append(qobj.score)

    # average by first word and difficulty
    for q in questions:
        # average by first word of question 
        qsent  = bl.get_sentences(q.question)[0]
        first_word = qsent[0][0]
        if not first_word in first_difficulty.keys():
            first_difficulty[first_word] = {}
        d = q.difficulty.strip().rstrip()
        if not d in first_difficulty[first_word].keys():
            first_difficulty[first_word][d] = []
        first_difficulty[first_word][d].append(q.score)

    # average by difficulty
    for qobj in questions:
        d = qobj.difficulty.strip().rstrip()
        if not d in measure.keys():
            measure[d] = []
        measure[d].append(qobj.score)




    difficulties = ['Easy', 'Medium', 'Hard']
    # output results
    print('Word1\t\trec\t pres\tf-score\tnum')
    count = 0
    tot = 0
    diffcount = 0
    for w1 in measure:
        if w1 in difficulties:
            continue    
        count = len(measure[w1])
        w1r, w1p, w1f = average(measure[w1])
        tot += count
        # dont output difficulties same time as first words
        print(w1 +'\t\t'+str(w1r)+'\t'+str(w1p)+'\t'+str(w1f)+'\t'+str(count))
        for diff in first_difficulty[w1].keys():
            dwr, dwp, dwf = average(first_difficulty[w1][diff])
            print('\t'+diff +'\t'+str(dwr)+'\t'+str(dwp)+'\t'+str(dwf)+'\t'+str(len(first_difficulty[w1][diff])))

    # difficulty
    print("Average by Difficulties")
    for diff in difficulties:
        if diff in measure.keys():
            r, p, f = average(measure[diff])
            print(diff +'\t\t'+str(r)+'\t'+str(p)+'\t'+str(f)+'\t'+str(len(measure[diff])))





