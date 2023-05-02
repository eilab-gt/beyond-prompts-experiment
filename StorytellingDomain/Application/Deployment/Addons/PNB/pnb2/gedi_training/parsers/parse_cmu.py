"""
parse_cmu.py

Parse the CMU Movie Summary dataset.

"""
from tqdm import tqdm

metadata_path = "../data/movie.metadata.tsv"
plot_path = "../data/plot_summaries.txt"

parsed_path = "../data/%s.txt"

import csv, json

# Genres that have more than 3000 appearances.
genres_raw = ['Thriller', 'Science Fiction', 'Horror', 'Adventure', 'Action', 'Mystery', 'Drama', 'Crime Fiction',
              'Short Film',
              'Silent film', 'Indie', 'Black-and-white', 'Comedy', 'Family Film', 'World cinema', 'Musical',
              'Action/Adventure',
              'Romantic drama', 'Romance Film', 'Animation', 'Comedy film', 'Documentary']

genres_to_consider = ['Thriller', 'Science', 'Horror', 'Adventure', 'Action', 'Mystery', 'Crime',
                      'Family', 'World', 'Musical',
                      'Romance', 'Fantasy', 'War']


def get_all_genres_from_cmu(large_cat_threshold=3000, print_debug=False):
    """
    Analyze what genres (and whether they are common along many entries).
    :param print_debug: if True print debug information (big genres).
    :param large_cat_threshold: ignore genres if it has less member than this number.
    :return: dict, key is original id, name and count
    """
    all_genres = {}
    movie_to_genres = {}
    with open(metadata_path) as metadata_file:
        meta_tsv = csv.reader(metadata_file, delimiter="\t")
        for row in meta_tsv:
            genre_json = json.loads(row[-1])
            for item in genre_json:
                if item not in all_genres:
                    all_genres[item] = {"name": genre_json[item], "count": 1}
                else:
                    all_genres[item]["count"] += 1

    large_count = 0
    large_names = []
    if print_debug:
        for item in all_genres:
            if all_genres[item]['count'] >= large_cat_threshold:
                print("ID: %s Name: %s Count: %s" % (item, all_genres[item]['name'], all_genres[item]['count']))
                large_count += 1
                large_names.append(all_genres[item]['name'])
        print("Count: %s (%s large)" % (len(all_genres), large_count))

        # ['Thriller', 'Science Fiction', 'Horror', 'Adventure', 'Action', 'Mystery', 'Drama', 'Crime Fiction', 'Short Film', 'Silent film', 'Indie', 'Black-and-white', 'Comedy', 'Family Film', 'World cinema', 'Musical', 'Action/Adventure', 'Romantic drama', 'Romance Film', 'Animation', 'Comedy film', 'Documentary']
        print(large_names)
    return all_genres


def get_movie_id_with_genre():
    """
    Get a list of movie id with their raw genre information.
    :return:
    """
    result = {}
    with open(metadata_path) as metadata_file:
        meta_tsv = csv.reader(metadata_file, delimiter="\t")
        for row in meta_tsv:
            genre_json = json.loads(row[-1])
            id = row[0]
            result[id] = genre_json
    return result


def parse_cmu(save_file_name=None):
    """
    Parse CMU Movie dataset into intermediate format.
    :param save_file_name:
    :return:
    """
    all_genres = get_all_genres_from_cmu()
    id_to_genre = get_movie_id_with_genre()

    result = []

    considered_genres_counter = {}
    for item in genres_to_consider:
        considered_genres_counter[item] = 0

    with open(plot_path) as plot_file:
        plot_tsv = csv.reader(plot_file, delimiter="\t")
        for row in tqdm(plot_tsv):
            if len(row) != 2:
                print("Parsing error? %s" % row)
                continue
            id = row[0]
            plot_text = row[1]
            try:
                genre_of_this_movie = id_to_genre[id]
            except KeyError as e:
                print("Movie id %s not exist in metadata!" % id)
                continue

            for item in genre_of_this_movie:
                for considering in genres_to_consider:
                    if considering in genre_of_this_movie[item]:
                        # big enough
                        result.append([considering, plot_text])
                        considered_genres_counter[considering] += 1

        print("finished, %s entries." % len(result))
        print(considered_genres_counter)

        all_result = {
            "meta":
                {
                    'total': considered_genres_counter,
                }
            ,
            "payload": result,

        }

        if save_file_name is not None:
            full_path = parsed_path % save_file_name
            with open(full_path, 'w') as parsed_file:
                json.dump(all_result, parsed_file)

        return result


if __name__ == '__main__':
    # get_all_genres_from_cmu(1500,print_debug=True)
    parse_cmu("parsed_1500_handpicked")
