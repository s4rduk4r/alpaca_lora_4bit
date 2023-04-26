from colorama import init, Style, Fore, Back
import time
import torch
from autograd_4bit import (
    load_llm, LLMGPTQv2LoaderArguments, EModelType
)

import config
config.WORK_MODE = config.EWorkModes.INFERENCE

from config.arg_parser import get_config

# ! Suppress warnings from safetensors
import warnings
warnings.filterwarnings(action="ignore", category=UserWarning, message="TypedStorage is deprecated")

# Color output
init(autoreset=True)

# ! Config
config = get_config()

config_path = config.llama_q4_config_dir
model_path = config.llama_q4_model
groupsize = config.groupsize

# * Show loaded parameters
print(f"{config}\n")

# Load Basic Model
model_args = LLMGPTQv2LoaderArguments(
    EModelType.LLaMA,
    config.llama_q4_config_dir,
    config.llama_q4_model,
    config.groupsize,
    2048,
    config.device_map,
    config.max_memory if config.offloading else None,
    config.lora_apply_dir
)
model, tokenizer = load_llm(model_args)


print(Fore.LIGHTYELLOW_EX + 'Apply AMP Wrapper ...')
from amp_wrapper import AMPWrapper
wrapper = AMPWrapper(model)
wrapper.apply_generate()


prompt = '''Slavik: Define favorable outcome, CABAL.
CABAL: '''
batch = tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
batch = {k: v.cuda() for k, v in batch.items()}

start = time.time()
with torch.no_grad():
    generated = model.generate(inputs=batch["input_ids"],
                               do_sample=True, use_cache=True,
                               repetition_penalty=1.1,
                               max_new_tokens=20,
                               temperature=0.9,
                               top_p=0.95,
                               top_k=40,
                               return_dict_in_generate=True,
                               output_attentions=False,
                               output_hidden_states=False,
                               output_scores=False)
result_text = tokenizer.decode(generated['sequences'].cpu().tolist()[0])
end = time.time()
print(result_text)
print(Fore.LIGHTGREEN_EX + f"Inference time: {end - start:.2f}s")
