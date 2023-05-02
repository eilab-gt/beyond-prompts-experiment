"""
carp.py

Main driver files.

Part of the code derived from the CARP project by Castricato et al.
"""

import torch
from torch import nn
import torch.nn.functional as F
import numpy as np
import math
import transformers

import torch
from transformers import PegasusForConditionalGeneration, PegasusTokenizer

from transformers import AutoModel, AutoTokenizer

CARP_MODEL_LOCATION = "/mnt/hdd/datasets/carp/CARP_L.pt"

LATENT_DIM = 2048
USE_CUDA = True
USE_HALF = True
config = transformers.RobertaConfig()

extract_fns = {'EleutherAI/gpt-neo-1.3B':
                   (lambda out: out['hidden_states'][-1]),
               'EleutherAI/gpt-neo-2.7B':
                   (lambda out: out['hidden_states'][-1]),
               'roberta-large':
                   (lambda out: out[0]),
               'roberta-base':
                   (lambda out: out[0]),
               'microsoft/deberta-v2-xlarge':
                   (lambda out: out[0])}

d_models = {'EleutherAI/gpt-neo-1.3B': 2048,
            'EleutherAI/gpt-neo-2.7B': 2560,
            'roberta-large': 1024,
            'roberta-base': 768,
            'microsoft/deberta-v2-xlarge': 1536}

MODEL_PATH = "roberta-large"


class TextEncoder(nn.Module):
    def __init__(self):
        super().__init__()

        self.model = AutoModel.from_pretrained(MODEL_PATH)

        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        self.d_model = d_models[MODEL_PATH]

        # Add cls token to model and tokenizer
        self.tokenizer.add_tokens(['[quote]'])
        self.model.resize_token_embeddings(len(self.tokenizer))

    def tok(self, string_batch):
        return self.tokenizer(string_batch,
                              return_tensors='pt',
                              padding=True).to('cuda')

    def forward(self, x, mask=None, tokenize=False, mask_sum=True):
        if tokenize:
            x = self.tok(x)
            mask = x['attention_mask']
            x = x['input_ids']

        out = self.model(x, mask, output_hidden_states=True, return_dict=True)

        # out is a tuple of (model output, tuple)
        # the second tuple is all layers
        # in this second tuple, last elem is model output
        # we take second last hidden -> third last layer
        # size is always [batch, seq, 1536]

        hidden = out[0]
        # layers = out[-1]
        # hidden = layers[-2]

        # Mask out pad tokens embeddings
        if mask_sum:
            emb_mask = mask.unsqueeze(2).repeat(1, 1, self.d_model)
            hidden = hidden * emb_mask

        y = hidden.sum(1)
        y = F.normalize(y)

        return y  # Sum along sequence


class ContrastiveModel(nn.Module):
    def __init__(self, encA, encB):
        super().__init__()

        self.encA = encA
        self.encB = encB

        self.projA = nn.Linear(self.encA.d_model, LATENT_DIM, bias=False)
        self.projB = nn.Linear(self.encB.d_model, LATENT_DIM, bias=False)

        self.logit_scale = nn.Parameter(torch.ones([]) * np.log(1 / 0.07))
        self.clamp_min = math.log(1 / 100)
        self.clamp_max = math.log(100)

    def clamp(self):
        with torch.no_grad():
            self.logit_scale.clamp(self.clamp_min, self.clamp_max)

    def encodeX(self, x, masks=None):
        x = self.encA(x, masks)
        return self.projA(x)

    def encodeY(self, y, masks=None):
        y = self.encB(y, masks)
        return self.projB(y)

    # Calculate contrastive loss between embedding groups
    # x, y are assumed encoding/embeddings here
    def cLoss(self, x, y):
        n = x.shape[0]
        # normalize
        x = F.normalize(x)
        y = F.normalize(y)

        logits = x @ y.T * self.logit_scale.exp()
        labels = torch.arange(n, device='cuda')

        loss_i = F.cross_entropy(logits, labels)
        loss_t = F.cross_entropy(logits.T, labels)
        acc_i = (torch.argmax(logits, dim=1) == labels).sum()
        acc_t = (torch.argmax(logits, dim=0) == labels).sum()

        return (loss_i + loss_t) / 2, (acc_i + acc_t) / n / 2

    def getLogits(self, x, y):
        x = self.encodeX(*x)
        y = self.encodeY(*y)

        x = F.normalize(x)
        y = F.normalize(y)

        logits = x @ y.T * self.logit_scale.exp()
        return logits

    def forward(self, x, y):
        return self.getLogits(x, y)


