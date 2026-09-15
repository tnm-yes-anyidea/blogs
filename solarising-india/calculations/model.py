from pathlib import Path
import csv
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"; FIG=ROOT/"figures"
G=1900; EFF=.22; PR=.80
print("Useful PV output:", G*EFF*PR, "kWh/m²/year")
years=range(2026,2041)
demand=[2000*(1.045)**(y-2026) for y in years]
capacity=[168.04+(1000-168.04)*(y-2026)/14 for y in years]
generation=[p*8760*.20/1000 for p in capacity]
with open(DATA/"results.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["year","demand_TWh","solar_GW","solar_TWh"])
    w.writerows(zip(years,demand,capacity,generation))
print("Average solar additions:",(1000-168.04)/14,"GW/year")
