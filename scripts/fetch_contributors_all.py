import logging
import json
import os 


def main():
    repos = json.load(open("repos.json"))

    for repo in repos:
        logging.info(f"Fetching contributors for {repo['org']}/{repo['repo']}")
        os.system(f"mkdir -p ./data/{repo['repo']}")
        os.system(f"mkdir -p ./profiles/{repo['repo']}")
        logging.info(f"Fetching contributors for {repo['org']}/{repo['repo']}")
        os.system(f"python scripts/fetch_contributors.py {repo['org']} {repo['repo']}  -o ./data/{repo['repo']} -f")
        logging.info(f"Generating summaries for {repo['org']}/{repo['repo']}")
        os.system(f"python scripts/generate_summaries.py ./data/{repo['repo']}/contributors.json ./data/{repo['repo']}/contributors.json -f")
        logging.info(f"Computing scores for {repo['org']}/{repo['repo']}")
        os.system(f"python scripts/compute_scores.py ./data/{repo['repo']}/contributors.json ./data/{repo['repo']}/contributors.json -f")    
    

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
