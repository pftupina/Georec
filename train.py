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


def main(file_path):

	# As we're loading a custom dataset, we need to define a reader. In the
	# movielens-100k dataset, each line has the following format:
	# 'user item rating timestamp', separated by '\t' characters.
	reader = Reader(line_format='user item rating', sep=',',skip_lines=1)

	data = Dataset.load_from_file(file_path, reader=reader)

	trainset = data.build_full_trainset()
	algo = KNNWithZScore(user_based=False);
	algo.fit(trainset)


	testset = trainset.build_anti_testset()
	predictions = algo.test(testset)

	top_n = get_top_n(predictions)

	# Print the recommended items for each user
	for uid, user_ratings in top_n.items():
	    print uid + "," + str([iid for (iid, _) in user_ratings])

if __name__ == "__main__":
	main(sys.argv[1])