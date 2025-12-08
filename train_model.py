import os
import csv
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib

def load_folder(path, label):
    X = []
    y = []
    for fname in os.listdir(path):
        if not fname.endswith(".csv"):
            continue
        with open(os.path.join(path, fname)) as f:
            reader = csv.DictReader(f)
            Lvalues = []
            Rvalues = []
            for row in reader:
                Lvalues.append(float(row["L"]))
                Rvalues.append(float(row["R"]))

            # características del archivo
            feat = [
                np.mean(Lvalues), np.std(Lvalues),
                np.mean(Rvalues), np.std(Rvalues)
            ]
            X.append(feat)
            y.append(label)
    return X, y

# cargar dataset
Xa, ya = load_folder("dataset/ambiente", 0)
Xl, yl = load_folder("dataset/linterna", 1)

X = np.array(Xa + Xl)
y = np.array(ya + yl)

# entrenar modelo
clf = RandomForestClassifier(n_estimators=200)
clf.fit(X, y)

# guardar modelo
joblib.dump(clf, "modelo_luz.pkl")

print("Modelo entrenado y guardado como modelo_luz.pkl")
