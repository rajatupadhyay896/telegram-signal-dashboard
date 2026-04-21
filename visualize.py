import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("outputs/rankings.csv", index_col=0)

df.plot(kind="bar", legend=False)
plt.title("Telegram Signal Quality Ranking (Advanced)")
plt.ylabel("Score")
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig("outputs/ranking_chart.png")

print("Chart saved to outputs/ranking_chart.png")
