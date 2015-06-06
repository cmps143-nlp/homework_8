
import os

def pars(filename):
    lines = open(filename, 'r')

    formated_content = []
    for line in lines:
        if 'QuestionID:' in line or 'Answer:' in line :
            formated_content.append(line)
    lines.close()
    return formated_content        

if __name__ == '__main__':
    print('hi')
    content = pars('hw7_dev.answers')
    with open('hw7_answers.answer', 'w') as fout: 
        i = 0
        while i < len(content):
            fout.write(content[i])
            fout.write(content[i+1])
            fout.write('\n')
            i += 2
