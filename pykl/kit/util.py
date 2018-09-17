# utils.py
# Copyright (C) 2008, 2009 Michael Trier (mtrier@gmail.com) and contributors
#
# This module is part of GitPython and is released under
# the BSD License: http://www.opensource.org/licenses/bsd-license.php
import contextlib
from functools import wraps
import getpass
import logging
import os
import re
import shutil
import stat
import time
import hashlib
import platform

import os.path as osp


def make_sha(source=''.encode("ascii")):
    """A python2.4 workaround for the sha/hashlib module fiasco

    **Note** From the dulwich project """
    try:
        return hashlib.sha1(source)
    except NameError:
        import sha
        sha1 = sha.sha(source)
        return sha1

log = logging.getLogger(__name__)

class InvalidGitRepositoryError(Exception):
    pass

def unbare_repo(func):
    """Methods with this decorator raise InvalidGitRepositoryError if they
    encounter a bare repository"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.repo.bare:
            raise InvalidGitRepositoryError("Method '%s' cannot operate on bare repositories" % func.__name__)
        # END bare method
        return func(self, *args, **kwargs)
    # END wrapper
    return wrapper


@contextlib.contextmanager
def cwd(new_dir):
    old_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield new_dir
    finally:
        os.chdir(old_dir)


def rmtree(path):
    """Remove the given recursively.

    :note: we use shutil rmtree but adjust its behaviour to see whether files that
        couldn't be deleted are read-only. Windows will not remove them in that case"""

    def onerror(func, path, exc_info):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)

        try:
            func(path)  # Will scream if still not possible to delete.
        except Exception as ex:
            if HIDE_WINDOWS_KNOWN_ERRORS:
                raise SkipTest("FIXME: fails with: PermissionError\n  %s", ex)
            else:
                raise

    return shutil.rmtree(path, False, onerror)


def rmfile(path):
    """Ensure file deleted also on *Windows* where read-only files need special treatment."""
    if osp.isfile(path):
        if is_win:
            os.chmod(path, 0o777)
        os.remove(path)


def stream_copy(source, destination, chunk_size=512 * 1024):
    """Copy all data from the source stream into the destination stream in chunks
    of size chunk_size

    :return: amount of bytes written"""
    br = 0
    while True:
        chunk = source.read(chunk_size)
        destination.write(chunk)
        br += len(chunk)
        if len(chunk) < chunk_size:
            break
    # END reading output stream
    return br


def join_path(a, *p):
    """Join path tokens together similar to osp.join, but always use
    '/' instead of possibly '\' on windows."""
    path = a
    for b in p:
        if len(b) == 0:
            continue
        if b.startswith('/'):
            path += b[1:]
        elif path == '' or path.endswith('/'):
            path += b
        else:
            path += '/' + b
    # END for each path token to add
    return path


def assure_directory_exists(path, is_file=False):
    """Assure that the directory pointed to by path exists.

    :param is_file: If True, path is assumed to be a file and handled correctly.
        Otherwise it must be a directory
    :return: True if the directory was created, False if it already existed"""
    if is_file:
        path = osp.dirname(path)
    # END handle file
    if not osp.isdir(path):
        os.makedirs(path)
        return True
    return False


def _get_exe_extensions():
    PATHEXT = os.environ.get('PATHEXT', None)
    return tuple(p.upper() for p in PATHEXT.split(os.pathsep)) \
        if PATHEXT \
        else (('.BAT', 'COM', '.EXE') if is_win else ())


def py_where(program, path=None):
    # From: http://stackoverflow.com/a/377028/548792
    winprog_exts = _get_exe_extensions()

    def is_exec(fpath):
        return osp.isfile(fpath) and os.access(fpath, os.X_OK) and (
            os.name != 'nt' or not winprog_exts or any(fpath.upper().endswith(ext)
                                                       for ext in winprog_exts))

    progs = []
    if not path:
        path = os.environ["PATH"]
    for folder in path.split(os.pathsep):
        folder = folder.strip('"')
        if folder:
            exe_path = osp.join(folder, program)
            for f in [exe_path] + ['%s%s' % (exe_path, e) for e in winprog_exts]:
                if is_exec(f):
                    progs.append(f)
    return progs

def get_user_id():
    """:return: string identifying the currently active system user as name@node"""
    return "%s@%s" % (getpass.getuser(), platform.node())


