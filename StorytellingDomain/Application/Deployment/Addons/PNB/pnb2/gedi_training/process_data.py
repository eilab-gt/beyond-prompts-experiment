"""
Process_data.py

Adapted from https://github.com/salesforce/GeDi/blob/master/proc_data.py

"""

import numpy as np
import csv
import random
import json


def create_binarized_dataset_from_json(input_filename, out_train, out_test):
    """
    Create dataset for modifier training from a json file specified by the parsers.
    :param input_filename: input json.
    :param out_train: where to save training set.
    :param out_test: where to save testing set.
    :return:
    """
    all_data = json.load(open(input_filename, 'r'))
    topics = list(all_data['meta']['total'].keys())

    payload = all_data['payload']
    entry_count = len(payload)

    split_location = int(entry_count * 0.9)

    train = payload[:split_location]
    test = payload[split_location:]

    true_test = []
    false_test = []

    true_train = []
    false_train = []

    range_arr = list(range(0, len(topics)))

    for i in range(0, len(test)):
        line = test[i]
        label = topics.index(line[0])
        text = line[1]

        if not (len(line) == 2):
            print("skipping " + str(i))
            continue

        choice_array = range_arr[:label] + range_arr[label + 1:]
        ps_label = random.choice(choice_array)

        true_ex = topics[label] + text
        false_ex = topics[ps_label] + text
        true_test.append(true_ex)
        false_test.append(false_ex)

    for i in range(0, len(train)):
        line = train[i]
        label = topics.index(line[0])
        text = line[1]

        if not (len(line) == 2):
            print("skipping " + str(i))
            continue

        choice_array = range_arr[:label] + range_arr[label + 1:]
        ps_label = random.choice(choice_array)

        true_ex = topics[label] + text
        false_ex = topics[ps_label] + text
        true_train.append(true_ex)
        false_train.append(false_ex)

    random.shuffle(true_train)
    random.shuffle(false_train)
    random.shuffle(true_test)
    random.shuffle(false_test)

    false_lines = []
    true_lines = []
    for i in range(0, len(false_test)):
        false_lines.append(false_test[i] + "\t0" + "\n")
    for i in range(0, len(false_test)):
        true_lines.append(true_test[i] + "\t1" + "\n")

    test_lines = false_lines + true_lines
    random.shuffle(test_lines)

    false_lines = []
    true_lines = []
    for i in range(0, len(false_train)):
        false_lines.append(false_train[i] + "\t0" + "\n")
    for i in range(0, len(true_train)):
        true_lines.append(true_train[i] + "\t1" + "\n")

    train_lines = false_lines + true_lines
    random.shuffle(train_lines)

    train_split_all = "\n" + "".join(train_lines)
    test_split_all = "\n" + "".join(test_lines)

    fid = open(out_train, 'w')
    fid.write(train_split_all)
    fid.close()

    fid = open(out_test, 'w')
    fid.write(test_split_all)
    fid.close()

    print("Done")


# region old


def proc_and_binarize(dir):
    if dir == "test":
        train = []
        for i in range(5):
            train.append("%s\t[A%s]\t[B%s]" % (i % 2 + 1, i, i))
        test = train
        topics = ["world", "sports", "business", "science"]
    else:
        fid = open(dir + "/train.tsv")
        train = fid.read()
        train = train.split("\n")[:-1]

        fid = open(dir + "/dev.tsv")
        test = fid.read()
        test = test.split("\n")[:-1]
        topics = ["world", "sports", "business", "science"]

    true_test = []
    false_test = []

    true_train = []
    false_train = []

    range_arr = list(range(0, len(topics)))

    for i in range(0, len(test)):
        line = test[i].split('\t')
        label = line[0]

        if not (len(line) == 3):
            print("skipping " + str(i))
            continue

        if label[0] == "\"":
            label = label[1:-1]
        label = int(label) - 1
        text = line[2]
        if text[0] == "\"":
            text = text[1:-1]
        if text[0] == " ":
            text = text[1:]

        choice_array = range_arr[:label] + range_arr[label + 1:]
        ps_label = random.choice(choice_array)

        true_ex = topics[label] + text
        false_ex = topics[ps_label] + text
        true_test.append(true_ex)
        false_test.append(false_ex)

    for i in range(0, len(train)):
        line = train[i].split('\t')

        if not (len(line) == 3):
            print("skipping " + str(i))
            continue

        label = line[0]
        if label[0] == "\"":
            label = label[1:-1]
        label = int(label) - 1
        text = line[2]
        if text[0] == "\"":
            text = text[1:-1]

        if text[0] == " ":
            text = text[1:]

        choice_array = range_arr[:label] + range_arr[label + 1:]
        ps_label = random.choice(choice_array)

        true_ex = topics[label] + text
        false_ex = topics[ps_label] + text
        true_train.append(true_ex)
        false_train.append(false_ex)

    return true_train, false_train, true_test, false_test


def main():
    fid = open("data/AG-news/train.csv")

    text_train = fid.read()

    fid = open("data/AG-news/test.csv")
    text_test = fid.read()
    fid.close()

    csv.writer(open("data/AG-news/train.tsv", 'w+'), delimiter='\t').writerows(
        csv.reader(open("data/AG-news/train.csv")))
    csv.writer(open("data/AG-news/dev.tsv", 'w+'), delimiter='\t').writerows(csv.reader(open("data/AG-news/test.csv")))

    true_train, false_train, true_test, false_test = proc_and_binarize("data/AG-news")
    random.shuffle(true_train)
    random.shuffle(false_train)
    random.shuffle(true_test)
    random.shuffle(false_test)

    false_lines = []
    true_lines = []
    for i in range(0, len(false_test)):
        false_lines.append(false_test[i] + "\t0" + "\n")
    for i in range(0, len(false_test)):
        true_lines.append(true_test[i] + "\t1" + "\n")

    test_lines = false_lines + true_lines
    random.shuffle(test_lines)

    false_lines = []
    true_lines = []
    for i in range(0, len(false_train)):
        false_lines.append(false_train[i] + "\t0" + "\n")
    for i in range(0, len(true_train)):
        true_lines.append(true_train[i] + "\t1" + "\n")

    train_lines = false_lines + true_lines
    random.shuffle(train_lines)

    train_split_all = "\n" + "".join(train_lines)
    test_split_all = "\n" + "".join(test_lines)

    fid = open("data/AG-news/train.tsv", 'w')
    fid.write(train_split_all)
    fid.close()

    fid = open("data/AG-news/dev.tsv", 'w')
    fid.write(test_split_all)
    fid.close()


# endregion


if __name__ == '__main__':
    # main()

    create_binarized_dataset_from_json(
        "data/parsed_1500_handpicked.txt",
        "data/cmumovie/train.tsv",
        "data/cmumovie/dev.tsv",
    )
