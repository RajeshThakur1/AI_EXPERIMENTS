import streamlit as st
import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Load the saved model
model = tf.keras.models.load_model('sentiment_model.h5', compile=False)
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
# Load the tokenizer
# You should save and load the tokenizer along with the model
# For now, we'll recreate it (this might not be accurate)
tokenizer = Tokenizer(num_words=5000)