import json
import os
import argparse
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate

def generate_summary(data):
    """Generate a quick summary blurb using Ollama"""
    model = ChatOllama(model='phi3:14b-medium-4k-instruct-q5_K_M', temperature=0.1)
    
    # Create simple prompt with recent activity
    activity = []
    if 'commits' in data['activity'].get('code', {}):
        commits = data['activity']['code']['commits'][:10]  # Last 10 commits
        activity.extend(f"Commit: {c['message']}" for c in commits)
    
    if 'pull_requests' in data['activity'].get('code', {}):
        prs = data['activity']['code']['pull_requests']
        activity.extend(f"PR: {pr['title']}" for pr in prs)

    prompt = PromptTemplate(
        template="""Based on this GitHub activity, write a 2-3 sentence summary of what {username} worked on:
{activity}
Keep it brief and focus on main areas of work. Write in present tense. Start with "{username} is" """,
        input_variables=["activity", "username"]
    )
    
    response = model.invoke(prompt.format(
        activity="\n".join(activity),
        username=data['contributor']
    ))
    return response.content.strip()

def process_contributors(input_file, output_file, force=False):
    """Process contributors.json file"""
    # Check if output file exists and force flag is not set
    if os.path.exists(output_file) and not force:
        raise FileExistsError(f"Output file {output_file} already exists. Use -f to overwrite.")
    
    try:
        with open(input_file, 'r') as f:
            contributors = json.load(f)
        
        updated_contributors = []
        
        for contributor in contributors:
            print(f"\nProcessing {contributor['contributor']}...")
            
            # Generate new summary
            new_summary = generate_summary(contributor)
            if new_summary:
                contributor['summary'] = new_summary
                
            print(f"Summary: {new_summary[:100]}...")
            updated_contributors.append(contributor)
        
        # Sort by score before saving
        updated_contributors.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        with open(output_file, 'w') as f:
            json.dump(updated_contributors, f, indent=2)
        
        print(f"\nSaved updated data to {output_file}")
            
    except Exception as e:
        print(f"Error processing contributors: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Generate quick GitHub summaries using Ollama")
    parser.add_argument("input_file", help="Input contributors.json file")
    parser.add_argument("output_file", help="Output contributors.json file")
    parser.add_argument("-f", "--force", action="store_true",
                       help="Force overwrite of output file if it exists")
    args = parser.parse_args()
    
    process_contributors(args.input_file, args.output_file, args.force)
    print("Done!")

if __name__ == "__main__":
    main()
