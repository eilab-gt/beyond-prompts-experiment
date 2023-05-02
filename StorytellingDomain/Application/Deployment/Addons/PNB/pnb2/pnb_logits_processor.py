import transformers
import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel, LogitsProcessorList, GPTJForCausalLM, AutoTokenizer
import sys
from nltk import sent_tokenize

# Set CUDA device to cuda if gpu is available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# srun --constraint=a40 --gpus-per-node=1 -c 6 <this_script>

# if 'slurm' in sys.argv:
#     gedi_location = "gedi_topic/"
# else:
#     gedi_location = "/mnt/hdd/trained_models/gedi_base/gedi_topic/"

default_gedi_location = "gedi_topic/"


def cut_into_sentences(text, do_cleanup=True):
    """
    Cut text into sentences. \n are also regarded as a sentence.
    :param do_cleanup: if True, do cleanups.
    :param text: input text.
    :return: sentences.
    """
    all_sentences = []
    # sentences_raw = text.split("\n")
    sentences_raw = [text.replace("\n", " ")]
    result = []

    for item in sentences_raw:
        sentence_in_item = sent_tokenize(item)
        for item2 in sentence_in_item:
            all_sentences.append(item2)

    if do_cleanup:
        for item in all_sentences:
            item = item.replace('<|endoftext|>', '')
            if len(item) > 2:
                result.append(item)
    else:
        result = all_sentences
    return result