N_CTX = 512


class CARPWorkflow():
    def __init__(self, config=None):
        self.config = config

        self.model = ContrastiveModel(TextEncoder(), TextEncoder())

        try:
            self.carp_path = config["carp_model_path"]
        except:
            print("Can't find carp_model_path in config, using default path.")
            self.carp_path = CARP_MODEL_LOCATION
        try:
            self.model.load_state_dict(torch.load(self.carp_path))
        except Exception as e:
            print(f"Exception: {str(e)}")
            print("You may need to download the CARP model at  https://the-eye.eu/public/AI/models/CARP/CARP_L.pt ")
        if USE_HALF: self.model.half()
        if USE_CUDA: self.model.cuda()

        # Paraphrases using peagasus. Used for softening.
        model_name = 'tuner007/pegasus_paraphrase'
        self.torch_device = 'cuda'
        self.tokenizer_pegasus = PegasusTokenizer.from_pretrained(model_name)
        self.model_pegasus = PegasusForConditionalGeneration.from_pretrained(model_name).half().to(self.torch_device)

    def tok(self, string_batch):
        for i, _ in enumerate(string_batch):
            if len(string_batch[i]) > N_CTX:
                string_batch[i] = string_batch[i][-N_CTX:]

        return self.model.encA.tok(string_batch)

    def get_batch_tokens(self, dataset, inds):
        batch = [dataset[ind] for ind in inds]
        pass_batch = [pair[0] for pair in batch]
        rev_batch = [pair[1] for pair in batch]

        pass_tokens = self.tok(pass_batch)
        rev_tokens = self.tok(rev_batch)
        pass_masks = pass_tokens['attention_mask']
        rev_masks = rev_tokens['attention_mask']
        pass_tokens = pass_tokens['input_ids']
        rev_tokens = rev_tokens['input_ids']

        return pass_tokens, pass_masks, rev_tokens, rev_masks

    def get_response(self, input_text, num_return_sequences, num_beams):
        batch = self.tokenizer_pegasus([input_text], truncation=True, padding='longest', max_length=60,
                                       return_tensors="pt").to(self.torch_device)
        translated = self.model_pegasus.generate(**batch, max_length=60, num_beams=num_beams,
                                                 num_return_sequences=num_return_sequences, temperature=1.5)
        tgt_text = self.tokenizer_pegasus.batch_decode(translated, skip_special_tokens=True)
        return tgt_text

    # Compute the logits of the passage against the reviews
    def get_passrev_logits(self, passages, reviews):
        pass_tokens = self.tok(passages)
        rev_tokens = self.tok(reviews)
        pass_masks = pass_tokens['attention_mask']
        rev_masks = rev_tokens['attention_mask']
        pass_tokens = pass_tokens['input_ids']
        rev_tokens = rev_tokens['input_ids']

        with torch.no_grad():
            logits = self.model.getLogits([pass_tokens, pass_masks],
                                          [rev_tokens, rev_masks]).type(dtype=torch.float32)
        return logits

    def report_logits(self, logits):
        logits /= 2.7441
        print((logits[0]).cpu().tolist())
        conf = logits.softmax(1)

        for i, row in enumerate(conf):
            for j, col in enumerate(row):
                print(str(i) + "-" + str(j) + ": " + str(round(col.item(), 2)))

    def compute_softened_logits(self, passages, reviews1, reviews2, pairs=True):
        logits1 = torch.sum(self.get_passrev_logits(passages, reviews1), dim=-1).unsqueeze(0) / float(len(reviews1))
        if pairs:
            logits2 = torch.sum(self.get_passrev_logits(passages, reviews2), dim=-1).unsqueeze(0) / float(len(reviews2))

            return torch.cat([logits1, logits2], dim=-1)
        else:
            return logits1

    # Lots of options to play with here that dictate how the paraphrases are generated.
    # Future work is needed
    def compute_logit(self, passages, reviews, soften=True,
                      top_k=False, k=3,
                      ret=False, pairs=True):
        # Softens the classifiers by using paraphrasing.
        if soften:
            if pairs:
                review1_paraphrases = list(
                    set(self.get_response(reviews[0], num_return_sequences=3, num_beams=3) + [reviews[0]]))
                review2_paraphrases = list(
                    set(self.get_response(reviews[1], num_return_sequences=3, num_beams=3) + [reviews[1]]))
                print(review1_paraphrases)
                print(review2_paraphrases)

                review1_contextual = list(map(lambda x: "[quote] " + x, review1_paraphrases))
                review2_contextual = list(map(lambda x: "[quote] " + x, review2_paraphrases))

                softened_logits = self.compute_softened_logits(passages, review1_contextual + review1_paraphrases,
                                                               review2_contextual + review2_paraphrases)
                # self.report_logits(softened_logits)
                if ret: return softened_logits
            else:
                review_paraphrases = list(
                    set(self.get_response(reviews, num_return_sequences=3, num_beams=3) + [reviews]))
                # print(review_paraphrases)

                review_contextual = list(map(lambda x: "[quote] " + x, review_paraphrases))
                softened_logits = self.compute_softened_logits(passages, review_contextual + review_paraphrases, None,
                                                               pairs=False)

                # softened_logits = (softened_logits/2.7441)
                # print(softened_logits.squeeze().cpu().tolist())

                if ret: return softened_logits

    def __call__(self, stories, reviews, version=1):
        if version == 1:
            return self.call_v1(stories, reviews)
        elif version == 2:
            return self.call_v2(stories, reviews)

    def call_v1(self, stories, reviews):
        """
        v1 api, that gives the best matched sentence from a specific review in the list.
        :param stories: lines in the stories.
        :param reviews: reviews to match.
        :return: dict, key is each item in `reviews`, value is the best match in `stories`.
        """
        if type(stories) is str:
            stories = [[x] for x in stories.split(".")]
        if type(stories) is not list:
            raise AttributeError(
                "Stories have to be either a string or a list of cut sentences, not %s." % str(type(stories)))

        if type(reviews) is str:
            reviews = [reviews]
        if type(stories) is not list:
            raise AttributeError(
                "Reviews have to be either a string or a list of cut sentences, not %s." % str(type(stories)))

        all_results = {}

        for review in reviews:
            best_score = -1000000
            best_item = None
            for item in stories:
                score = self.compute_logit(item, review, pairs=False, ret=True)
                # print("Sentence: %s, score=%s" % (item, score))
                if score > best_score:
                    best_score = score
                    best_item = item

            # print("By saying [%s], you want to apply it to %s. Right?" % (review, best_item))
            all_results[review] = best_item
        return all_results

    def call_v2(self, stories, reviews):
        """
        v2 api, that returns all sentences above a threshold.
        :param stories: lines in the stories.
        :param reviews: dict, key is reviews, value is threshold.
        :return: dict of dict, key is each item in `reviews`,
        value is a dict with key the sentence and value the score for the match.

        """
        if type(stories) is str:
            stories = [x for x in stories.split(".")]
        if type(stories) is not list:
            raise AttributeError(
                "Stories have to be either a string or a list of cut sentences, not %s." % str(type(stories)))

        if type(reviews) is not dict:
            raise AttributeError("v2 api: Reviews has to be a dict, not %s." % str(type(stories)))

        all_results = {}

        for review in reviews:  # key
            this_result = {}
            for item in stories:
                score = self.compute_logit(item, review, pairs=False, ret=True)
                score = (score / self.model.logit_scale.exp()).item()
                print("Sentence: %s, score=%s" % (item, score))
                if score > reviews[review]:  # value
                    this_result[item] = score

            # print("By saying [%s], you want to apply it to %s. Right?" % (review, best_item))
            all_results[review] = this_result
        return all_results


#
#
#
# print(stories)


if __name__ == '__main__':
    raw_story = "I woke up in the morning. It was really cold outside. I went to the beach and had a great day!"
    # review = "This story should be in afternoon."
    review = {"This story should be in afternoon.": 0}
    c = CARPWorkflow()
    result = c(raw_story, review, version=2)
    print(result)
