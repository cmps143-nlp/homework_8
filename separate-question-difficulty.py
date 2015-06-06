#!/usr/bin/env python

import zipfile, argparse, os, sys
from collections import defaultdict

###############################################################################
## Utility Functions ##########################################################
###############################################################################

# This method takes as input the file extension of the set of files you want to open
# and processes the data accordingly
# Assumption: this python program is in the same directory as the training files
def getData(filename):
    dataset_dict = defaultdict()
    getQA(open(filename, 'rU'), dataset_dict)
    return dataset_dict

# returns a dictionary where the question numbers are the key
# and its items are another dict of difficulty, question, type, and answer
# e.g. story_dict = {'fables-01-1': {'Difficulty': x, 'Question': y, 'Type':}, 'fables-01-2': {...}, ...}
def getQA(content, dataset_dict):
    qid = ""
    for line in content:
        if "QuestionID: " in line:
            qid = line[len("QuestionID: "):len(line)-1]
            dataset_dict[qid] = defaultdict()
        elif "Question: " in line: dataset_dict[qid]['Question'] = line[len("Question:")+1:len(line)-1]
        elif "Answer: " in line: dataset_dict[qid]['Answer'] = line[len("Answer:")+1:len(line)-1]
        elif "Difficulty: " in line: dataset_dict[qid]['Difficulty'] = line[len("Difficulty:")+1:len(line)-1]
        elif "Type: " in line: dataset_dict[qid]['Type'] = line[len("Type:")+1:len(line)-1]
    return dataset_dict

def write_answer_files(dataset_dict, filename):
    if len(dataset_dict) <= 0:
        return
    file = open(filename, "w")

    keylist = sorted(dataset_dict.keys())
    for key in keylist:
        value = dataset_dict[key]
        file.write('QuestionID: ' + key + '\n')
        for inkey, invalue in value.items():
            file.write(inkey + ': ' + invalue + '\n')
        file.write('\n')
    file.close()

def write_solution_files(dataset_dict, filename):
    if len(dataset_dict) <= 0:
        return
    file = open(filename, "w")

    keylist = sorted(dataset_dict.keys())
    for key in keylist:
        value = dataset_dict[key]
        file.write('QuestionID: ' + key + '\n')
        file.write('Question: ' + value['Question'] + '\n')
        file.write('Answer: ' + value['Answer']+ '\n')
        file.write('Difficulty: ' + value['Difficulty']+ '\n')
        file.write('Type: ' + value['Type']+ '\n')
        file.write('\n')
    file.close()



###############################################################################
## Program Entry Point ########################################################
###############################################################################
if __name__ == '__main__':
    standard_answers_name = sys.argv[2]
    student_answers_name = sys.argv[1]

    standard_answers = getData(standard_answers_name)
    student_answers = getData(student_answers_name)
    
    easy_questions = defaultdict()
    medium_questions = defaultdict()
    hard_questions = defaultdict()

    easy_solutions = defaultdict()
    medium_solutions = defaultdict()
    hard_solutions = defaultdict()

    for key, value in standard_answers.items():
        if value['Difficulty'][0] == 'E' or value['Difficulty'][0] == 'e':
            if key in student_answers.keys(): easy_questions[key] = student_answers[key]
            easy_solutions[key] = standard_answers[key]
        elif value['Difficulty'][0] == 'M' or value['Difficulty'][0] == 'm':
            if key in student_answers.keys(): medium_questions[key] = student_answers[key]
            medium_solutions[key] = standard_answers[key]
        elif value['Difficulty'][0] == 'H' or value['Difficulty'][0] == 'h':
            if key in student_answers.keys(): hard_questions[key] = student_answers[key]
            hard_solutions[key] = standard_answers[key]

    write_answer_files(easy_questions, "student_easy.answers")
    write_answer_files(medium_questions, "student_med.answers")
    write_answer_files(hard_questions, "student_hard.answers")

    write_solution_files(easy_solutions, "dev_easy.answers")
    write_solution_files(medium_solutions, "dev_med.answers")
    write_solution_files(hard_solutions, "dev_hard.answers")