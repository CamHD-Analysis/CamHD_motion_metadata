#!/usr/bin/env python3

"""
Train a CNN classification model.

TODO: Currently the selected models are persisted as a model_config after the training done using this script.

# Ref: https://blog.keras.io/building-powerful-image-classification-models-using-very-little-data.html
# Ref: https://keras.io/applications/#vgg16

Note: If the classification model details are are updated, then the 'DEFAULT_CNN_MODEL_CONFIG'
in the process_regions_files.py script also needs to be updated.

"""
from keras.models import Sequential
from keras.layers import Activation, BatchNormalization, Conv2D, Dense, Dropout, Flatten, MaxPooling2D
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping, ModelCheckpoint, TensorBoard
from keras.preprocessing.image import ImageDataGenerator

import argparse
import logging
import os
import random
import shutil


# TODO: This could be generalized once the script allows multiple types of models by reading form model_config.
TARGET_SIZE = (256, 256, 3)

SCENE_TAGS_CLASSIFICATION_SPEC_STRING = "SCENE_TAGS"
SCENE_TAGS_PLAIN_WATER_CLASSIFICATION_SPEC_STRING = "SCENE_TAGS_PLAIN_WATER"

# TODO: Keep this logic at one place.
# Standard CamHD scene_tags.
SCENE_TAGS = [
    'p0_z0',
    'p0_z1',
    'p0_z2',
    'p1_z0',
    'p1_z1',
    'p2_z0',
    'p2_z1',
    'p3_z0',
    'p3_z1',
    'p3_z2',
    'p4_z0',
    'p4_z1',
    'p4_z2',
    'p5_z0',
    'p5_z1',
    'p5_z2',
    'p6_z0',
    'p6_z1',
    'p6_z2',
    'p7_z0',
    'p7_z1',
    'p8_z0',
    'p8_z1'
]

SCENE_TAGS_PLAIN_WATER = [
    'p0_z0',
    'p0_z1',
    'p0_z2',
    'p1_z0',
    'p1_z1',
    'p2_z0',
    'plain_water', # 'p2_z1' and 'p4_z2'
    'p3_z0',
    'p3_z1',
    'p3_z2',
    'p4_z0',
    'p4_z1',
    # 'p4_z2',
    'p5_z0',
    'p5_z1',
    'p5_z2',
    'p6_z0',
    'p6_z1',
    'p6_z2',
    'p7_z0',
    'p7_z1',
    'p8_z0',
    'p8_z1'
]

#os.environ["CUDA_VISIBLE_DEVICES"] = "0"

def get_args():
    parser = argparse.ArgumentParser(description="Run the Training Pipeline for scene_tag classification.")
    parser.add_argument('--func',
                        required=True,
                        help="Specify the function to be called. The available list of functions: ['train_cnn', 'test_cnn'].")
    parser.add_argument('--data-dir',
                        help="The path to the data directory containing the images corresponding to each class label. "
                             "The images of each class label must be organized into separate directory having the "
                             "the name of the corresponding class label."
                             "Valid for functions: 'train_cnn'.")
    parser.add_argument('--classes',
                        required=True,
                        help="The set of classes to be considered. Provide comma separated string. "
                             "Specify '%s' to classify the standard scene_tags in CamHD. "
                             "Specify '%s' for scene_tags 'p2_z1' and 'p4_z2' considered as plain_water."
                             % (SCENE_TAGS_CLASSIFICATION_SPEC_STRING, SCENE_TAGS_PLAIN_WATER_CLASSIFICATION_SPEC_STRING))
    parser.add_argument('--deployment',
                        help="Must be provided if classes is '%s'. Specify the deployment version to be "
                             "prefixed to the standard scene_tags."
                             % SCENE_TAGS_CLASSIFICATION_SPEC_STRING)
    parser.add_argument('--val-split',
                        type=float,
                        default=0.20,
                        help="The validation split ratio. Default: 0.20."
                             "Valid for functions: 'train_cnn'.")
    parser.add_argument('--epochs',
                        type=int,
                        default=100,
                        help="The number of epochs to be run. Default: 100."
                             "Valid for functions: 'train_cnn'.")
    parser.add_argument('--batch-size',
                        type=int,
                        default=32,
                        help="The batch_size for training. Default: 32."
                             "Valid for functions: 'train_cnn'.")
    parser.add_argument('--model-outfile',
                        required=True,
                        help="The path to the model output file (HDF5 file)."
                             "Valid for functions: 'train_cnn', 'test_cnn'.")
    parser.add_argument('--tensorboard-logdir',
                        help="The path to the Tensorboard log directory. If not provided, tensorboard logs will not be written."
                             "Valid for functions: 'train_cnn'.")
    parser.add_argument('--image-ext',
                        dest="img_ext",
                        default='png',
                        help="The image file extension. Default: png."
                             "Valid for functions: 'train_cnn', 'test_cnn'.")
    parser.add_argument('--test-dir',
                        help="The path to the test data directory containing the test patches. "
                             "Valid for functions: 'test_cnn'.")
    parser.add_argument('--test-output-path',
                        help="The path to the output file where the predictions (csv) need to be written."
                             "Valid for functions: 'test_cnn'.")
    parser.add_argument("--log",
                        default="INFO",
                        help="Specify the log level. Default: INFO.")

    return parser.parse_args()


