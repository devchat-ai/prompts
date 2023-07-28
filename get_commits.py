import os
import requests
import pandas as pd
from typing import Dict, List

def get_commits(org: str, repo: str) -> List[Dict[str, str]]:
    url = f"https://api.github.com/repos/{org}/{repo}/commits"
    response = requests.get(url)
    response.raise_for_status()
    commits = response.json()
    commit_data = []
    for commit in commits:
        commit_message_title = commit['commit']['message'].split('\n', 1)[0]
        commit_data.append({
            "Commit": f"[{commit_message_title}](https://github.com/{org}/{repo}/commit/{commit['sha']})",
            "Commit Hash": commit["sha"],
            "Author": f"[{commit['commit']['author']['name']}](https://github.com/{commit['author']['login']})",
            "Prompts with GPT": f"[Prompts with GPT](./commits/{commit['sha']}.md)",
            "给 GPT 的 Prompts": f"[给 GPT 的 Prompts](./commits/{commit['sha']}_zh.md)",
        })
    return commit_data

def append_commits_to_file(commits: List[Dict[str, str]], file_path: str) -> None:
    df = pd.DataFrame(commits)
    df['Commit Hash'] = df['Commit Hash'].apply(lambda x: x[:7])
    with open(file_path, "a") as f:
        f.write(df.to_markdown(index=False))

def create_commit_files(commit: Dict[str, str], directory: str = "devchat-ai/gopool/commits") -> None:
    """
    Create markdown files for each commit.
    """
    for suffix in ["", "_zh"]:
        file_path = os.path.join(directory, f"{commit['Commit Hash']}{suffix}.md")
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                f.write("")

def main():
    org = "devchat-ai"
    repo = "gopool"
    file_path = "devchat-ai/gopool/index.md"
    commits = get_commits(org, repo)
    append_commits_to_file(commits, file_path)
    for commit in commits:
        create_commit_files(commit)

if __name__ == "__main__":
    main()
