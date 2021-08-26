#doplneni textu o slovni druhy a zakladni tvary slov pro presnejsi vyhledavani recenzi.
#Author:Simon Matyas (xmatya11)
import sys
import os
from ufal.morphodita import *

dirname = os.path.dirname(os.path.realpath(__file__))
#nacteni modelu
tagger = Tagger.load(dirname+'/../models/czech-morfflex-pdt-161115.tagger')

#prida slovni druhy a zakladni tvary slov zadanemu textu  
def tagText(text):

  forms = Forms()
  lemmas = TaggedLemmas()
  tokens = TokenRanges()
  tokenizer = tagger.newTokenizer()
  if tokenizer is None:
    sys.stderr.write("Wrong model")
    sys.exit(1)
  tokenizer=tokenizer.newVerticalTokenizer()
  tokenizer.setText(text)
  t = 0
  returnString=''
  while tokenizer.nextSentence(forms, tokens):
    tagger.tag(forms, lemmas)

    for i in range(len(lemmas)):
      lemma = lemmas[i]
      token = tokens[i]

      returnString+=str(text[token.start : token.start + token.length]+'\t'+lemma.tag+'\t'+lemma.lemma+'\n')

      t = token.start + token.length
    return str(returnString)