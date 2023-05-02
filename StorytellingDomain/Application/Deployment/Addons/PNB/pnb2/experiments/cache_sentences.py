"""
cache_sentences.py

Based the on the prompts, generate sentences with different weights and topics.

These sentences generated are for further experiments.

"""

import json

from pnb_logits_processor import PNBWorkflow
from tqdm import tqdm

# From ROCStories, eval split, 30 first sentences.
prompts = ['Tom had a very short temper.', 'Luke was playing hockey at school.',
           "Ben's Boy Scout Troop worked for weeks on a float.",
           "The people gathered to protest the court's ruling last week.", "Chad's dog would always jump on people.",
           'Nicole wanted to go to a concert in another city.',
           'James had always wanted to try out for a sport at his school.',
           'Marc always had perfect attendance at school.', 'When Shawn was growing up he collected beanie babies.',
           'The children laughed as it started raining on them.', 'Allen thought he was a very talented poet.',
           'Teddy was looking for a new car.', 'Bill is driving to work.', 'Yesterday, I went shopping for shoes.',
           'Jessica wanted something cold and sweet to eat.', 'Joshua traveled to State College to visit the campus.',
           'There was a bug on the wall by the bed.', "Billy wasn't able to ride the big roller coaster last year.",
           'I used to smoke a pack of cigarettes a day.', 'Marnie was getting married.',
           'In 2014, Marcy adopted a poodle.', 'Sammy was tired of working, but she soldiered on.',
           'The boys were pumped.', 'Tim is an avid coffee drinker.', 'Hank bought a new dog.',
           'Susan was very excited to take a dolphin cruise while in Florida.', 'Lisa wants to start a new business.',
           "My sister in law's granddaughter lives in Maine.", 'There was a war in the kingdom.',
           'Angelique decided to throw a baby shower for expected baby girl.']

default_topic_list = ["Business", "Science", "Sports", "World"]


def all_weights(topic1, topic2, base_omega):
    result = [{topic1: base_omega}]
    for w1 in [0.25, 0.5, 0.75]:
        w2 = 1 - w1
        result.append({topic1: w1 * base_omega, topic2: w2 * base_omega})
    result.append({topic2: base_omega})
    return result


def cache_sentences(generator, filename, base_omega=1):
    def gen(prompt, topic):
        result = obj({"sentence": prompt, "topics": topic})['out_sentence']
        return result

    all_results = []

    idx1 = -1
    for item in prompts:
        this_result = {
            "prompt": item,
            "sets": [],
            "base_omega": base_omega,
        }
        idx1 += 1
        print("Working on prompt %s:%s." % (idx1, item))
        for topic1 in default_topic_list:
            for topic2 in default_topic_list:
                if topic1 > topic2:
                    this_set = []
                    all_weights_list = all_weights(topic1, topic2, base_omega)
                    for weight in all_weights_list:
                        out_sentence = obj({"sentence": item, "topic": weight})['out_sentence']
                        this_set.append(
                            {
                                "topics": weight,
                                "out": out_sentence
                            }
                        )
                        print("%s = %s" % (weight, out_sentence))
                    this_result['sets'].append(this_set)
        all_results.append(this_result)
        with open(filename, 'w') as f:
            json.dump(all_results, f)


if __name__ == '__main__':
    obj = PNBWorkflow(config={
        # "slurm" : True,
        "base_location": "/mnt/hdd/trained_models/skill_model/ROC-large_v201",
        "gedi_location": "/mnt/hdd/trained_models/gedi_base/gedi_topic/",
    }
    )
    cache_sentences(obj, 'cache_gen_nosample_2.txt', 2)
