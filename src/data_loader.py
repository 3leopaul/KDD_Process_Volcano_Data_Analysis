import pandas as pd

DATA_PATH = "volcano-events.tsv"

def load_data():
    """
    Charge le fichier volcano-events.tsv et renvoie un DataFrame.
    """
    df = pd.read_csv(DATA_PATH, sep="\t")
    return df

if __name__ == "__main__":
    df = load_data()
    print(df.head())
