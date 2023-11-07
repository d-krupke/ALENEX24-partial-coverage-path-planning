import subprocess


def get_git_revision():
    try:
        label = subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip().decode(
            'ascii')
    except subprocess.CalledProcessError:
        print("Warning: Could not read git-revision!")
        label = None
    return label