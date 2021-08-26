Struktura adresáře
- models		- adresář obsahující modely pro skripty
- result		- ukázky výsledků
- Scripts		- adresář obsahující skripty
- sent10		- adresář obsahující virtuální prostředí
- readme.txt	- tento soubor
- training 		- adresář obsahující datovou sadu a skript pro trenování modelu
- doc 			- text a zdrojové kódy textové části práce
- plakat.pdf 	- plakát popisující práci
- xmatya11-Metavyhledavani-recenzi.pdf 	- textová část práce

Spuštění virtualniho prostředí z kořenového adresáře pamětového media pomocí knihovny virtualenv na operačním systému Linux
server minerva3 skupiny KNoT má k dispozici všechny potřebné knihovny ke spuštění virtuálního prostředí pomocí následujícího příkazu.

source sent10/bin/activate

Argumenty spuštění skriptu z kořenového adresáře pamětového media

python Scripts/findReviewArticles.py [reviewProduct] [startDate] [endDate] [parProc]

reviewProduct - hledaný produkt pro který budou vyhledány recenze
startDate - počáteční datum hledaných recenzí formát YYYY-MM-DD
endDate - konečné datum hledaných recenzí formát YYYY-MM-DD
parProc - počet na kolika procesech se ma skript spustit pro zpracování více souborů najednou

Průběh skriptu je ukazován na chybovém výstupu. Ukazuje informace o počtu již zpracovaných souborů, kolik souborů ještě zbývá pracovat, délka zpracování a předpokládaný čas do dokončení práce.
Zpracování jednoho dne trvá průměrně 30 sekund.

Adresáře

	Models
		best_model_state.bin - model pro určení sentimentu
		DeepPavlov_bert-base-bg-cs-pl-ru-cased - model pro tokenizer použitý pro určení sentimentu 
		czech-morfflex-pdt-161115.tagger - model pro nástroj morphoDita
		czech-pdt-ud-2.5-191206.udpipe - model pro nástroj udpipe
		negative_words_czech.txt - slovník negativních slov
		positive_words_czech.txt - slovník pozitivních slov
		stop_words_czech.txt - slovník stopslov
		manualReviews.txt - datová sada vytvořena manualnim vyhledáváním recenzí

	Scripts
		brandFinder.py - ve wikidatech vyhledá alternativní názvy pro zadaný produkt a výrobce zadaného produktu
		findReviewArticles.py - hlavní skript, vyhledá články mezi dvěma daty obsahující recenze zadaného produktu 
		morphoditaTagger.py - doplnění textu o slovní druhy a základní tvary slov pro přesnější vyhledávání recenzí
		productFinder.py - potvrzení že vyhledaná recenze se zabývá hledaným produktem
		SentimentAnalyzerAspect.py - analýza jestli je vyhledaná recenze pozitivní nebo negativní
		udpipeParse.py - určení aspektů a jejich hodnocení v textu
		config.txt - konfigurační soubor
	result
		example.txt - vysledek příkladu použití v readme.txt
		auto 2021-01-01 2021-04-19.txt - výsledky spuštění s argumenty v nazvu souboru
		film 2021-01-01 2021-04-19.txt
		kniha 2021-01-01 2021-04-19.txt
		sluchatka 2021-01-01 2021-04-19.txt
		telefon 2021-01-01 2021-04-19.txt

Příklad spuštění

Nejprve spustit virtualní prostředí příkazem:

	source sent10/bin/activate

poté spustit samotný skript příkazem:

	python Scripts/findReviewArticles.py telefon 2021-3-10 2021-3-20 4

s těmito argumenty vyhledá recenze telefonů mezi daty 10.3.2021 a 20.3.2021
výsledek tohoto příkladu je v ./result/example.txt

Výstup:
výstup na stdout je ve formátu:
	
	[Název produktu] - [Sentiment] - url na článek

skript vyhledá všechny články které se i nejméně podobají na recenzi daného produktu a seřadí je podle relevance. Články jsou seřazeny sestupně, tak že na posledním řádku je článek nejvíce se podobající recenzi.

Nastavení konfiguračního souboru

Konfigurační soubor je tvořen Python slovníkem při úpravě souboru je tedy potřeba dodržet přesný formát

	Formát konfiguračního souboru

	{
		"dataSource":"/mnt/data-2/feeds_crawling/big_brother/workplace/3-vert/cs_media/",
		"specialProduct":{
			"Název Produktu":[
				{"portal":"Název portálu","productName":"""kód pro vyhledání názvu produktu v HTML pomocí nástroje BeautifulSoup"""}
			]
		}
	}

	kód pro vyhledání názvu je potřeba vložit do trojitých uvozovek a vyhledaný název nahrát do proměnné ArticleProduct
	v kódu je možné použít proměnnou page_soup obsahujici html zpracované nástrojem BeautifulSoup