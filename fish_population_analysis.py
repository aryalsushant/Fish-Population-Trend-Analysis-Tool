# Full Python Code to Clean, Process, and Analyze the Dataset

import pandas as pd
import matplotlib.pyplot as plt

# Load the dataset
file_path = "./data/fishstat_export_s_capture2020.csv"
data = pd.read_csv(file_path)

# Step 1: Drop flag columns (columns starting with 'S')
columns_to_drop = [col for col in data.columns if col.startswith('S')]
data_cleaned = data.drop(columns=columns_to_drop)

# Step 2: Replace missing or invalid values with 0
data_cleaned = data_cleaned.replace('.', 0)
data_cleaned = data_cleaned.fillna(0)

# Step 3: Reshape the data from wide to long format
long_data = pd.melt(
    data_cleaned,
    id_vars=["Country (Country)", "ASFIS species (ASFIS species)", "FAO major fishing area (FAO major fishing area)"],
    var_name="Year",
    value_name="Population"
)

# Rename columns for simplicity
long_data.columns = ["Country", "Species", "Fishing Area", "Year", "Population"]

# Convert Year and Population to numeric
long_data["Year"] = pd.to_numeric(long_data["Year"], errors="coerce")
long_data["Population"] = pd.to_numeric(long_data["Population"], errors="coerce")

# Step 4: Group and Analyze
# Example: Total population by year for a specific species, will update soon
species_to_analyze = "FCY"  # Replace with the species of interest
species_data = long_data[long_data["Species"] == species_to_analyze]
grouped_data = species_data.groupby("Year")["Population"].sum().reset_index()

# Step 5: Plot the population trend for the selected species
plt.figure(figsize=(10, 6))
plt.plot(grouped_data["Year"], grouped_data["Population"], marker="o", color="orange", label=species_to_analyze)
plt.title(f"Population Trends for {species_to_analyze}")
plt.xlabel("Year")
plt.ylabel("Population (Tonnes)")
plt.legend()
plt.grid(True)
plt.show()

# Step 6: Save the processed data
processed_file_path = "/mnt/data/processed_fish_population.csv"
long_data.to_csv(processed_file_path, index=False)
print(f"Processed data saved to {processed_file_path}")
