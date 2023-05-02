import json

import numpy
from tqdm import tqdm
from transformers import pipeline
import scipy


def ranking_svm_loss(scores, should_increase=True):
    """
    Calculate Ranking SVM loss based on Kendall's Tau-a coefficient.
    :param scores: all scores.
    :param should_increase: True means `scores` should be increasing.
    :return: ranking svm loss (how unordered the list is)
    """
    order = 1 if should_increase else -1
    max_possible = len(scores) * (len(scores) - 1) / 2.0
    same_order_count = 0
    same_value_count = 0
    for index1, x1 in enumerate(scores):
        for index2, x2 in enumerate(scores):
            if index1 >= index2:
                continue  # skip considered ones.
            if (x2 - x1) * order > 0:
                same_order_count += 1
            elif x1 == x2:
                same_value_count += 1
    different_order_count = max_possible - same_order_count - same_value_count
    # best_raw_score = min(bigger_count,smaller_count)

    # Since we now force an order as input
    raw_score = same_order_count - different_order_count
    normalized_raw_score = raw_score / max_possible
    score = normalized_raw_score
    return score


classification_pipeline = None


def classifier_scoring_full(topic1, topic2, text):
    """
    Using a classifier, score text based on how close it is to topic 1.
    :param topic1: topic1. the closer the better.
    :param topic2: topic2. the further away the better.
    :param text: text under consideration.
    :return: dict containing:
        score : score from -1 to 1.
        entropy: uncertainty of the classifier from 0 to 1.
    """
    global classification_pipeline
    if classification_pipeline is None:
        classification_pipeline = pipeline("zero-shot-classification")
    if len(text) == 0:
        print("Empty sentence! using score=0.5 entropy=1")
        return {
            "score": 0.5,
            "entropy": 1,
        }
    result = classification_pipeline(text, [topic1, topic2])
    # print(result)
    for idx in range(2):
        if result['labels'][idx] == topic1:
            return {
                "score": result['scores'][idx],
                # "entropy": scipy.stats.entropy(result['scores'])
            }
    raise RuntimeError("Topic is missing from inferring results. Classification model may not be working.")


def sort_single_sets(unsorted_data):
    """
    Sort the unsorted data of 5 sentences and get the topics used.
    :param unsorted_data: unsorted 5-sentence sets.
    :return: topic1, topic2, sorted_sentences
    """
    # First get topics
    topics = []
    for item in unsorted_data:
        for topic in item['topics']:
            if topic not in topics:
                topics.append(topic)
    topics = sorted(topics)

    # Second get weights
    weight_to_sentence = {}
    for item in unsorted_data:
        topic_used = item['topics']  # only take first

        if topics[0] not in topic_used:
            weight_to_sentence[0] = item['out']
        else:
            weight_to_sentence[topic_used[topics[0]]] = item['out']
    # Finally get them into sorted sentences (weight not needed anymore)
    result = []
    for i in sorted(weight_to_sentence.keys()):
        result.append(weight_to_sentence[i])
    return topics[0], topics[1], result


def experiments(data_file):
    report = {
        "data_file": data_file,
        "meta": {},
        "scores": {}
    }
    all_data = json.load(open(data_file, 'r'))
    for single_data in tqdm(all_data):
        prompt = single_data['prompt']
        for single_data_set in single_data['sets']:
            topic1, topic2, sents = sort_single_sets(single_data_set)
            topic_set = "[%s][%s]" % (topic1, topic2)
            confidences = [classifier_scoring_full(topic1, topic2, x)['score'] for x in sents]
            score = ranking_svm_loss(confidences, should_increase=True)
            if topic_set not in report['scores']:
                report['scores'][topic_set] = [score]
            else:
                report['scores'][topic_set].append(score)

        report['meta']['avg'] = {}
        for item in report['scores']:
            average = numpy.mean(report['scores'][item])
            report['meta']['avg'][item] = average
            print("%s: score = %s" % (item, average))

    with open("tau_a_%s" % data_file, 'w') as f:
        json.dump(report, f)
    print(report)


if __name__ == '__main__':
    experiments("cache_gen_nosample_2.txt")