class PlugAndBlendLogitsProcessor(transformers.LogitsProcessor):
    gedi_model = None
    """
    Path to GeDi model files. Should be initialized externally.
    """

    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

    # default omega from original GeDi work, higher disc_weight means more aggressive topic steering.
    # can be overridden when calling generate_one_sentence(), see that function.
    # default value (1x) is 30.
    # PnB uses 30*2 (2x) as default.
    omega = 45

    # A hyperparameter asssociated with the GeDi model.
    logit_scale = 1.312

    def __init__(self, topic: str, weight: float):
        super().__init__()

        if PlugAndBlendLogitsProcessor.gedi_model is None:
            print("WARNING! gedi_model is not initialized externally. Trying to load from default location...")
            PlugAndBlendLogitsProcessor.gedi_model = GPT2LMHeadModel.from_pretrained(default_gedi_location).to(device)

        self.topic = topic
        self.weight = weight
        self.encoded_topic = PlugAndBlendLogitsProcessor.tokenizer.encode(topic)[0]

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        # print("Applying topic: %s, weight: %s" % (self.encoded_topic, self.weight))
        # print("test %s" % scores[:, 100])
        # scores[:, 100] += 1
        # print("after %s" % scores[:, 100])
        modifiers = self.get_gedi_modifiers(input_ids=input_ids)

        # Make them appear on the same device
        modifiers = modifiers.to(scores.device)

        # Dealing with GPT-J (50400 tokens instead of 50257, but all other tokens just extras)
        if scores.shape[-1] >= modifiers.shape[-1]:
            magic_number = -123456789 * 1 if self.weight > 0 else -1  # "-inf"
            expanded_modifier = (torch.ones(scores.size()) * magic_number).to(scores.device)
            # Add `modifier` to this `expanded modifiers` along final axis (where dims are different)
            # So we get an extended modifier tensor with extra elements at last axis with 0.
            expanded_modifier.index_copy_(-1, torch.arange(modifiers.size()[-1]).to(scores.device), modifiers)
            modifiers = expanded_modifier

        # print(scores.shape)

        scores += modifiers * self.weight * PlugAndBlendLogitsProcessor.omega

        return scores

    def get_gedi_modifiers(self, input_ids):

        # Make sure that there are nothing going out of bounds
        if input_ids[input_ids > 50256].any():
            print("WARNING: some input_ids are invalid!")
        input_ids[input_ids > 50256] = 50256

        # Setting up some constants
        code_0 = "false"
        code_1 = "true"
        nt_id = PlugAndBlendLogitsProcessor.tokenizer.encode(code_0)[0]
        pt_id = PlugAndBlendLogitsProcessor.tokenizer.encode(code_1)[0]

        # define class weights for cross entropy loss: give weight 0 to [50256], the padding (eot) token.
        crossentropy_loss_weight = [1] * 50257
        crossentropy_loss_weight[50256] = 0  # do not calculate loss on eos token
        crossentropy_loss_weight = torch.tensor(crossentropy_loss_weight).float().to(device)

        # Creating prefixes.
        seq_pt = (torch.ones(input_ids.shape[0]) * pt_id).type_as(input_ids).view(-1, 1)
        seq_nt = (torch.ones(input_ids.shape[0]) * nt_id).type_as(input_ids).view(-1, 1)
        encoded_topic_torch = (torch.ones(input_ids.shape[0]) * self.encoded_topic).type_as(input_ids).view(-1, 1)

        # Assemble input_ids.
        seq_pt_new = torch.cat((seq_pt, encoded_topic_torch, input_ids), dim=1)[:, :]
        seq_nt_new = torch.cat((seq_nt, encoded_topic_torch, input_ids), dim=1)[:, :]

        def prepare_inputs_for_generation(input_ids, **kwargs):
            return {"input_ids": input_ids.to(device)}

        seq_batched = torch.cat([seq_pt_new, seq_nt_new], dim=0)

        model_inputs = prepare_inputs_for_generation(input_ids=seq_batched)

        gedi_outputs = PlugAndBlendLogitsProcessor.gedi_model(**model_inputs)

        # Let's calculate modifier on the whole sentence:
        # This is modifier on all tokens multiplied.
        # Here, we calculate the baseline (sentence without generated token) modifier, for normalization.

        shift_logits = gedi_outputs["logits"][..., :-1, :].contiguous().to(device)
        shift_labels = seq_batched[..., 1:].contiguous().to(device)

        # By using Cross Entropy on previous tokens,
        # This effectively picked probabilities of previous tokens in the sequence.
        loss_fct = torch.nn.CrossEntropyLoss(reduction="none",
                                             weight=crossentropy_loss_weight,
                                             )

        # Cross entropy loss originally gives -p(x), so...
        logits_r = -1 * loss_fct(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1),
        )
        logits_r = logits_r.view(seq_batched.shape[0], -1)

        seq_len = logits_r.shape[1]

        logits_r = torch.sum(logits_r, 1)

        # Now, finally add the baseline into the actual final (generated token) logits.
        gedi_logits = torch.log_softmax(gedi_outputs["logits"][:, -1, :], -1)
        gedi_logits += logits_r.unsqueeze(1)

        # Normalize modifier logits by sequence length and reshape it for output
        gedi_logits_split = torch.split(gedi_logits / (seq_len + 1),
                                        input_ids.shape[0])

        logits = torch.stack(gedi_logits_split, 2)

        logits = PlugAndBlendLogitsProcessor.logit_scale * logits

        logp_related_softmax = torch.log_softmax(logits, dim=-1)

        # Once normalized, we only care about the "positive" dimension (0).
        final_modifier = logp_related_softmax[..., 0]

        # print(torch.sum(final_modifier[0,:1000]))

        return final_modifier


