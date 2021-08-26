#vyhledani aspektu a jejich hodnoceni pomoci vetne stavby
#Author: Simon Matyas (xmatya11), Rohan Goel
#https://medium.com/analytics-vidhya/aspect-based-sentiment-analysis-a-practical-approach-8f51029bbc4a
import sys
import os
from ufal.udpipe import Model, Pipeline, ProcessingError 

dirname = os.path.dirname(os.path.realpath(__file__))
model = Model.load(dirname+"/../models/czech-pdt-ud-2.5-191206.udpipe")
error = ProcessingError()

with open(dirname+'/../models/stop_words_czech.txt',encoding='utf8') as f:
    content = f.read()
    
def AspectAnalyse(text):

    #Zpracovani vstupnich dat
    pipeline = Pipeline(model,'tokenize', Pipeline.DEFAULT, Pipeline.DEFAULT, 'conllu')
    processed = pipeline.process(text, error)

    stop_words = content.split('\n')
    fcluster = []
    totalfeatureList=[]
    dic={}
    finalcluster = []

    for sentence in processed.split('# sent_id'):#Rozdeleni textu na vety
        sentence="# sent_id"+sentence
        newList=[]
        for i in sentence.split('\n'):
            if(not i.startswith('#')):
                lineParts=i.split('\t')
                if(len(lineParts)>3):
                    if(lineParts[2] not in stop_words):#odstraneni stopslov z vety
                        newList.append(lineParts[2])

        test=' '.join(newList)
        #zpracovani nove vety bez stopslov
        pipeline = Pipeline(model,'tokenize', Pipeline.DEFAULT, Pipeline.DEFAULT, 'conllu')
        sentence = pipeline.process(test, error)
        newList=[]

        for x in sentence.split('\n'):
            lineParts=x.split('\t')
            if(len(lineParts)>7):
                newList.append([lineParts[1],lineParts[6],lineParts[7]])#vytvoreni dvojic slov ktere na sobe zavisi se zkratkou popisujici jejich vztah

        for x in range(0,len(newList)):
            wordTarget=sentence.split('\n')

            if(newList[x][2]!='root'):
                try:
                    newList[x][1]=wordTarget[4+int(newList[x][1])-1].split('\t')[1]
                except:
                    continue
        featureList=[]

        categories=[]
        for x in sentence.split('\n'):
            if(not x.startswith('#')):
                lineParts=x.split('\t')
                if(len(lineParts)>1):#tvorba seznamu vlastností   
                    if(lineParts[3]=='NOUN' or lineParts[3]=='ADJ'):

                        featureList.append([lineParts[2],lineParts[3]])
                        totalfeatureList.append([lineParts[2],lineParts[3]])
                        categories.append(lineParts[2])


        for i in featureList:
            filist = []
            for j in newList:#vyber dvojic obsahujici aspekt a hodnoceni podle zkratky vztahu
                if((j[0]==i[0] or j[1]==i[0]) and (j[2] in ["nsubj", "acl:relcl", "obj", "advmod", "amod", "neg", "xcomp", "compound","orphan","acl","conj","appos"])):
                    if(j[0]==i[0]):
                        filist.append(j[1])
                    else:
                        filist.append(j[0])
            fcluster.append([i[0],filist])

    for i in totalfeatureList:
        dic[i[0]] = i[1]

    for i in fcluster:
        if(dic[i[0]]=="NOUN"):#vyhledani aspektu v seznamu vlastnosti
            finalcluster.append(i)
            

    return(finalcluster)


