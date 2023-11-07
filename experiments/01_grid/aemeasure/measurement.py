import datetime
import json
import os
import socket
import sys
import typing
import zipfile
from zipfile import ZipFile

import pandas as pd

from aemeasure.utils.capture import OutputCopy
from aemeasure.utils.git import get_git_revision

git_revision = get_git_revision()


class Measurement(dict):
    _measurement_stack = []

    @staticmethod
    def last() -> dict:
        return Measurement._measurement_stack[-1]

    def time(self, timer=None) -> datetime.timedelta:
        if timer is None:
            return datetime.datetime.now() - self._time
        else:
            return datetime.datetime.now() - self._timer[timer]

    def save_timestamp(self, key="timestamp"):
        self[key] = datetime.datetime.now().isoformat()

    def save_seconds(self, key="runtime", timer=None):
        v = self.time(timer).total_seconds()
        self[key] = v
        return v

    def save_hostname(self, key="hostname"):
        v = socket.gethostname()
        self[key] = v
        return v

    def save_argv(self, key="argv"):
        if sys.argv:
            v = " ".join(sys.argv)
            self[key] = v
            return v
        else:
            self[key] = None
            return None

    def save_git_revision(self, key="git_revision") -> str:
        self[key] = git_revision
        return git_revision

    def save_metadata(self):
        self.save_seconds()
        self.save_timestamp()
        self.save_hostname()
        self.save_argv()
        self.save_git_revision()
        self.save_cwd()

    def start_timer(self, name: str):
        self._timer[name] = datetime.datetime.now()

    def __init__(self, path: typing.Optional[str],
                 capture_stdout: typing.Optional[str] = None,
                 capture_stderr: typing.Optional[str] = None):
        super().__init__()
        self._time = datetime.datetime.now()
        self._path = path
        self._timer = dict()
        self._capture_stdout = capture_stdout
        self._capture_stderr = capture_stderr

    def __enter__(self):
        self._measurement_stack.append(self)
        self.start_capture()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_capture()
        if not exc_type:
            self.write()
        else:
            print("Do not save measurement due to exception.")
        e = self._measurement_stack.pop()
        assert e is self

    def save_cwd(self, label="cwd"):
        self[label] = os.getcwd()

    def start_capture(self):
        if self._capture_stdout:
            sys.stdout = OutputCopy(sys.stdout)
        if self._capture_stderr:
            sys.stderr = OutputCopy(sys.stderr)

    def stop_capture(self):
        if self._capture_stdout:
            self[self._capture_stdout] = sys.stdout.getvalue()
            sys.stdout = sys.stdout.wrapped_stream
        if self._capture_stderr:
            self[self._capture_stderr] = sys.stderr.getvalue()
            sys.stderr = sys.stderr.wrapped_stream

    def write(self):
        if not self._path:
            return
        if os.path.exists(self._path):
            with open(self._path, "r") as f:
                data = json.load(f)
                if not data:
                    data = []
                data.append(self)
            with open(self._path, "w") as f:
                json.dump(data, f)
        else:
            if os.path.dirname(self._path):
                os.makedirs(os.path.dirname(self._path), exist_ok=True)
            with open(self._path, "w") as f:
                json.dump([self], f)


def read_as_pd(path, columns: typing.Optional[typing.List[str]] = None,
               verbose: bool = True) -> pd.DataFrame:
    """
    Reads a database as a pandas table. You can select specfic columns via the
    columns-parameter.
    :param verbose: Print some default information.
    :param path:
    :param columns:
    :return:
    """
    with open(path, "r") as f:
        data = json.load(f)
        if type(data) is not list:
            raise ValueError("Expected list of dicts but json file contains", type(data))
        converted_data = dict()
        for i, entry in enumerate(data):
            for key, value in entry.items():
                if columns is None or key in columns:
                    converted_data.setdefault(key, dict())[i] = value
        t = pd.DataFrame.from_dict(converted_data, orient='columns')
        if verbose:
            print("Loaded dataframe", path)
            if "hostname" in t.columns:
                print("Executed on:", t["hostname"].unique())
            if "timestamp" in t.columns:
                times = pd.to_datetime(t["timestamp"])
                print("During:", times.min(), "and", times.max())
        return t


def query(path: str, query: dict) -> typing.Iterable[dict]:
    """
    Returns all entries in a database matching a specific query.
    The query consists of a dict with possibly multiple conjunctive 'column': 'value'
    pairs. For example you can query all solutions of size n solved by algorithm 'alg_a'
    via
    ```
    query(my_path, {'size': n, 'algorithm': 'alg_a'})
    ```
    If a row of the database does not have the corresponding column, it defaults to 
    'none'.

    :param path: The path to the json file.
    :param q: The query
    :return: All entries matching the queryh
    """
    if not os.path.exists(path):
        print("Query on not existing path", path)
        return

    with open(path, "r") as f:
        data = json.load(f)
        if type(data) is not list:
            raise ValueError("Expected list of dicts but json file contains", type(data))

    def compare(e: dict, q: dict):
        for k, v in q.items():
            if e.setdefault(k, None) != v:
                return False
        return True

    for entry in data:
        if compare(entry, query):
            yield entry


def exists(path: str, q: dict) -> bool:
    """
    Checks if an entry for a specific query exists. This is useful to check if the
    corresponding instance has already been solved. The query consists of a dict with
    possibly multiple conjunctive 'column': 'value' pairs. For example you can query
    if instance 'ins_a' has been solved using algorithm 'alg_a' via 
    ```
    exists(my_path, {'instance': 'ins_a', 'algorithm': 'alg_a'})
    ```
    If a row of the database does not have the corresponding column, it defaults to 
    'none'.
    
    :param path: The path to the json file.
    :param q: The query
    :return: True if there already exists such an entry.
    """
    for _ in query(path, q):
        return True
    return False


def pack(path: str):
    """
    Packs the database into a zip with the date in the name.
    :param path: Database path
    :return:
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    zip_base_path = os.path.splitext(path)[0] + "_" + timestamp
    zip_path = zip_base_path + ".zip"
    i = 0
    while os.path.exists(zip_path):
        zip_path = zip_base_path + f"_{i}.zip"
        i += 1

    with ZipFile(zip_path, "w", compression=zipfile.ZIP_LZMA) as zf:
        zf.write(path)


def unpack(path: str):
    """
    A simple function to undo `pack` and automatically have the latest data set.
    :param path:
    :return:
    """
    folder = os.path.dirname(path)
    zip_base_path = os.path.splitext(path)[0]
    options = [f for f in os.listdir(folder) if f.startswith(zip_base_path)]
    if not options:
        print("No packed results detected!")
        return
    options = [f for f in os.listdir(folder) if f.startswith(zip_base_path)
               and f.endswith(".zip")]
    print("Following ZIPs are detected:")
    for option in options:
        print(option)
    option = options[-1]
    print("Choosing:", option)
    with ZipFile(option, 'r') as zip_f:
        zip_f.extract(os.path.basename(path))