def finalize_process(proc, **kwargs):
    """Wait for the process (clone, fetch, pull or push) and handle its errors accordingly"""
    ## TODO: No close proc-streams??
    proc.wait(**kwargs)


def expand_path(p, expand_vars=True):
    try:
        p = osp.expanduser(p)
        if expand_vars:
            p = osp.expandvars(p)
        return osp.normpath(osp.abspath(p))
    except Exception:
        return None

#} END utilities

#{ Classes

class Actor(object):
    """Actors hold information about a person acting on the repository. They
    can be committers and authors or anything with a name and an email as
    mentioned in the git log entries."""
    # PRECOMPILED REGEX
    name_only_regex = re.compile(r'<(.+)>')
    name_email_regex = re.compile(r'(.*) <(.+?)>')

    # ENVIRONMENT VARIABLES
    # read when creating new commits
    env_author_name = "GIT_AUTHOR_NAME"
    env_author_email = "GIT_AUTHOR_EMAIL"
    env_committer_name = "GIT_COMMITTER_NAME"
    env_committer_email = "GIT_COMMITTER_EMAIL"

    # CONFIGURATION KEYS
    conf_name = 'name'
    conf_email = 'email'

    __slots__ = ('name', 'email')

    def __init__(self, name, email):
        self.name = name
        self.email = email

    def __eq__(self, other):
        return self.name == other.name and self.email == other.email

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash((self.name, self.email))

    def __str__(self):
        return self.name

    def __repr__(self):
        return u'<git.Actor "%s <%s>">' % (self.name, self.email)

    @classmethod
    def _from_string(cls, string):
        """Create an Actor from a string.
        :param string: is the string, which is expected to be in regular git format

                John Doe <jdoe@example.com>

        :return: Actor """
        m = cls.name_email_regex.search(string)
        if m:
            name, email = m.groups()
            return Actor(name, email)
        else:
            m = cls.name_only_regex.search(string)
            if m:
                return Actor(m.group(1), None)
            else:
                # assume best and use the whole string as name
                return Actor(string, None)
            # END special case name
        # END handle name/email matching

    @classmethod
    def _main_actor(cls, env_name, env_email, config_reader=None):
        actor = Actor('', '')
        default_email = get_user_id()
        default_name = default_email.split('@')[0]

        for attr, evar, cvar, default in (('name', env_name, cls.conf_name, default_name),
                                          ('email', env_email, cls.conf_email, default_email)):
            try:
                val = os.environ[evar]
                if not PY3:
                    val = val.decode(defenc)
                # end assure we don't get 'invalid strings'
                setattr(actor, attr, val)
            except KeyError:
                if config_reader is not None:
                    setattr(actor, attr, config_reader.get_value('user', cvar, default))
                # END config-reader handling
                if not getattr(actor, attr):
                    setattr(actor, attr, default)
            # END handle name
        # END for each item to retrieve
        return actor

    @classmethod
    def committer(cls, config_reader=None):
        """
        :return: Actor instance corresponding to the configured committer. It behaves
            similar to the git implementation, such that the environment will override
            configuration values of config_reader. If no value is set at all, it will be
            generated
        :param config_reader: ConfigReader to use to retrieve the values from in case
            they are not set in the environment"""
        return cls._main_actor(cls.env_committer_name, cls.env_committer_email, config_reader)

    @classmethod
    def author(cls, config_reader=None):
        """Same as committer(), but defines the main author. It may be specified in the environment,
        but defaults to the committer"""
        return cls._main_actor(cls.env_author_name, cls.env_author_email, config_reader)


class Stats(object):

    """
    Represents stat information as presented by git at the end of a merge. It is
    created from the output of a diff operation.

    ``Example``::

     c = Commit( sha1 )
     s = c.stats
     s.total         # full-stat-dict
     s.files         # dict( filepath : stat-dict )

    ``stat-dict``

    A dictionary with the following keys and values::

      deletions = number of deleted lines as int
      insertions = number of inserted lines as int
      lines = total number of lines changed as int, or deletions + insertions

    ``full-stat-dict``

    In addition to the items in the stat-dict, it features additional information::

     files = number of changed files as int"""
    __slots__ = ("total", "files")

    def __init__(self, total, files):
        self.total = total
        self.files = files

    @classmethod
    def _list_from_string(cls, repo, text):
        """Create a Stat object from output retrieved by git-diff.

        :return: git.Stat"""
        hsh = {'total': {'insertions': 0, 'deletions': 0, 'lines': 0, 'files': 0}, 'files': {}}
        for line in text.splitlines():
            (raw_insertions, raw_deletions, filename) = line.split("\t")
            insertions = raw_insertions != '-' and int(raw_insertions) or 0
            deletions = raw_deletions != '-' and int(raw_deletions) or 0
            hsh['total']['insertions'] += insertions
            hsh['total']['deletions'] += deletions
            hsh['total']['lines'] += insertions + deletions
            hsh['total']['files'] += 1
            hsh['files'][filename.strip()] = {'insertions': insertions,
                                              'deletions': deletions,
                                              'lines': insertions + deletions}
        return Stats(hsh['total'], hsh['files'])


