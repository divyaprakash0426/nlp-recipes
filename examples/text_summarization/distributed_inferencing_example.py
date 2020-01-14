import os
import tempfile
import torch
import torch.distributed as dist
import torch.nn as nn
import torch.optim as optim
import torch.multiprocessing as mp

from torch.nn.parallel import DistributedDataParallel as DDP
import time
from torch.multiprocessing import Manager
from copy import deepcopy

def setup(rank, world_size):
    os.environ['MASTER_ADDR'] = 'localhost'
    os.environ['MASTER_PORT'] = '12356'

    # initialize the process group
    #dist.init_process_group("gloo", rank=rank, world_size=world_size)
    torch.distributed.init_process_group(
        backend="nccl",
        # init_method="tcp://" + args.dist_url, # if "--dist_url": "$AZ_BATCH_MASTER_NODE"
        #init_method=args.dist_url,
        init_method="tcp://"+os.environ['MASTER_ADDR']+":"+os.environ['MASTER_PORT'],
        world_size=world_size,
        rank=rank,
    )

    # Explicitly setting seed to make sure that models created in two processes
    # start from same random weights and biases.
    torch.manual_seed(42)


def cleanup():
    dist.destroy_process_group()

    ## Set QUICK_RUN = True to run the notebook on a small subset of data and a smaller number of epochs.
QUICK_RUN = True
## Set USE_PREPROCSSED_DATA = True to skip the data preprocessing
USE_PREPROCSSED_DATA = True

import os
import sys
from tempfile import TemporaryDirectory
import torch

nlp_path = os.path.abspath("../../")
if nlp_path not in sys.path:
    sys.path.insert(0, nlp_path)

from utils_nlp.common.pytorch_utils import get_device
from utils_nlp.dataset.cnndm import CNNDMBertSumProcessedData
from utils_nlp.eval.evaluate_summarization import get_rouge
from utils_nlp.models.transformers.extractive_summarization import (
    ExtractiveSummarizer,
    ExtSumProcessedData,
    ExtSumProcessor,
)


       
# Transformer model being used
MODEL_NAME = "distilbert-base-uncased"
PROCESSED_DATA_PATH = TemporaryDirectory().name
data_path = "./temp_data5/"
PROCESSED_DATA_PATH = data_path
if USE_PREPROCSSED_DATA:
    CNNDMBertSumProcessedData.download(local_path=PROCESSED_DATA_PATH)
    train_dataset, test_dataset = ExtSumProcessedData().splits(root=PROCESSED_DATA_PATH)
# notebook parameters
# the cache data path during find tuning
CACHE_DIR = TemporaryDirectory().name

# batch size, unit is the number of tokens
BATCH_SIZE = 3000

# GPU used for training
NUM_GPUS = 4

# Encoder name. Options are: 1. baseline, classifier, transformer, rnn.
ENCODER = "transformer"

summarizer = ExtractiveSummarizer(MODEL_NAME, ENCODER, CACHE_DIR)


def score(rank, world_size, test_result):
    setup(rank, world_size)
    torch.cuda.set_device(rank)

    start = time.time()
    prediction = summarizer.predict(test_dataset, num_gpus=world_size, local_rank=rank)
    end = time.time()
    print("rank {0}, duration {1:.6f}s".format(rank, end - start))
    test_result.append((rank,prediction))
    cleanup()
    
def run_demo(demo_fn, world_size, test_result):
    mp.spawn(demo_fn,
             args=(world_size,test_result,),
             nprocs=world_size,
             join=True)

if __name__ == "__main__":
    with Manager() as manager:
        """
        test_results = manager.list()
        run_demo(score, NUM_GPUS, test_results)
        results = deepcopy(test_results)
        print("results", len(results))"""
        result = [(0, ["hello", "how are you"]),
                  (3, ["I am good", "bad weahter"]),
                  (2, ["dalfsdfha"], ["dahfldsakd"],
                  (1, ["okay", ["okay"]]))]
        predictions = []
        new_list = sorted(results, key=lambda x: x[0])
        for i in range(len(new_list)):
            print(len(new_list[i][1]))
            print(results[i][1][2])
