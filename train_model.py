# train_model.py
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping
import matplotlib.pyplot as plt

# ── Load data ──
df = pd.read_csv('dataset/landmarks.csv')
X = df.drop('label', axis=1).values   # 63 features (21 landmarks × x,y,z)
y = df['label'].values

# ── Normalize ──
# Landmarks are already 0–1 normalized by MediaPipe, but
# we subtract wrist position to make it hand-position independent
def normalize_landmarks(X):
    X = X.reshape(-1, 21, 3)
    # Subtract wrist (landmark 0) to make relative
    wrist = X[:, 0:1, :]
    X = X - wrist
    return X.reshape(-1, 63)

X = normalize_landmarks(X)

# ── Encode labels ──
le = LabelEncoder()
y_encoded = le.fit_transform(y)
y_cat = tf.keras.utils.to_categorical(y_encoded)

# ── Train/test split ──
X_train, X_test, y_train, y_test = train_test_split(
    X, y_cat, test_size=0.2, random_state=42, stratify=y_encoded
)

print(f"Training samples: {len(X_train)}")
print(f"Test samples    : {len(X_test)}")
print(f"Classes         : {le.classes_}")

# ── Model ──
model = Sequential([
    Dense(128, activation='relu', input_shape=(63,)),
    BatchNormalization(),
    Dropout(0.3),
    Dense(64, activation='relu'),
    BatchNormalization(),
    Dropout(0.2),
    Dense(32, activation='relu'),
    Dense(len(le.classes_), activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

model.summary()

# ── Train ──
early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

history = model.fit(
    X_train, y_train,
    epochs=100,
    batch_size=32,
    validation_data=(X_test, y_test),
    callbacks=[early_stop],
    verbose=1
)

# ── Evaluate ──
loss, acc = model.evaluate(X_test, y_test, verbose=0)
print(f"\nTest Accuracy: {acc*100:.2f}%")

# ── Save model ──
model.save('gesture_model.h5')
import json
with open('label_classes.json', 'w') as f:
    json.dump(le.classes_.tolist(), f)
print("Model saved as gesture_model.h5")
print("Labels saved as label_classes.json")

# ── Plot training curves ──
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

ax1.plot(history.history['accuracy'],    label='Train Acc')
ax1.plot(history.history['val_accuracy'],label='Val Acc')
ax1.set_title('Accuracy'); ax1.legend(); ax1.grid(True)

ax2.plot(history.history['loss'],    label='Train Loss')
ax2.plot(history.history['val_loss'],label='Val Loss')
ax2.set_title('Loss'); ax2.legend(); ax2.grid(True)

plt.tight_layout()
plt.savefig('training_curves.png')
plt.show()
print("Training curves saved.")