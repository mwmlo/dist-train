from __future__ import absolute_import, division, print_function

import argparse
import json
import os

import tensorflow as tf


def make_datasets_unbatched():
  BUFFER_SIZE = 10000

  # Preprocessing functions
  def preprocess(x, y):
    pass
  
  datasets = ...
  return datasets['train'].map(preprocess).cache().shuffle(BUFFER_SIZE)


def build_and_compile_model():
  pass

def decay(epoch):
  if epoch < 3:
    return 1e-3
  if 3 <= epoch < 7:
    return 1e-4
  return 1e-5

def main(args):

  # MultiWorkerMirroredStrategy creates copies of all variables in the model's
  # layers on each device across all workers
  # if your GPUs don't support NCCL, replace "communication" with another
  # https://www.tensorflow.org/tutorials/distribute/keras
  strategy = tf.distribute.MultiWorkerMirroredStrategy(
      communication_options=tf.distribute.experimental.CommunicationOptions(implementation=tf.distribute.experimental.CollectiveCommunication.AUTO))

  BATCH_SIZE_PER_REPLICA = 64
  BATCH_SIZE = BATCH_SIZE_PER_REPLICA * strategy.num_replicas_in_sync

  with strategy.scope():
    ds_train = make_datasets_unbatched().batch(BATCH_SIZE).repeat()
    options = tf.data.Options()
    # https://www.tensorflow.org/tutorials/distribute/input
    options.experimental_distribute.auto_shard_policy = \
        tf.data.experimental.AutoShardPolicy.DATA
    ds_train = ds_train.with_options(options)
    # Model building/compiling need to be within `strategy.scope()`.
    multi_worker_model = build_and_compile_model()

  # Define the checkpoint directory to store the checkpoints
  checkpoint_dir = args.checkpoint_dir

  # Name of the checkpoint files
  checkpoint_prefix = os.path.join(checkpoint_dir, "ckpt_{epoch}")

  # Function for decaying the learning rate.
  # You can define any decay function you need.
  # Callback for printing the LR at the end of each epoch.
  class PrintLR(tf.keras.callbacks.Callback):

    def on_epoch_end(self, epoch, logs=None): #pylint: disable=no-self-use
      print('\nLearning rate for epoch {} is {}'.format(
        epoch + 1, multi_worker_model.optimizer.lr.numpy()))

  callbacks = [
      tf.keras.callbacks.TensorBoard(log_dir='./logs'),
      tf.keras.callbacks.ModelCheckpoint(filepath=checkpoint_prefix,
                                         save_weights_only=True),
      tf.keras.callbacks.LearningRateScheduler(decay),
      PrintLR()
  ]

  # Keras' `model.fit()` trains the model with specified number of epochs and
  # number of steps per epoch. Note that the numbers here are for demonstration
  # purposes only and may not sufficiently produce a model with good quality.
  multi_worker_model.fit(ds_train,
                         epochs=1,
                         steps_per_epoch=70,
                         callbacks=callbacks)

  # Saving a model
  # Let `is_chief` be a utility function that inspects the cluster spec and
  # current task type and returns True if the worker is the chief and False
  # otherwise.
  def is_chief():
    return TASK_INDEX == 0

  if is_chief():
    model_path = args.saved_model_dir

  else:
    # Save to a path that is unique across workers.
    model_path = args.saved_model_dir + '/worker_tmp_' + str(TASK_INDEX)

  multi_worker_model.save(model_path)


if __name__ == '__main__':
  os.environ['NCCL_DEBUG'] = 'INFO'

  # to decide if a worker is chief, get TASK_INDEX in Cluster info
  tf_config = json.loads(os.environ.get('TF_CONFIG') or '{}')
  TASK_INDEX = tf_config['task']['index']

  parser = argparse.ArgumentParser()
  parser.add_argument('--saved_model_dir',
                      type=str,
                      required=True,
                      help='Tensorflow export directory.')

  parser.add_argument('--checkpoint_dir',
                      type=str,
                      required=True,
                      help='Tensorflow checkpoint directory.')

  parsed_args = parser.parse_args()
  main(parsed_args)