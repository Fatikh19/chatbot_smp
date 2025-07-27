import pandas as pd
import numpy as np
import tensorflow as tf
import re
import pickle
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Input, LSTM, Dense, Embedding
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import os
import matplotlib.pyplot as plt
from tensorflow.keras.optimizers import Adam
import string

# --- Fungsi bantu ---
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

def clean_text_input(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # hapus semua tanda baca
    return text.strip()

def clean_text_response(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)  # hanya normalisasi spasi, tidak menghapus tanda baca
    return text.strip()

# --- Config ---
train_model = True  # Ubah ke True jika ingin melatih ulang
max_input_len = 20
max_response_len = 30
embedding_dim = 128
latent_dim = 256
model_path = "chatbot_rnn.h5"
tokenizer_path = "tokenizer.pkl"

# --- Training Mode ---
if train_model:
    print("[INFO] Melatih model...")
    data = pd.read_csv("dataset.csv").dropna()
    data['input'] = data['input'].astype(str).apply(clean_text_input)
    data['response'] = data['response'].astype(str).apply(clean_text_response)
    data['input_with_intent'] = data['intent'] + " " + data['input']

    inputs = data['input_with_intent'].tolist()
    responses = ["<sos> " + r + " <eos>" for r in data['response'].tolist()]

    tokenizer = Tokenizer(filters='')
    tokenizer.fit_on_texts(inputs + responses)

    input_sequences = tokenizer.texts_to_sequences(inputs)
    response_sequences = tokenizer.texts_to_sequences(responses)

    max_input_len = max(len(seq) for seq in input_sequences)
    max_response_len = max(len(seq) for seq in response_sequences)

    encoder_input = pad_sequences(input_sequences, maxlen=max_input_len, padding='post')
    decoder_input = pad_sequences(response_sequences, maxlen=max_response_len, padding='post')

    decoder_target = np.zeros_like(decoder_input)
    decoder_target[:, :-1] = decoder_input[:, 1:]

    vocab_size = len(tokenizer.word_index) + 1

    encoder_inputs = Input(shape=(None,))
    enc_emb = Embedding(vocab_size, embedding_dim)(encoder_inputs)
    encoder_lstm, state_h, state_c = LSTM(latent_dim, return_state=True)(enc_emb)
    encoder_states = [state_h, state_c]

    decoder_inputs = Input(shape=(None,))
    dec_emb = Embedding(vocab_size, embedding_dim)(decoder_inputs)
    decoder_lstm, _, _ = LSTM(latent_dim, return_sequences=True, return_state=True)(dec_emb, initial_state=encoder_states)
    decoder_outputs = Dense(vocab_size, activation='softmax')(decoder_lstm)

    learning_rate = 0.001  # You can adjust this value
    optimizer = Adam(learning_rate=learning_rate)

    model = Model([encoder_inputs, decoder_inputs], decoder_outputs)
    model.compile(optimizer=optimizer, loss='sparse_categorical_crossentropy', metrics=['accuracy'])

    history = model.fit([encoder_input, decoder_input], np.expand_dims(decoder_target, -1),
              batch_size=64,
              epochs=500,
              validation_split=0.2)

    model.save(model_path)
    with open(tokenizer_path, "wb") as f:
        pickle.dump(tokenizer, f)

    print(f"[INFO] Model dan tokenizer disimpan.")

    # --------------------------
    # 🔹 Plot Training Graphs
    # --------------------------
    plt.figure(figsize=(12, 5))

    # Plot Loss
    plt.subplot(1, 2, 1)
    plt.plot(history.history['loss'], label='Training Loss', color='blue')
    plt.plot(history.history['val_loss'], label='Validation Loss', color='red')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.title('Loss Curve')
    plt.legend()

    # Plot Accuracy
    plt.subplot(1, 2, 2)
    plt.plot(history.history['accuracy'], label='Training Accuracy', color='blue')
    plt.plot(history.history['val_accuracy'], label='Validation Accuracy', color='red')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.title('Accuracy Curve')
    plt.legend()

    plt.savefig("training_graph.png", dpi=300)
    plt.close()

    # --------------------------
    # 🔹 Training Summary Report
    # --------------------------
    print("\n[INFO] Training Summary Report")
    print("-" * 30)
    print(f"Total Epochs: {len(history.history['loss'])}")
    print(f"Final Training Loss: {history.history['loss'][-1]:.4f}")
    print(f"Final Validation Loss: {history.history['val_loss'][-1]:.4f}")
    print(f"Final Training Accuracy: {history.history['accuracy'][-1]:.4f}")
    print(f"Final Validation Accuracy: {history.history['val_accuracy'][-1]:.4f}")
    print("-" * 30)

else:
    print("[INFO] Memuat model dan tokenizer...")
    model = load_model(model_path)
    with open(tokenizer_path, "rb") as f:
        tokenizer = pickle.load(f)

# --- Intent Detection ---
intent_list = [
    'ucapan_salam',
    'tanya_biaya_formulir',
    'tanya_biaya_seragam',
    'tanya_biaya_dsp',
    'tanya_biaya_pendaftaran',
    'tanya_biaya_spp',
    'tanya_biaya_ujian',
    'tanya_biaya_ekstrakulikuler',
    'tanya_biaya_paket',
    'tanya_biaya_lks',
]

def detect_intent(text):
    text = clean_text(text)

    if any(word in text for word in [
        'halo', 'assalamu', 'selamat', 'hai', 'wassalamu',
        'pagi', 'siang', 'sore', 'malam', 'terima kasih',
        'makasih', 'terimakasih', 'tanya'
    ]):
        return 'ucapan_salam'
    
    elif any(word in text for word in [
        'formulir', 'harga formulir', 'formulr', 'daftar ulang',
        'formulir daftar', 'formulir pendaftaran'
    ]):
        return 'tanya_biaya_formulir'
    
    elif any(word in text for word in [
        'seragam', 'seragamnya', 'baju sekolah', 'harga seragam', 'total seragam'
    ]):
        return 'tanya_biaya_seragam'
    
    elif any(word in text for word in [
        'dsp', 'gedung', 'bangunan', 'biaya gedung'
    ]):
        return 'tanya_biaya_dsp'
    
    elif any(word in text for word in [
        'pendaftaran', 'daftar masuk', 'biaya daftar', 'beban',
        'biaya pendaftaran', 'total daftar', 'daftar formulir'
    ]):
        return 'tanya_biaya_pendaftaran'
    
    elif any(word in text for word in [
        'spp', 'bayar bulanan', 'biaya spp', 'spp naik', 'spp total', 'spp total setahun'
    ]):
        return 'tanya_biaya_spp'
    
    elif any(word in text for word in [
        'ujian', 'ujian nasional', 'ujian sekolah',
        'ujian praktek', 'ujian sumatif', 'anbk', 'sumatif', 'sumatif tengah', 'sumatif akhir'
    ]):
        return 'tanya_biaya_ujian'
    
    elif any(word in text for word in [
        'ekstra', 'ekskul', 'ekstrakulikuler',
        'eskul', 'pramuka', 'silat', 'hadroh', 'futsal'
        , 'ekskul pramuka', 'ekskul silat', 'ekskul hadroh', 'ekskul futsal'
    ]):
        return 'tanya_biaya_ekstrakulikuler'
    
    elif any(word in text for word in [
        'paket', 'buku paket', 'biaya buku paket'
    ]):
        return 'tanya_biaya_paket'
    
    elif any(word in text for word in [
        'lks', 'buku lks', 'biaya buku lks'
    ]):
        return 'tanya_biaya_lks'
    else:
        return None


def proper_case(text):
    if not text:
        return ""
    
    # Normalisasi spasi
    text = text.strip()
    
    # Konversi awal ke lowercase
    text = text.lower()

    # Daftar istilah khusus yang perlu tetap kapital
    special_terms = ['rp', 'smp', 'islam', 'arrohman','rp.','spp','dsp','anbk','lks','arrohman.']

    words = text.split()
    for i, word in enumerate(words):
        # Huruf pertama kalimat selalu kapital
        if i == 0:
            words[i] = word.capitalize()
        elif word in special_terms:
            words[i] = word.upper()
    
    # Gabungkan kembali
    result = ' '.join(words)
    
    # Tambahkan titik jika belum ada tanda baca di akhir
    if result[-1] not in string.punctuation:
        result += '.'
    
    return result

def generate_response(input_text, intent):
    full_input = f"{intent} {clean_text_input(input_text)}"
    input_seq = tokenizer.texts_to_sequences([full_input])
    input_seq = pad_sequences(input_seq, maxlen=max_input_len, padding='post')

    response = ['<sos>']
    for _ in range(max_response_len):
        token_seq = tokenizer.texts_to_sequences([response])[0]
        token_seq = pad_sequences([token_seq], maxlen=max_response_len, padding='post')

        predictions = model.predict([input_seq, token_seq], verbose=0)
        next_token_id = np.argmax(predictions[0, len(response)-1])
        next_word = tokenizer.index_word.get(next_token_id, '')
        if next_word == '<eos>' or not next_word:
            break
        response.append(next_word)

    # Join the response and remove <sos> and <eos>
    final_response = ' '.join(response[1:])
    final_response = final_response.replace('<eos>', '').strip()  # Remove <eos> token
    return proper_case(final_response)

def chatbot_reply(input_text):
    try:
        intent = detect_intent(input_text)
        if intent is None:
            return "Maaf saya tidak mengerti, harap ketik ulang pertanyaan yang lebih spesifik."
        
        reply = generate_response(input_text, intent)
        return reply if reply else "Maaf saya tidak mengerti, harap ketik ulang pertanyaan yang lebih spesifik."
    except Exception as e:
        return f"Terjadi kesalahan: {str(e)}"