class IndexFileSHA1Writer(object):

    """Wrapper around a file-like object that remembers the SHA1 of
    the data written to it. It will write a sha when the stream is closed
    or if the asked for explicitly using write_sha.

    Only useful to the indexfile

    :note: Based on the dulwich project"""
    __slots__ = ("f", "sha1")

    def __init__(self, f):
        self.f = f
        self.sha1 = make_sha(b"")

    def write(self, data):
        self.sha1.update(data)
        return self.f.write(data)

    def write_sha(self):
        sha = self.sha1.digest()
        self.f.write(sha)
        return sha

    def close(self):
        sha = self.write_sha()
        self.f.close()
        return sha

    def tell(self):
        return self.f.tell()



class IterableList(list):

    """
    List of iterable objects allowing to query an object by id or by named index::

     heads = repo.heads
     heads.master
     heads['master']
     heads[0]

    It requires an id_attribute name to be set which will be queried from its
    contained items to have a means for comparison.

    A prefix can be specified which is to be used in case the id returned by the
    items always contains a prefix that does not matter to the user, so it
    can be left out."""
    __slots__ = ('_id_attr', '_prefix')

    def __new__(cls, id_attr, prefix=''):
        return super(IterableList, cls).__new__(cls)

    def __init__(self, id_attr, prefix=''):
        self._id_attr = id_attr
        self._prefix = prefix

    def __contains__(self, attr):
        # first try identity match for performance
        rval = list.__contains__(self, attr)
        if rval:
            return rval
        # END handle match

        # otherwise make a full name search
        try:
            getattr(self, attr)
            return True
        except (AttributeError, TypeError):
            return False
        # END handle membership

    def __getattr__(self, attr):
        attr = self._prefix + attr
        for item in self:
            if getattr(item, self._id_attr) == attr:
                return item
        # END for each item
        return list.__getattribute__(self, attr)

    def __getitem__(self, index):
        if isinstance(index, int):
            return list.__getitem__(self, index)

        try:
            return getattr(self, index)
        except AttributeError:
            raise IndexError("No item found with id %r" % (self._prefix + index))
        # END handle getattr

    def __delitem__(self, index):
        delindex = index
        if not isinstance(index, int):
            delindex = -1
            name = self._prefix + index
            for i, item in enumerate(self):
                if getattr(item, self._id_attr) == name:
                    delindex = i
                    break
                # END search index
            # END for each item
            if delindex == -1:
                raise IndexError("Item with name %s not found" % name)
            # END handle error
        # END get index to delete
        list.__delitem__(self, delindex)


class Iterable(object):

    """Defines an interface for iterable items which is to assure a uniform
    way to retrieve and iterate items within the git repository"""
    __slots__ = ()
    _id_attribute_ = "attribute that most suitably identifies your instance"

    @classmethod
    def list_items(cls, repo, *args, **kwargs):
        """
        Find all items of this type - subclasses can specify args and kwargs differently.
        If no args are given, subclasses are obliged to return all items if no additional
        arguments arg given.

        :note: Favor the iter_items method as it will

        :return:list(Item,...) list of item instances"""
        out_list = IterableList(cls._id_attribute_)
        out_list.extend(cls.iter_items(repo, *args, **kwargs))
        return out_list

    @classmethod
    def iter_items(cls, repo, *args, **kwargs):
        """For more information about the arguments, see list_items
        :return:  iterator yielding Items"""
        raise NotImplementedError("To be implemented by Subclass")

#} END classes


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


# In Python 2.6, there is no NullHandler yet. Let's monkey-patch it for a workaround.
if not hasattr(logging, 'NullHandler'):
    logging.NullHandler = NullHandler


if __name__ == '__main__':
    print get_user_id()

    print py_where('git')