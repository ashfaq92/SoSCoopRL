# data format
# cycle,mean_battery,box_count,alive_robots,robot_type
# 10,298.5,45,89,random
# 20,295.2,52,87,random
# 10,299.1,43,90,greedy
# 20,297.8,38,89,greedy


import os
import pandas as pd
import matplotlib.pyplot as plt

print("Current working directory:", os.getcwd())


df = pd.read_csv('data_analysis/data_python.csv', names=['cycle', 'battery', 'boxes', 'alive', 'type'])


print("Robot types in data:", df['type'].unique())
print("Data counts per type:")
print(df['type'].value_counts())
print("\nFirst few rows:")
print(df.head(10))

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))

# Plot battery levels
for robot_type, color in [('rl', 'red'), ('greedy', 'green'), ('cooperative', 'blue'), ('saphesia', 'black')]:
    data = df[df['type'] == robot_type]
    ax1.plot(data['cycle'], data['battery'], color=color, label=robot_type)
ax1.set_ylabel('Mean Battery Level')
ax1.legend()

# Plot box counts
for robot_type, color in [('rl', 'red'), ('greedy', 'green'), ('cooperative', 'blue'), ('saphesia', 'black')]:
    data = df[df['type'] == robot_type]
    ax2.plot(data['cycle'], data['boxes'], color=color, label=robot_type)
ax2.set_ylabel('Boxes in Environment')
ax2.legend()

# Plot alive robots
for robot_type, color in [('rl', 'red'), ('greedy', 'green'), ('cooperative', 'blue'), ('saphesia', 'black')]:
    data = df[df['type'] == robot_type]
    ax3.plot(data['cycle'], data['alive'], color=color, label=robot_type)
ax3.set_ylabel('Alive Robots in Environment')
ax3.set_xlabel('Cycle')
ax3.legend()

plt.tight_layout()
plt.show()