def vgg16_custom(num_classes, input_size, batch_norm=True, pretrained_weights=None):
    model = Sequential()

    model.add(Conv2D(32, (3, 3), padding='same', name='block1_conv1', input_shape=input_size))
    model.add(BatchNormalization()) if batch_norm else None
    model.add(Activation('relu'))

    model.add(Conv2D(32, (3, 3), padding='same', name='block1_conv2'))
    model.add(BatchNormalization()) if batch_norm else None
    model.add(Activation('relu'))

    model.add(MaxPooling2D((2, 2), strides=(2, 2), name='block1_pool'))

    model.add(Conv2D(64, (3, 3), padding='same', name='block2_conv1'))
    model.add(BatchNormalization()) if batch_norm else None
    model.add(Activation('relu'))

    model.add(Conv2D(64, (3, 3), padding='same', name='block2_conv2'))
    model.add(BatchNormalization()) if batch_norm else None
    model.add(Activation('relu'))

    model.add(MaxPooling2D((2, 2), strides=(2, 2), name='block2_pool'))

    model.add(Conv2D(128, (3, 3), padding='same', name='block3_conv1'))
    model.add(BatchNormalization()) if batch_norm else None
    model.add(Activation('relu'))

    model.add(Conv2D(128, (3, 3), padding='same', name='block3_conv2'))
    model.add(BatchNormalization()) if batch_norm else None
    model.add(Activation('relu'))

    model.add(MaxPooling2D((2, 2), strides=(2, 2), name='block3_pool'))

    model.add(Conv2D(256, (3, 3), padding='same', name='block4_conv1'))
    model.add(BatchNormalization()) if batch_norm else None
    model.add(Activation('relu'))

    model.add(Conv2D(256, (3, 3), padding='same', name='block4_conv2'))
    model.add(BatchNormalization()) if batch_norm else None
    model.add(Activation('relu'))

    model.add(MaxPooling2D((2, 2), strides=(2, 2), name='block4_pool'))

    model.add(Conv2D(512, (3, 3), padding='same', name='block5_conv1'))
    model.add(BatchNormalization()) if batch_norm else None
    model.add(Activation('relu'))

    model.add(Conv2D(512, (3, 3), padding='same', name='block5_conv2'))
    model.add(BatchNormalization()) if batch_norm else None
    model.add(Activation('relu'))

    model.add(MaxPooling2D((2, 2), strides=(2, 2), name='block5_pool'))

    model.add(Flatten())

    model.add(Dense(1024, name='fc1'))
    model.add(BatchNormalization()) if batch_norm else None
    model.add(Activation('relu'))
    model.add(Dropout(0.5))

    model.add(Dense(2048, name='fc2'))
    model.add(BatchNormalization()) if batch_norm else None
    model.add(Activation('relu'))
    model.add(Dropout(0.5))

    model.add(Dense(num_classes))
    model.add(BatchNormalization()) if batch_norm else None
    model.add(Activation('softmax'))

    model.compile(optimizer=Adam(lr=0.001), loss='categorical_crossentropy', metrics=['accuracy'])

    if(pretrained_weights):
        model.load_weights(pretrained_weights)

    return model


