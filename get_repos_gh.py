import requests
import yaml
from datetime import datetime, timedelta
import urllib3
from termcolor import colored

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

config_file = 'config.yaml'
output_file = 'inactive-repos.txt'

def display_ascii_art():
    title = "Search GitHub Inactive Repos - by PdLx420"
    
    ascii_art = r"""
 ____                      _        ____ _ _   _   _       _      
/ ___|  ___  __ _ _ __ ___| |__    / ___(_) |_| | | |_   _| |__   
\___ \ / _ \/ _` | '__/ __| '_ \  | |  _| | __| |_| | | | | '_ \  
 ___) |  __/ (_| | | | (__| | | | | |_| | | |_|  _  | |_| | |_) | 
|____/ \___|\__,_|_|  \___|_| |_|  \____|_|\__|_| |_|\__,_|_.__/  
|_ _|_ __   __ _  ___| |_(_)_   _____  |  _ \ ___ _ __   ___  ___ 
 | || '_ \ / _` |/ __| __| \ \ / / _ \ | |_) / _ \ '_ \ / _ \/ __|
 | || | | | (_| | (__| |_| |\ V /  __/ |  _ <  __/ |_) | (_) \__ \
|___|_| |_|\__,_|\___|\__|_| \_/ \___| |_| \_\___| .__/ \___/|___/
                                                 |_|              
    """

    colored_title = colored(title, 'green', attrs=['bold'])
    colored_art = colored(ascii_art, 'green')

    print(colored_title)
    print(colored_art)

display_ascii_art()

def read_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

config = read_config(config_file)
GITHUB_TOKEN = config['github_token']
ORG_NAME= config['org_name']

headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}"
    }

def list_repos(organization):
    print(f"\nContabilizando os repos...\n")
    base_url = "https://api.github.com/orgs/{}/repos"

    all_repositories = []
    url = base_url.format(organization)

    while True:
        response = requests.get(url, headers=headers, verify=False) # realiza a requisicao na api do GH

        if response.status_code == 200:
            all_repositories.extend(response.json()) # o codigo abaixo captura os repos acessando as paginacoes que o GH gera
            next_link = response.links.get("next")
            if not next_link:
                break
            url = next_link.get("url")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            break
    return sorted(all_repositories, key=lambda repo: repo["name"].lower()) # ordena os repos por ordem alfabetica

repositories = list_repos(ORG_NAME)

def list_inactive_repos(repos):
    archived_repos = 0
    inactive_repos = 0
    days_without_commit = 180
    github_date_format = (datetime.now() - timedelta(days=days_without_commit)).isoformat() + 'Z'
    default_branch = 'main'

    for repo in repos:
        url = f'https://api.github.com/repos/{repo['full_name']}/commits?sha={default_branch}&since={github_date_format}'
        response = requests.get(url, headers=headers, verify=False)
        commits = response.json()
        active_collaborators = {}
        
        for commit in commits: # identifica os commiters ativos
            if 'author' in commit:
                author = commit['author']
                if author is not None:
                    author_name = author['login']
                    if author_name in active_collaborators:
                        active_collaborators[author_name] += 1
                    else:
                        active_collaborators[author_name] = 1

        if repo['archived'] is True:
            archived_repos += 1

        if len(active_collaborators) == 0:
            with open(output_file, "a") as arquivo:
                arquivo.write(repo['full_name'] + '\n')
            inactive_repos += 1
    
    return archived_repos, inactive_repos

archived_repos, inactive_repos = list_inactive_repos(repositories)

total_repos = len(repositories) - archived_repos
total_active_repos = total_repos - inactive_repos
print(f"Repos arquivados: {(archived_repos)}")
print(f"Total de repos: {(total_repos)}")
print(f"Repos inativos: {(inactive_repos)}")
print(f"Repos ativos: {(total_active_repos)}\n")
print(f"Repos inativos salvos em: {(output_file)}\n")