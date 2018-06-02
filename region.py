from collections import defaultdict
import csv
import sys

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
                

def filter_by_region(file_path, dic):
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
            with open( k + '_USER_ITEM.csv','w') as write_file:
                fieldnames = ['USER','ITEM','QTD']
                csv_writer = csv.DictWriter(write_file,fieldnames=fieldnames,delimiter=',')
                csv_writer.writeheader()    
                for line in regions_list[k]:
                    csv_writer.writerow(line)


def main(file_path_region,file_path_user):
    dic = generate_region_dict(file_path_region)
    filter_by_region(file_path_user, dic)

if __name__ == "__main__":
    main(sys.argv[1],sys.argv[2])

