import pickle, nltk
from nltk.corpus import wordnet as wn


if __name__ == "__main__":

    ## You can use either the .csv files or the .dict files.
    ## If you use the .dict files, you MUST use "rb"!

    # noun_ids = load_wordnet_ids("Wordnet_nouns.csv")
    # verb_ids = load_wordnet_ids("Wordnet_verbs.csv")


    # {synset_id : {synset_offset: X, noun/verb: Y, stories: set(Z)}}, ...}
    # e.g. {help.v.01: {synset_offset: 2547586, noun: aid, stories: set(Z)}}, ...
    noun_ids = pickle.load(open("Wordnet_nouns.dict", "rb"))
    verb_ids = pickle.load(open("Wordnet_verbs.dict", "rb"))

    # iterate through dictionary
    for synset_id, items in noun_ids.items():
        noun = items['story_noun']
        stories = items['stories']
        # get lemmas, hyponyms, hypernyms

    for synset_id, items in verb_ids.items():
        verb = items['story_verb']
        stories = items['stories']
        # get lemmas, hyponyms, hypernyms


    # 'Rodent' is a hypernym of 'mouse',
    # so we look at hyponyms of 'rodent' to find 'mouse'
    #
    # Question: Where did the rodent run into?
    # Answer: the face of the lion
    # Sch: The lion awaked because a mouse ran into the face of the lion.
    rodent_synsets = wn.synsets("rodent")
    print("'Rodent' synsets: %s" % rodent_synsets)
    # > [Synset('rodent.n.01')]

    print("'Rodent' hyponyms")
    for rodent_synset in rodent_synsets:
        rodent_hypo = rodent_synset.hyponyms()
        print("%s: %s" % (rodent_synset, rodent_hypo))
        # > Synset('rodent.n.01'): [Synset('water_rat.n.03'), Synset('murine.n.01'), Synset('marmot.n.01'), Synset('mara.n.02'),
        # Synset('wood_rat.n.01'), Synset('gerbil.n.01'), Synset('new_world_mouse.n.01'), Synset('beaver.n.07'),
        # Synset('capybara.n.01'), Synset('chinchilla.n.03'), Synset('lemming.n.01'), Synset('abrocome.n.01'),
        # Synset('porcupine.n.01'), Synset('agouti.n.01'), Synset('mountain_beaver.n.01'),
        # Synset('round-tailed_muskrat.n.01'), Synset('viscacha.n.01'), Synset('muskrat.n.02'), Synset('prairie_dog.n.01'),
        # Synset('mole_rat.n.01'), Synset('cavy.n.01'), Synset('mountain_chinchilla.n.01'), Synset('mountain_paca.n.01'),
        # Synset('hamster.n.01'), Synset('dormouse.n.01'), Synset('squirrel.n.01'), Synset('jumping_mouse.n.01'),
        # Synset('cotton_rat.n.01'), Synset('jerboa.n.01'), Synset('mole_rat.n.02'), Synset('rat.n.01'), Synset('paca.n.01'),
        # Synset('sand_rat.n.01'), Synset('mouse.n.01'), Synset('coypu.n.01')]

        for hypo in rodent_hypo:
            print(hypo.name()[0:hypo.name().index(".")])
            print("is hypo_synset in Wordnet_nouns/verbs.dict?")
            # match on "mouse.n.01"


    # 'Know' is a hyponym of 'recognize' (know.v.09),
    # so we look at hypernyms of 'know' to find 'recognize'
    #
    # Question: What did the mouse know?
    # Answer: the voice of the lion
    # Sch: The mouse recognized the voice of the lion.
    know_synsets = wn.synsets("know")
    print("\n'Know' synsets: %s" % know_synsets)
    # > [Synset('know.n.01'), Synset('know.v.01'), Synset('know.v.02'), Synset('know.v.03'),
    # Synset('know.v.04'), Synset('know.v.05'), Synset('acknowledge.v.06'), Synset('know.v.07'),
    # Synset('sleep_together.v.01'), Synset('know.v.09'), Synset('know.v.10'), Synset('know.v.11')]

    print("'Know' hypernyms")
    for know_synset in know_synsets:
        know_hyper = know_synset.hypernyms()
        print("%s: %s" % (know_synset, know_hyper))
        # > Synset('know.n.01'): [Synset('knowing.n.01')]
        # > Synset('know.v.01'): []
        # > Synset('know.v.02'): []
        # > Synset('know.v.03'): []
        # > Synset('know.v.04'): []
        # > Synset('know.v.05'): [Synset('experience.v.01')]
        # > Synset('know.v.06'): [Synset('accept.v.01')]
        # > Synset('know.v.07'): []
        # > Synset('sleep_together.v.01'): [Synset('copulate.v.01')]
        # > Synset('know.v.09'): [Synset('recognize.v.02')]
        # > Synset('know.v.10'): [Synset('distinguish.v.01')]
        # > Synset('know.v.11'): [Synset('remember.v.01')]


    # 'Express mirth' is a lemma of 'laugh'
    # so we look at lemmas of 'express mirth' to find 'laugh'
    #
    # Question: Who expressed mirth?
    # Answer: the lion
    # Sch: The lion laughed aloud because he thought that the mouse is extremely not able to help him.
    mirth_synsets = wn.synsets("express_mirth")
    print("\n'Express Mirth' synsets: %s" % mirth_synsets)
    # > [Synset('laugh.v.01')]

    print("'Express mirth' lemmas")
    for mirth_synset in mirth_synsets:
        print(mirth_synset)
        # > Synset('laugh.v.01')

        # look up in dictionary
        print("\n'%s' is in our dictionary: %s" % (mirth_synset.name(), (mirth_synset.name() in verb_ids)))
        # > laugh.v.01 is in our dictionary: True