# Wrapper for the logits processor.
class PNBWorkflow:
    def __init__(self, config=None):
        if config is None:
            config = {}
        print("Transformers version: %s (PnB Tested on 4.16.2~)" % transformers.__version__)
        print("Start loading models with config %s" % config)
        print("(Hint: If failed, check out https://colab.research.google.com/drive/1nuxJ7eGHu3WSGui3WT5cJjxR49R_Lg41?usp=sharing ")
        if 'slurm' in config:
            print("slurm parameter detected! Into deployment mode.")
            self.tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-j-6B")
            self.model = GPTJForCausalLM.from_pretrained("EleutherAI/gpt-j-6B", torch_dtype=torch.float16).to(device)
        else:
            print("Developer mode. Loading smaller model...")
            self.tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
            if 'base_location' in config:
                base_location = config['base_location']
            else:
                base_location = "gpt2"
            print("Loading base model at %s." % base_location)
            self.model = GPT2LMHeadModel.from_pretrained(base_location, pad_token_id=self.tokenizer.eos_token_id).to(
                device)
        if 'gedi_location' in config:
            PlugAndBlendLogitsProcessor.gedi_model = GPT2LMHeadModel.from_pretrained(config['gedi_location']).to(device)
        print("PNB Workflow initialized.")

    def __call__(self, body):

        # Fixing compatibility problems for bad words
        bad_word_ids_raw = [7, 58, 62, 834, 17569, 1427, 29343, 25947, 37405, 2602]  # ",(,[ and different length of _s
        bad_word_ids = [[x] for x in bad_word_ids_raw]

        # default sentence
        sentence = 'Here is a story. Once upon a time,'
        if 'sentence' in body:
            sentence = body['sentence']
        else:
            print("Using default prompt: %s" % sentence)

        if 'topic' in body:
            topic = body['topic']
        else:
            print("Topic not specified! Using dummy topics with 0 weight.")
            topic = {"dummy": 0}

        lp_raw_list = []
        for key, value in topic.items():
            lp_raw_list.append(PlugAndBlendLogitsProcessor(topic=key, weight=value))

        # print("Original: %s" % sentence)
        #
        input_ids = self.tokenizer.encode(sentence, return_tensors='pt').to(device)

        #
        # decode_test_sentence = PlugAndBlendLogitsProcessor.tokenizer.decode(input_ids[0], skip_special_tokens=True)
        #
        # print("Re-decoded: %s" % decode_test_sentence)

        # input_ids = torch.cat([input_ids,input_ids,input_ids],dim=0)

        # lp_list = LogitsProcessorList()
        lp_list = LogitsProcessorList(lp_raw_list)

        output = self.model.generate(
            input_ids,
            max_length=32 + input_ids.shape[-1],
            min_length=8 + input_ids.shape[-1],
            logits_processor=lp_list,
            do_sample=True,
            num_beams=2,
            no_repeat_ngram_size=2,
            repetition_penalty=1.2,
            length_penalty=0.8,
            bad_words_ids=bad_word_ids,
        )
        # print("Output:\n" + 100 * '-')
        out_sentence = self.tokenizer.decode(output[0], skip_special_tokens=True)

        raw_out_sentence = out_sentence

        # print("RAW: %s" % raw_out_sentence)

        length_of_prompt = len(sentence)

        text = raw_out_sentence[length_of_prompt:]
        text = cut_into_sentences(text)
        if len(text) == 0:
            print("Warning! No text generated.")
            out_sentence = ""
        else:
            out_sentence = text[0]

        # Remove blanks. We don't need them in our application.
        out_sentence = out_sentence.lstrip()

        if 'do_not_process' in body:
            # Throw away processed results
            out_sentence = raw_out_sentence

        response = {
            "in_sentence": sentence,
            "topics": topic,
            "out_sentence": out_sentence,
        }

        # print(response)

        return response

        # greedy_output = model.generate(
        #     input_ids,
        #     max_length=50,
        #     logits_processor=lp_list,
        # )
        # print("Output:\n" + 100 * '-')
        # print(tokenizer.decode(greedy_output[0], skip_special_tokens=True))


# Tests


if __name__ == '__main__':
    obj = PNBWorkflow(config={
        "base_location": "/mnt/hdd/trained_models/skill_model/ROC-large_v201",
        "gedi_location": "/mnt/hdd/trained_models/gedi_base/gedi_topic/",
    }
    )

    sentence = "What is science fiction?"
    for item in range(1):
        topic = {"Science": 1}  # {"Science": 1, "Business":1}
        result = obj({"sentence": sentence, "topic": topic})
        print(result)

    # sentence = "In the news today:"
    #
    # topics = ["Science", "Business", "World", "Sports"]
    #
    # for topic in topics:
    #     result = obj({"sentence": sentence, "topic": {topic: 2}})
    #     print(result)
