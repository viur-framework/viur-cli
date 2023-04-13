import os, sys, click, json, requests
from . import cli, get_config
import subprocess
import google.auth

class color:
    BOLD = '\033[1m'
    END = '\033[0m'

def first():
    credentials, project_id = google.auth.default()
    print(credentials)
    print("Google Auth:", project_id)
    projectConfig = get_config()
    dist_folder = projectConfig["default"]["distribution_folder"]
    print(projectConfig)
    print(dist_folder)
    
def get_gcloud_active_account() -> str:
    """Returns user active account """
    
    command = 'gcloud auth list --filter=status:ACTIVE --format="value(account)"'
    
    click.echo(f"Execution command {color.BOLD}{command}{color.END} ...")
    
    active_account = subprocess.check_output([command], shell=True, text=True).strip()
    return active_account


def isInViurFolder() -> bool:
    """Check if the command runs in the Folder of a ViUR Project"""
    # At present, only existance of project.json is being checked
    click.echo("\nChecking if you are in the project directory...")
    isFolder = False
    isFile = os.path.exists('project.json')
    
    if isFile:
        with open('project.json', 'r') as f:
            data = json.load(f)
            if 'vi' in data.get('default'):
                isFolder = True
                click.echo("Great, you are in")
    else:
        click.echo("Please, change directory to ViUR project")
        sys.exit()
    return isFolder

def gcloud_prep():
    try:
        os.system('gcloud init')
        
        isFile = os.path.exists('сloudbuild.yaml')
        if isFile:
            print('сloudbuild was found')
        if not isFile:
            return 
            # TODO: discuss how to send user:password with header in POST request
            url = 'https://bitbucket.org/mausbrand/viur-build/src/main/example%20cloudbuild/cloudbuild.yaml'
            r = requests.get(url)
            print(r.status_code)
            open('сloudbuild.yaml', 'wb').write(r.content)
    except Exception:
        sys.exit() # TODO: figure out what can go wrong

def gcloud_project():
    if not click.confirm('\nDo you have already Google Cloud Source Project?'):
        print('How to setup:')
        print('1. ?')
        print('2. ?')

def create_trigger():
    """
    https://cloud.google.com/build/docs/automating-builds/create-manage-triggers
    gcloud source repos list
    
    REPO_NAME                           PROJECT_ID      URL
    bitbucket_kenvoitsekh_co-dev-viur3  vk-testprojekt  https://bitbucket.org/kenvoitsekh/co-dev-viur3.git
    bitbucket_mausbrand_co-dev-viur3    vk-testprojekt  https://bitbucket.org/mausbrand/co-dev-viur3.git

    Args:
        repo_name: is the name of your repository.
        branch_pattern: is the branch name in your repository to invoke the build on.
        build_config:  is the path to your build configuration file.
        service_account: is the email associated with your service account
    """
    # gcloud beta builds triggers create cloud-source-repositories \                                                                                               01:10:05
    #                                            --repo=bitbucket_kenvoitsekh_co-dev-viur3 \
    #                                            --branch-pattern=main \
    #                                            --build-config=cloudbuild.yaml \
    #                                            --description="Test trigger, to be deleted"
    
    #req = 'gcloud source repos list| grep %s' % (repo_name)
    
    print('Checking repos list...')
    get_repo_list = 'gcloud source repos list'
    
    # n_repos= int(subprocess.check_output(req+' | wc -l', shell=True))
    # if not n_repos:
    #     print(f"{repo_name} was not found!")
    #     print("Available list of repos:")
    #     os.system('gcloud source repos list')
    #     sys.exit()
    os.system(get_repo_list)
    repo_name = click.prompt('Please type a valid repo name:', type=str)
    branch_pattern = click.prompt('Please type a branch pattern:', type=str, default='main')
    build_config = click.prompt('Please type a build file:', type=str, default='cloudbuild.yaml')
    descr = click.prompt('Please type a trigger description:', type=str, default='Build-and-deploy')
    #print(n)
    
    command = f'''gcloud beta builds triggers create cloud-source-repositories\
    --repo={repo_name}\
    --branch-pattern={branch_pattern}\
    --build-config={build_config}\
    --description={descr}'''
    
    click.echo(command)
    if click.confirm('Are the arguments correct?'):
        click.echo('Creating trigger...')
        os.system(command)
    # gcloud beta builds triggers run MY-TRIGGER --branch=master
    if click.confirm('Run this trigger?'):
        click.echo('Running trigger...')
        command = f'gcloud beta builds triggers run {descr} --branch={branch_pattern}'
        click.echo(command)
        os.system(command)
def fix_gitmodules(fn='.gitmodules'):
    """changes url in .gitmodules file from ssh to https link and pushes the changes
    3 ways:
        1) do it with re module
        2) using Perl
           perl -i -p -e 's|https://(.*?)/|git@\1:|g' .gitmodules
        3) using sed 's/url = git@/url = https:\/\//g;s/:/\//2;s/\.git//g'

    before:
        url = git@github.com:viur-framework/viur-scriptor.git
    after:
        url = https://github.com/viur-framework/viur-scriptor
        
    git submodule sync
    """
    click.echo('Checking .gitmodules...')
    import re
    with open(fn, 'r') as f:
        file_string = f.readlines()
        for line in file_string:
            if 'url = git@' in line:
                replacements=[
                    ('url = git@', 'url = https://'),
                    (':', '/'),
                    ('.git', '')]
                for old, new in replacements:
                    result = re.sub(old, new, line)
        print(result)
        # TODO: if result is ok -> update .gitmodules and commit changes
    

def fix_url_in_yaml(fn: str):
    # Ask Roland or Tilman about docker images, which to use on every step
    pass


def prep():
    projectConfig = get_config()
    print(projectConfig)


@cli.command()
def setupcicd():
    """Setup and prepare GCP commands and pipeline to build project"""
    #first()
    #return
    
    account = get_gcloud_active_account()
    if len(account) > 0:
        click.echo(f"Found {account} active account")
        click.confirm("Proceed with this account?", abort=True)
    else:
        click.echo(f"You have to sign in, type {color.BOLD}google auth login{color.END}")
    
    isInViurFolder()
    

    gcloud_prep()
    gcloud_project()
    # fix_gitmodules('.gitmodules')

    create_trigger()
    #prep()
if __name__ == '__main__':
    setupcicd()
