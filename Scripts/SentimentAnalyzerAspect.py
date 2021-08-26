#skript pro analyzu sentimentu aspektovou analyzou a pomoci strojoveho uceni.
#Author: Simon Matyas (xmatya11)
import requests
import justext
import udpipeParse
import transformers
from transformers import BertModel, BertTokenizer, AdamW, get_linear_schedule_with_warmup
import torch
import os
from torch import nn

class SentimentClassifier(nn.Module):
  def __init__(self, n_classes):
    super(SentimentClassifier, self).__init__()
    self.bert = BertModel.from_pretrained(PRE_TRAINED_MODEL_NAME)
    self.drop = nn.Dropout(p=0.3)
    self.out = nn.Linear(self.bert.config.hidden_size, n_classes)
  def forward(self, input_ids, attention_mask):
    _, pooled_output = self.bert(
      input_ids=input_ids,
      attention_mask=attention_mask,
      return_dict=False
    )
    output = self.drop(pooled_output)
    return self.out(output)

dirname = os.path.dirname(os.path.realpath(__file__))
PRE_TRAINED_MODEL_NAME=dirname+'/../models/DeepPavlov_bert-base-bg-cs-pl-ru-cased'
tokenizer = transformers.BertTokenizer.from_pretrained(PRE_TRAINED_MODEL_NAME, return_dict=False)
device = torch.device("cpu")
class_names = ['neg','pos']
model = SentimentClassifier(len(class_names))
model.load_state_dict(torch.load(dirname+'/../models/best_model_state.bin'))
model = model.to(device)



with open(dirname+'/../models/negative_words_czech.txt',encoding='utf8') as f:
    content = f.read()
    negative_words = content.split('\n')
with open(dirname+'/../models/positive_words_czech.txt',encoding='utf8') as f:
    content = f.read()
    positive_words = content.split('\n')
#urceni sentimentu pomoci strojoveho uceni
def Sentiment_from_Articletext(ArticleText):
	cnt = 0
	result = 0
	MAX_LEN = 200
	for y in ArticleText: #rozdeleni clanku na odstavce
		if (not y.is_boilerplate): 
			if(len(y.text)>30 or y.is_heading): #oddeleni nadpisu
				review_text=y.text
				encoded_review = tokenizer.encode_plus( 
					review_text,
					max_length=MAX_LEN,
					add_special_tokens=True,
					return_token_type_ids=False,
					padding='max_length',
					return_attention_mask=True,
					return_tensors='pt',
				)
				cnt+=1

				input_ids = encoded_review['input_ids'].to(device)
				attention_mask = encoded_review['attention_mask'].to(device)
				output = model(input_ids, attention_mask)
				_, prediction = torch.max(output, dim=1)
				if(prediction>0):
					result+=1
	#vypocet prumeru ze vsech odstavcu webu
	if(cnt>0):
		if((result/cnt)>0.5):
		    return('pos')
		else:
		    return('neg')
	else:
		return('??')

#ze zadaneho URL vyhodnoti sentiment
def Sentiment_from_url(url):
	try:
		response = requests.get(url)#stazeni stranky ze zadaneho url
	except:
		return '??'
	#vyhledani relevantniho textu
	f = justext.justext(response.content.decode(errors='ignore'), justext.get_stoplist("Czech"))

	cnt = 0
	result = 0
	poscnt=0				
	negcnt=0

	for y in f:
		if (not y.is_boilerplate):
			if(len(y.text)>30 or y.is_heading):
				cnt+=1
				AspectList=udpipeParse.AspectAnalyse(y.text)#vyhledani aspektu a jejich hodnoceni v textu
				for x in AspectList:#urceni sentimentu na zaklade hodnoceni aspektu
					if(len(x[1])>0):
						if(len(set(x[1]) & set (negative_words))):
							result-=1
						if(len(set(x[1]) & set (positive_words))):
							result+=1
	if(cnt>0):
		if(result==0):
			return Sentiment_from_Articletext(f)#urceni sentimentu na pomoci strojoveho uceni
		else:

			if((result/cnt)>0):
			    return('pos')
			else:
			    return('neg')

	else:
		return('??')