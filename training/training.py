#skript pro vytrenovani modelu pro urceni sentimentu
#Author: Venelin Valkov, Šimon Matyáš
#https://curiousily.com/posts/sentiment-analysis-with-bert-and-hugging-face-using-pytorch-and-python/
import transformers
from transformers import BertModel, BertTokenizer, AdamW, get_linear_schedule_with_warmup
import torch
import numpy as np
import pandas as pd
import seaborn as sns
from pylab import rcParams
import matplotlib.pyplot as plt
from matplotlib import rc
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
from collections import defaultdict
from textwrap import wrap
from torch import nn, optim
from torch.utils.data import Dataset, DataLoader
import nltk
class GPReviewDataset(Dataset):
	def __init__(self, reviews, targets, tokenizer, max_len):
		self.reviews = reviews
		self.targets = targets
		self.tokenizer = tokenizer
		self.max_len = max_len
	def __len__(self):
		return len(self.reviews)
	def __getitem__(self, item):
		
		review = str(self.reviews.iloc[item])
		target = self.targets.iloc[item]
		encoding = self.tokenizer.encode_plus(
			review,
			add_special_tokens=True,
			max_length=self.max_len,
			return_token_type_ids=False,
			padding='max_length',
			truncation=True,
			return_attention_mask=True,
			return_tensors='pt',
		)
		return {
			'review_text': review,
			'input_ids': encoding['input_ids'].flatten(),
			'attention_mask': encoding['attention_mask'].flatten(),
			'targets': torch.tensor(target, dtype=torch.long)
		}


def create_data_loader(df, tokenizer, max_len, batch_size):

	ds = GPReviewDataset(
		reviews=df.text,
		targets=df.sentiment,
		tokenizer=tokenizer,
		max_len=max_len
	)
	return DataLoader(
		ds,
		batch_size=batch_size,
		num_workers=4
	)
	

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


def train_epoch(
	model,
	data_loader,
	loss_fn,
	optimizer,
	device,
	scheduler,
	n_examples
):
	model = model.train() 
	losses = []
	correct_predictions = 0
	for d in data_loader:
		input_ids = d["input_ids"].to(device)
		attention_mask = d["attention_mask"].to(device)
		targets = d["targets"].to(device)
		outputs = model(
			input_ids=input_ids,
			attention_mask=attention_mask
		)
		_, preds = torch.max(outputs, dim=1)
		loss = loss_fn(outputs, targets)
		correct_predictions += torch.sum(preds == targets)
		losses.append(loss.item())
		loss.backward()
		nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
		optimizer.step()
		scheduler.step()
		optimizer.zero_grad()

	return correct_predictions.double() / n_examples, np.mean(losses)

def eval_model(model, data_loader, loss_fn, device, n_examples):
	model = model.eval()
	losses = []
	correct_predictions = 0
	with torch.no_grad():
		for d in data_loader:
			input_ids = d["input_ids"].to(device)
			attention_mask = d["attention_mask"].to(device)
			targets = d["targets"].to(device)
			outputs = model(
			  input_ids=input_ids,
			  attention_mask=attention_mask
			)
			_, preds = torch.max(outputs, dim=1)
			loss = loss_fn(outputs, targets)
			correct_predictions += torch.sum(preds == targets)
			losses.append(loss.item())
	return correct_predictions.double() / n_examples, np.mean(losses)

def get_predictions(model, data_loader):
	model = model.eval()
	review_texts = []
	predictions = []
	prediction_probs = []
	real_values = []
	with torch.no_grad():
		for d in data_loader:
			texts = d["review_text"]
			input_ids = d["input_ids"].to(device)
			attention_mask = d["attention_mask"].to(device)
			targets = d["targets"].to(device)
			outputs = model(
				input_ids=input_ids,
				attention_mask=attention_mask
			)
			_, preds = torch.max(outputs, dim=1)
			review_texts.extend(texts)
			predictions.extend(preds)
			prediction_probs.extend(outputs)
			real_values.extend(targets)
	predictions = torch.stack(predictions).cpu()
	prediction_probs = torch.stack(prediction_probs).cpu()
	real_values = torch.stack(real_values).cpu()
	return review_texts, predictions, prediction_probs, real_values




if __name__ == '__main__':
	PRE_TRAINED_MODEL_NAME=r'/mnt/minerva1/nlp/projects/sentiment10/models/DeepPavlov_bert-base-bg-cs-pl-ru-cased'
	tokenizer = transformers.BertTokenizer.from_pretrained(PRE_TRAINED_MODEL_NAME, return_dict=False)

	RANDOM_SEED = 69
	np.random.seed(RANDOM_SEED)
	torch.manual_seed(RANDOM_SEED)
	device = torch.device("cpu")
	class_names = ['neg','pos']


	MAX_LEN = 200
	df = pd.read_csv("trainingReviews.csv")
	
	df_train, df_test = train_test_split(
		df,
		test_size=0.1,
		random_state=RANDOM_SEED
	)
	df_val, df_test = train_test_split(
		df_test,
		test_size=0.5,
		random_state=RANDOM_SEED
	)
	
	BATCH_SIZE = 8
	train_data_loader = create_data_loader(df_train, tokenizer, MAX_LEN, BATCH_SIZE)
	val_data_loader = create_data_loader(df_val, tokenizer, MAX_LEN, BATCH_SIZE)
	test_data_loader = create_data_loader(df_test, tokenizer, MAX_LEN, BATCH_SIZE)

	bert_model = BertModel.from_pretrained(PRE_TRAINED_MODEL_NAME)
	
	model = SentimentClassifier(len(class_names))
	model = model.to(device)
	EPOCHS = 10
	optimizer = AdamW(model.parameters(), lr=2e-5, correct_bias=False)
	total_steps = len(train_data_loader) * EPOCHS
	scheduler = get_linear_schedule_with_warmup(
		optimizer,
		num_warmup_steps=0,
		num_training_steps=total_steps
	)
	loss_fn = nn.CrossEntropyLoss().to(device)
	
	history = defaultdict(list)
	best_accuracy = 0
	for epoch in range(EPOCHS):
		print(f'Epoch {epoch + 1}/{EPOCHS}')
		print('-' * 10)
		train_acc, train_loss = train_epoch(
			model,
			train_data_loader,
			loss_fn,
			optimizer,
			device,
			scheduler,
			len(df_train)
		)
		print(f'Train loss {train_loss} accuracy {train_acc}')
		val_acc, val_loss = eval_model(
			model,
			val_data_loader,
			loss_fn,
			device,
			len(df_val)
		)
		print(f'Val   loss {val_loss} accuracy {val_acc}')
		print()
		history['train_acc'].append(train_acc)
		history['train_loss'].append(train_loss)
		history['val_acc'].append(val_acc)
		history['val_loss'].append(val_loss)
		if val_acc > best_accuracy:
			torch.save(model.state_dict(), 'best_model_state.bin')
			best_accuracy = val_acc