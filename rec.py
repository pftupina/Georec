from surprise import BaselineOnly
from surprise import Dataset
from surprise import Reader
from surprise import SVD
from surprise import accuracy
from surprise import KNNWithZScore
from collections import defaultdict
from surprise.model_selection import KFold
from surprise.model_selection import train_test_split
from surprise.model_selection import cross_validate
import csv
import sys
import os


def get_algo(algo_id):
	#Define o algoritimo usado com base no segundo parametro da linha de comando
	#KNN com Zscore itembased
	if(algo_id == 2):
		algo = KNNWithZScore(user_based=False);
	#SVD com userbased
	elif(algo_id == 3):
		algo = KNNWithZScore(user_based=True);
	#KNN com Zscore userbased
	else:
		algo = KNNWithZScore(user_based=True);

	return algo

#--------------------------------------------------------------------------------------#

def generate_region_dict(file_path):
	with open(file_path) as csv_base:
		csv_reader = csv.DictReader(csv_base)

		d = defaultdict(list)
		for line in csv_reader:
			d[line['DESCRICAO']].append(line['FID_CLIENTE'])
        
        return d

def search_region_dic(current_user,dic):
    for k in dic:
        for user in dic[k]:
            if(user == current_user):
                return k
    return ''
                

#Cria os arquivos de dataset filtrados por area
def filter_by_area(file_path, dic,area):
	
	#Cria o diretorio aonde os dados filtrados ficam	
	if not os.path.exists(area):
		os.makedirs(area)

	with open(file_path) as csv_base:
		csv_reader = csv.DictReader(csv_base)

		current_user = ''
		region = ''
		regions_list = defaultdict(list)

		for line in csv_reader:
			#Usuario novo
			if current_user != line['USER']:
				current_user = line['USER']
				region = search_region_dic(current_user,dic)
				if(region != ''):
					regions_list[region].append(line)
			#Usuario nao novo mas pertencente a uma regiao
			elif(region!=''):
			    regions_list[region].append(line)


		for k in regions_list:
			with open(area + '/' + k +'_USER_ITEM.csv','w') as write_file:
				fieldnames = ['USER','ITEM','QTD']
				csv_writer = csv.DictWriter(write_file,fieldnames=fieldnames,delimiter=',')
				csv_writer.writeheader()    
				for line in regions_list[k]:
					csv_writer.writerow(line)

#--------------------------------------------------------------------------------------#
def get_top_n(predictions, n=10):

    # First map the predictions to each user.
    top_n = defaultdict(list)
    for uid, iid, true_r, est, _ in predictions:
        top_n[uid].append((iid, est))

    # Then sort the predictions for each user and retrieve the k highest ones.
    for uid, user_ratings in top_n.items():
        user_ratings.sort(key=lambda x: x[1], reverse=True)
        top_n[uid] = user_ratings[:n]

    return top_n

def context_top_n(file_path,context,algo_id):

	#Define o algoritimo
	algo = get_algo(algo_id)

	#Define o padrao de leitura dos arquivos
	reader = Reader(line_format='user item rating', sep=',',skip_lines=1)

	#Cria o dataset baseado nos dados lidos
	data = Dataset.load_from_file(file_path, reader)

	#Cria um conjunto de testes usando todos os dados
	trainset = data.build_full_trainset()

	#treina o algoritimo conforme os dados de treino
	algo.fit(trainset);

	#Pega os dados para usar como conjunto de teste
	testset = trainset.build_anti_testset()


	predictions = algo.test(testset)
	top_n = get_top_n(predictions)

	if not os.path.exists('resultados'):
		os.makedirs('resultados')

	with open("resultados/TOP_N_"+ context + '_' + str(algo_id) + ".csv","w") as result_file:	
		# Printa os itens recomendados para cada usuario
		for uid, user_ratings in top_n.items():
			result_file.write(uid)
			for iid in user_ratings:
				result_file.write("," + iid[0])
			result_file.write('\n')

#--------------------------------------------------------------------------------------#

def context_RMSE(file_path,context,algo_id,k=10):
	
	#Define o algoritimo
	algo = get_algo(algo_id)

	#Define o padrao de leitura dos arquivos
	reader = Reader(line_format='user item rating', sep=',',skip_lines=1)

	#Cria o dataset baseado nos dados lidos
	data = Dataset.load_from_file(file_path, reader)

	# define a cross-validation iterator
	kf = KFold(k)

	if not os.path.exists('resultados'):
		os.makedirs('resultados')

	with open("resultados/RMSE_"+ context + '_' + str(algo_id) + ".csv","w") as result_file:	
		
		result_file.write('RMSEs:\n')
		# Printa os itens recomendados para cada usuario
		for trainset, testset in kf.split(data):

			# treina e testa o algoritimo
			algo.fit(trainset)
			predictions = algo.test(testset)
			result_file.write(str(accuracy.rmse(predictions)) +'\n')


#--------------------------------------------------------------------------------------#


def main(algo_id):

	#Filtra os dados por regiao, e separando-os numa pasta
	dictionary_region  = generate_region_dict("USER_REGIAO.csv")
	filter_by_area("USER_ITEM.csv", dictionary_region, "REGIAO_DADOS")

	#Filtra os dados por municipio, e separando-os numa pasta
	dictionary_region  = generate_region_dict("USER_MUNICIPIO.csv")
	filter_by_area("USER_ITEM.csv", dictionary_region, "MUNICIPIO_DADOS")

	#Filtra os dados por municipio, e separando-os numa pasta
	dictionary_region  = generate_region_dict("USER_BAIRRO.csv")
	filter_by_area("USER_ITEM.csv", dictionary_region, "BAIRRO_DADOS")
 
	#- ---------------------------------- -#

	#Calcula os Top N sem contexto
	context_top_n("USER_ITEM.csv","GERAL",algo_id)

	#Faz varios testes com splits diferentes dos dados para calculo do RMSE
	context_RMSE("USER_ITEM.csv","GERAL",algo_id)

	#''   '''    '''' regional

	for filename in os.listdir('REGIAO_DADOS'):
		context_top_n("REGIAO_DADOS/" + filename,"REGIAO",algo_id)
		context_RMSE("REGIAO_DADOS/" + filename,"REGIAO",algo_id)

	#''   '''    '''' municipal

	for filename in os.listdir('MUNICIPIO_DADOS'):
		context_top_n("MUNICIPIO_DADOS/" + filename,"MUNICIPIO",algo_id)


	#''   '''    '''' por bairro
	for filename in os.listdir('BAIRRO_DADOS'):
		context_top_n("BAIRRO_DADOS/" + filename,"BAIRRO",algo_id)



if __name__ == "__main__":
	main(sys.argv[1])