
import logging
import argparse
import os
from pathlib import Path
import subprocess
import stat

__author__ = 'psessford'

"""
This script copies over the source ("src") directory of a repo to another repo 
so that the functionality of the copied source directory can be imported and 
used in the other repo. The design is to allow repos to share common and 
narrow functionality, such as authentication middleware for a Flask app, or 
frontend template functionality for web apps.

Script inputs:
- The repo that's source directory is to be copied (the "input repo").
- The repo to which the source directory is to be copied (the "output repo").

Script functionality:
- Check that there is only one directory in the input repo. (This is for 
simplicity and to emphasize that an input repo should be narrow in its 
functionality.)
- Check that the size (memory to store the code) of the input repo is small. 
(This is so that files that take a large amount of memory to store do not get 
replicated, and to emphasize that an input repo should be narrow in its 
functionality.)
- Copy over the source directory of the input repo to the root of the output 
repo.
- Displays information to user that copied directory should (almost always) be 
seen as read-only. (This is because the idea is for development of the input 
repo to be done on that repo directly so that it can then be used by other 
repos too.)

For simplicity, this script should only use the Python standard library 
(assuming Python 3.7 or later).

Possible alternative methods to using this script:
- Package up the input repo, add it to the requirements file, and use pip to 
install it for use in the output repo. This is more complicated if the input 
repo is private.
- When using Docker, specify the copying over of the input repo in the Docker 
file. This is more complicated when different versions of the input repo are 
developed, since updating the input repo could lead to the breaking of the 
output repo, or to the need to keep multiple versions of the input repo and 
specify which is wanted for the output repo.

Some useful discussions:
- https://stackoverflow.com/questions/55929417/
how-to-securely-git-clone-pip-install-a-private-repository-into-my-docker-image
- https://stackoverflow.com/questions/50468951/
credentials-in-pip-conf-for-private-pypi
"""

# TODO: add some functionality to check the number of differences between the
#  input directory and an output directory that has previously between copied
#  over (could make updating easier)?


def get_inputted_repo_paths():
    """Get path to the "input repo" and that to the "output repo" from the
    script inputs; the input repo contains the source directory to be copied
    to the output repo

    :return input_repo_path, output_repo_path: (Path, Path)
    """
    logging.info("getting inputted repo paths")

    parser = argparse.ArgumentParser()
    parser.add_argument('input_repo')
    parser.add_argument('output_repo')
    args = parser.parse_args()

    input_repo_path = Path(args.input_repo, help='path to input repo')
    output_repo_path = Path(args.output_repo, help='path to output repo')

    input_repo_path = (
        input_repo_path if input_repo_path.is_absolute()
        else Path.cwd() / input_repo_path)
    output_repo_path = (
        output_repo_path if output_repo_path.is_absolute()
        else Path.cwd() / output_repo_path)

    logging.info(f"input repo: {str(input_repo_path)}")
    logging.info(f"output repo: {str(output_repo_path)}")
    return input_repo_path, output_repo_path


def get_single_public_directory(dir_path):
    """Get the single (public) directory within a parent directory

    :param dir_path: (Path) parent directory
    :return public_dir: (Path) only public directory within parent directory
    """
    logging.info(f"getting single public directory ({dir_path.name})")

    hidden_dirs = [p for p in dir_path.glob('./.*') if p.is_dir()]
    private_dirs = [p for p in dir_path.glob('./_*') if p.is_dir()]
    public_dirs = [p for p in dir_path.glob('./*')
                   if (p.is_dir() and p not in hidden_dirs + private_dirs)]

    if len(public_dirs) != 1:
        raise ValueError(f"single public directory not found "
                         f"({[d.name for d in public_dirs]})")

    public_dir = public_dirs[0]
    logging.info(f"found public directory {public_dir}")
    return public_dir


def check_small_dir(dir_path, max_gigabytes=0.001):
    """Check that the size of a directory is small

    :param dir_path: (Path) directory of which to check the size
    :param max_gigabytes: (float) maximum allowed size of directory in
        gigabytes
    """
    logging.info(f"checking that directory takes a small amount of memory to "
                 f"store ({dir_path.name})")
    dir_bytes_size = os.path.getsize(dir_path)
    dir_gigabytes_size = dir_bytes_size / 1073741824.

    if max_gigabytes < dir_gigabytes_size:
        raise Exception(
            f"input directory too large ({dir_gigabytes_size} gigabytes)")


def copy_directory(input_dir_path, output_repo_path):
    """Copy a directory to the root of another repo

    :param input_dir_path: (Path) directory to copy
    :param output_repo_path: (Path) destination repo for copied directory
    :return output_dir_path: (Path) copied directory
    """
    logging.info(f"copying src directory of input repo to the root of the "
                 f"output repo (i.e. to within {output_repo_path.name})")
    subprocess.run(
        ["cp", "-R", f"{str(input_dir_path)}", f"{str(output_repo_path)}"])

    output_dir_path = output_repo_path / input_dir_path.name
    logging.info(f"finished copying directory from {str(input_dir_path)} to "
                 f"{str(output_dir_path)}")
    logging.info(
        "!!NOTE: the copied directory should (almost always) be seen as "
        "READ-ONLY (just like an external package), such that any additions/"
        "edits to the copied funcationality should be made on the original "
        "(input) repo, not the copied code. This is because the idea is for "
        "development of the input repo to also be avaiable to other repos "
        "too.!!")
    return output_dir_path


def set_directory_to_read_only(dir_path):
    """Set the permissions of a directory to read-only

    :param dir_path: (Path)
    """
    logging.info(f"setting directory to read-only permission ({dir_path})")
    dir_path.chmod(stat.S_IREAD)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    input_repo_path, output_repo_path = get_inputted_repo_paths()

    input_dir_path = get_single_public_directory(dir_path=input_repo_path)
    check_small_dir(dir_path=input_dir_path)
    output_dir_path = copy_directory(
        input_dir_path=input_dir_path, output_repo_path=output_repo_path)
    # set_directory_to_read_only(dir_path=output_dir_path)
