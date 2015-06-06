
EXEC= hw6.py
OUTFILE= train_my_answers.txt
answerfile7= hw7_answers.answer
answerfile6= train_answers.answer
orderfile = hw8_process_stories.txt

KEY7= hw7_dev.answers
KEY8= hw8_dev.answers

LOG= score_log.txt
buf= temp.txt
run:
	python3 hw6.py ${orderfile}
test:
	perl score-answers.pl ${OUTFILE} ${KEY8} > ${buf}
	python3 log_results.py ${buf} ${LOG}
	tail -15 ${LOG}
	python3 score.py temp.txt
