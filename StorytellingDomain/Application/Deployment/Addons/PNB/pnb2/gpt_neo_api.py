"""
gpt_neo_api.py

playground to test neuro gpt neo apis.
"""

import npu
import torch
from transformers import GPTNeoForCausalLM, AutoConfig
from transformers import GPTNeoModel, GPTNeoForCausalLM, \
    GPT2Tokenizer, GPTNeoConfig
import torch

NPU_API_KEY = "" # Insert your API key here

def test_api():
    tokenizer = GPT2Tokenizer.from_pretrained("EleutherAI/gpt-neo-2.7B")
    npu.api(NPU_API_KEY, deployed=True)
    model_id = '60ca2a1e54f6ecb69867c72c'

    untokenized = input("Sentence?")
    tokens = tokenizer.encode_plus(untokenized, return_tensors="pt")

    kwargs = {
        'response_length': 100,  # how many response tokens to generate
        'remove_input': False,  # whether to return your input
        'num_beams': 4,
        'repetition_penalty': 1.2,
        'no_repeat_ngram_size': 4,
        'early_stopping': True,
        # 'bad_words_ids': skippable_tokens,
        'min_length': len(untokenized) + 30,
        'top_p': 0.9,
        'temperature': 0.8,
        # all params from the transformers' library `generate` function are supported
    }

    gptj_output = npu.predict(model_id, [untokenized], kwargs)
    print(gptj_output)


if __name__ == '__main__':
    test_api()