# Stratified splitting.
def get_train_val_split(data_dir, val_split, allow_exist=True):
    split_exists = False
    if val_split > 0.5:
        raise ValueError("The validation split of 0.5 and above are not accepted.")

    train_dir = data_dir + "_train"
    if os.path.exists(train_dir):
        if not allow_exist:
            raise ValueError("The train_dir already exists: %s" % train_dir)
        split_exists = True
    else:
        os.makedirs(train_dir)

    val_dir = data_dir + "_val"
    if os.path.exists(val_dir):
        if not allow_exist:
            raise ValueError("The val_dir already exists: %s" % val_dir)
    else:
        if split_exists:
            raise ValueError("The train_dir already exists but val_dir doesn't exist.")

        os.makedirs(val_dir)

    if split_exists:
        train_size = 0
        val_size = 0

        labels = os.listdir(data_dir)
        for label in labels:
            train_label_dir_path = os.path.join(train_dir, label)
            train_size += len(os.listdir(train_label_dir_path))

            val_label_dir_path = os.path.join(val_dir, label)
            val_size += len(os.listdir(val_label_dir_path))

        return train_dir, val_dir, train_size, val_size

    # Create new splits.
    train_size = 0
    val_size = 0

    # Each of these labels must be directories.
    labels = os.listdir(data_dir)
    for label in labels:
        orig_label_dir_path = os.path.join(data_dir, label)
        if not os.path.isdir(orig_label_dir_path):
            raise ValueError("The data doesn't seem to have been correctly organized.")

        train_label_dir_path = os.path.join(train_dir, label)
        os.makedirs(train_label_dir_path)
        val_label_dir_path = os.path.join(val_dir, label)
        os.makedirs(val_label_dir_path)

        img_names = os.listdir(orig_label_dir_path)
        random.shuffle(img_names)

        num_imgs = len(img_names)
        cur_train_size = int(num_imgs * (1 - val_split))

        c = 0
        for img_name in img_names:
            c += 1

            src_img_path = os.path.join(orig_label_dir_path, img_name)

            # Stratified sub-sampling with respect to cur_train_size.
            if c <= cur_train_size:
                train_size += 1
                dest_img_path = os.path.join(train_label_dir_path, img_name)
            else:
                val_size += 1
                dest_img_path = os.path.join(val_label_dir_path, img_name)

            shutil.copy(src_img_path, dest_img_path)

    return train_dir, val_dir, train_size, val_size


def train_cnn(args):
    # Data preparation
    train_dir, val_dir, train_size, val_size = get_train_val_split(args.data_dir, args.val_split)

    # Load the model and compile.
    model = vgg16_custom(len(args.classes), input_size=TARGET_SIZE, batch_norm=True)

    # Setup data loading.
    # This is the augmentation configuration we will use for training.
    # TODO: Allow specification of different augmentations through config.
    train_datagen = ImageDataGenerator(rescale=1./255)

    # This is the augmentation configuration we will use for testing: only rescaling.
    test_datagen = ImageDataGenerator(rescale=1./255)

    # This is a generator that will read pictures found in subfolders of 'data/train', and indefinitely generate
    # batches of augmented image data.
    train_generator = train_datagen.flow_from_directory(train_dir,
                                                        target_size=TARGET_SIZE[:-1],
                                                        batch_size=args.batch_size,
                                                        color_mode="rgb",
                                                        class_mode='categorical',
                                                        classes=args.classes,
                                                        seed=3)

    # This is a similar generator, for validation data.
    validation_generator = test_datagen.flow_from_directory(val_dir,
                                                            target_size=TARGET_SIZE[:-1],
                                                            batch_size=args.batch_size,
                                                            color_mode="rgb",
                                                            class_mode='categorical',
                                                            classes=args.classes,
                                                            seed=3)

    # Setup training.
    model_checkpoint = ModelCheckpoint(args.model_outfile, monitor='val_acc', mode='auto', verbose=1, save_best_only=True)
    early_stopping = EarlyStopping(monitor='val_loss', min_delta=0, patience=10, verbose=0, mode='auto')
    callbacks = [model_checkpoint, early_stopping]
    if args.tensorboard_logdir:
        tensorboard = TensorBoard(log_dir=args.tensorboard_logdir)
        logging.info("To view tensorboard, run: 'tensorboard --logdir=%s'" % args.tensorboard_logdir)
        callbacks.append(tensorboard)

    model.fit_generator(train_generator,
                        steps_per_epoch=train_size/args.batch_size,
                        validation_data=validation_generator,
                        validation_steps=val_size/args.batch_size,
                        epochs=args.epochs,
                        shuffle=True,
                        callbacks=callbacks)

    logging.info("The trained model has been saved in %s" % args.model_outfile)


def test_cnn(args):
    pass


if __name__ == "__main__":
    args = get_args()
    logging.basicConfig(level=args.log.upper())

    if args.classes in (SCENE_TAGS_CLASSIFICATION_SPEC_STRING, SCENE_TAGS_PLAIN_WATER_CLASSIFICATION_SPEC_STRING):
        if not args.deployment:
            raise ValueError("The --deployment needs to be provided since the classes provided is %s" % args.classes)

        if args.classes == SCENE_TAGS_CLASSIFICATION_SPEC_STRING:
            args.classes = ["%s_%s" % (args.deployment, x) for x in SCENE_TAGS]
        else:
            args.classes = ["%s_%s" % (args.deployment, x) for x in SCENE_TAGS_PLAIN_WATER]

    if args.func == "train_cnn":
        train_cnn(args)
    elif args.func == "test_cnn":
        test_cnn(args)
    else:
        raise ValueError("The given function is not supported: %s" % args.func)
