import os
import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB4
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, Conv2D, Multiply
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.optimizers import SGD, Adam
from tensorflow.keras.callbacks import ReduceLROnPlateau, EarlyStopping, ModelCheckpoint

def attention_block(x):
    attention = Conv2D(1, kernel_size=(1, 1), activation='sigmoid')(x)
    return Multiply()([x, attention])

def build_model(num_classes):
    base_model = EfficientNetB4(include_top=False, weights='imagenet', input_shape=(224, 224, 3))

    for layer in base_model.layers[-30:]:
        layer.trainable = True
    
 
    x = base_model.output
    x = attention_block(x)
    x = GlobalAveragePooling2D()(x)
    

    x = Dropout(0.5)(x)
    x = Dense(1024, activation='relu')(x)
    x = Dropout(0.5)(x)
    predictions = Dense(num_classes, activation='softmax')(x)
    

    model = Model(inputs=base_model.input, outputs=predictions)
    
    return model

dataset_dir = r'D:\Kartik Gounder\Dataset\Plant Disease Detection\Limited_class'

train_datagen = ImageDataGenerator(
    rescale=1.0/255.0,
    rotation_range=30,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.3,
    horizontal_flip=True,
    fill_mode='nearest',
    validation_split=0.2
)
train_generator = train_datagen.flow_from_directory(
    dataset_dir,  
    target_size=(224, 224),
    batch_size=16,
    class_mode='categorical',
    subset='training'
)

val_generator = train_datagen.flow_from_directory(
    dataset_dir,
    target_size=(224, 224),
    batch_size=16,
    class_mode='categorical',
    subset='validation'
)
num_classes = len(train_generator.class_indices)
model = build_model(num_classes)

model.compile(optimizer=SGD(learning_rate=0.001, momentum=0.9),
              loss='categorical_crossentropy', 
              metrics=['accuracy'])

early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6)
checkpoint = ModelCheckpoint('best_model.h5', monitor='val_accuracy', save_best_only=True, mode='max')

history = model.fit(train_generator,
                    validation_data=val_generator,
                    epochs=20,
                    callbacks=[early_stopping, reduce_lr, checkpoint],
                    verbose=1)
model.save('plant_disease_model_with_attention.h5')
import json

def save_history(history, filename='training_history.json'):
    history_dict = {key: [float(val) for val in values] for key, values in history.history.items()}
    
    with open(filename, 'w') as f:
        json.dump(history_dict, f)

save_history(history, 'training_history.json')

# # Function to load history
# def load_history(filename='training_history.json'):
#     # Open and load the JSON file
#     with open(filename, 'r') as f:
#         history = json.load(f)
#     return history

# # Load the saved history
# loaded_history = load_history('training_history.json')

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix

def plot_training_results(history):
    acc = history.history['accuracy']
    val_acc = history.history['val_accuracy']
    loss = history.history['loss']
    val_loss = history.history['val_loss']

    epochs_range = range(len(acc))

    plt.figure(figsize=(12, 6))

    # Plot accuracy
    plt.subplot(1, 2, 1)
    plt.plot(epochs_range, acc, label='Training Accuracy')
    plt.plot(epochs_range, val_acc, label='Validation Accuracy')
    plt.legend(loc='lower right')
    plt.title('Training and Validation Accuracy')

    # Plot loss
    plt.subplot(1, 2, 2)
    plt.plot(epochs_range, loss, label='Training Loss')
    plt.plot(epochs_range, val_loss, label='Validation Loss')
    plt.legend(loc='upper right')
    plt.title('Training and Validation Loss')

    plt.show()

plot_training_results(history)

def evaluate_model(model, val_generator):

    y_pred = model.predict(val_generator)
    y_pred_classes = np.argmax(y_pred, axis=1)

    y_true = val_generator.classes

    class_labels = list(val_generator.class_indices.keys())

    print("Classification Report:")
    print(classification_report(y_true, y_pred_classes, target_names=class_labels))

    cm = confusion_matrix(y_true, y_pred_classes)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_labels, yticklabels=class_labels)
    plt.title("Confusion Matrix")
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.show()

evaluate_model(model, val_generator)

