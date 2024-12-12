import json
import os 

repos = json.load(open("repos.json"))

for repo in repos:
    os.system(f"mkdir -p ./data/{repo['repo']}")
    os.system(f"python scripts/fetch_contributors.py {repo['org']} {repo['repo']}  -o ./data/{repo['repo']} -f")
    os.system(f"python scripts/generate_summaries.py ./data/{repo['repo']}/contributors.json ./data/{repo['repo']}/contributors.json -f")
    os.system(f"python scripts/compute_scores.py ./data/{repo['repo']}/contributors.json ./data/{repo['repo']}/contributors.json -f")    