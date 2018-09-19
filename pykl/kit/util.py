# -*- coding: UTF-8 -*-

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

import re
from collections import deque as Deque

from string import digits
import time
import calendar
from datetime import datetime, timedelta, tzinfo


from stat import S_ISDIR



def tree_to_stream(entries, write):
    """Write the give list of entries into a stream using its write method
    :param entries: **sorted** list of tuples with (binsha, mode, name)
    :param write: write method which takes a data string"""
    ord_zero = ord('0')
    bit_mask = 7            # 3 bits set

    for binsha, mode, name in entries:
        mode_str = b''
        for i in xrange(6):
            mode_str = bchr(((mode >> (i * 3)) & bit_mask) + ord_zero) + mode_str
        # END for each 8 octal value

        # git slices away the first octal if its zero
        if byte_ord(mode_str[0]) == ord_zero:
            mode_str = mode_str[1:]
        # END save a byte

        # here it comes:  if the name is actually unicode, the replacement below
        # will not work as the binsha is not part of the ascii unicode encoding -
        # hence we must convert to an utf8 string for it to work properly.
        # According to my tests, this is exactly what git does, that is it just
        # takes the input literally, which appears to be utf8 on linux.
        if isinstance(name, text_type):
            name = name.encode(defenc)
        write(b''.join((mode_str, b' ', name, b'\0', binsha)))
    # END for each item


def tree_entries_from_data(data):
    """Reads the binary representation of a tree and returns tuples of Tree items
    :param data: data block with tree data (as bytes)
    :return: list(tuple(binsha, mode, tree_relative_path), ...)"""
    ord_zero = ord('0')
    space_ord = ord(' ')
    len_data = len(data)
    i = 0
    out = []
    while i < len_data:
        mode = 0

        # read mode
        # Some git versions truncate the leading 0, some don't
        # The type will be extracted from the mode later
        while byte_ord(data[i]) != space_ord:
            # move existing mode integer up one level being 3 bits
            # and add the actual ordinal value of the character
            mode = (mode << 3) + (byte_ord(data[i]) - ord_zero)
            i += 1
        # END while reading mode

        # byte is space now, skip it
        i += 1

        # parse name, it is NULL separated

        ns = i
        while byte_ord(data[i]) != 0:
            i += 1
        # END while not reached NULL

        # default encoding for strings in git is utf8
        # Only use the respective unicode object if the byte stream was encoded
        name = data[ns:i]
        name = safe_decode(name)

        # byte is NULL, get next 20
        i += 1
        sha = data[i:i + 20]
        i = i + 20
        out.append((sha, mode, name))
    # END for each byte in data stream
    return out


def _find_by_name(tree_data, name, is_dir, start_at):
    """return data entry matching the given name and tree mode
    or None.
    Before the item is returned, the respective data item is set
    None in the tree_data list to mark it done"""
    try:
        item = tree_data[start_at]
        if item and item[2] == name and S_ISDIR(item[1]) == is_dir:
            tree_data[start_at] = None
            return item
    except IndexError:
        pass
    # END exception handling
    for index, item in enumerate(tree_data):
        if item and item[2] == name and S_ISDIR(item[1]) == is_dir:
            tree_data[index] = None
            return item
        # END if item matches
    # END for each item
    return None


def _to_full_path(item, path_prefix):
    """Rebuild entry with given path prefix"""
    if not item:
        return item
    return (item[0], item[1], path_prefix + item[2])


def traverse_trees_recursive(odb, tree_shas, path_prefix):
    """
    :return: list with entries according to the given binary tree-shas.
        The result is encoded in a list
        of n tuple|None per blob/commit, (n == len(tree_shas)), where
        * [0] == 20 byte sha
        * [1] == mode as int
        * [2] == path relative to working tree root
        The entry tuple is None if the respective blob/commit did not
        exist in the given tree.
    :param tree_shas: iterable of shas pointing to trees. All trees must
        be on the same level. A tree-sha may be None in which case None
    :param path_prefix: a prefix to be added to the returned paths on this level,
        set it '' for the first iteration
    :note: The ordering of the returned items will be partially lost"""
    trees_data = []
    nt = len(tree_shas)
    for tree_sha in tree_shas:
        if tree_sha is None:
            data = []
        else:
            data = tree_entries_from_data(odb.stream(tree_sha).read())
        # END handle muted trees
        trees_data.append(data)
    # END for each sha to get data for

    out = []
    out_append = out.append

    # find all matching entries and recursively process them together if the match
    # is a tree. If the match is a non-tree item, put it into the result.
    # Processed items will be set None
    for ti, tree_data in enumerate(trees_data):
        for ii, item in enumerate(tree_data):
            if not item:
                continue
            # END skip already done items
            entries = [None for _ in range(nt)]
            entries[ti] = item
            sha, mode, name = item                          # its faster to unpack @UnusedVariable
            is_dir = S_ISDIR(mode)                          # type mode bits

            # find this item in all other tree data items
            # wrap around, but stop one before our current index, hence
            # ti+nt, not ti+1+nt
            for tio in range(ti + 1, ti + nt):
                tio = tio % nt
                entries[tio] = _find_by_name(trees_data[tio], name, is_dir, ii)
            # END for each other item data

            # if we are a directory, enter recursion
            if is_dir:
                out.extend(traverse_trees_recursive(
                    odb, [((ei and ei[0]) or None) for ei in entries], path_prefix + name + '/'))
            else:
                out_append(tuple(_to_full_path(e, path_prefix) for e in entries))
            # END handle recursion

            # finally mark it done
            tree_data[ii] = None
        # END for each item

        # we are done with one tree, set all its data empty
        del(tree_data[:])
    # END for each tree_data chunk
    return out


def traverse_tree_recursive(odb, tree_sha, path_prefix):
    """
    :return: list of entries of the tree pointed to by the binary tree_sha. An entry
        has the following format:
        * [0] 20 byte sha
        * [1] mode as int
        * [2] path relative to the repository
    :param path_prefix: prefix to prepend to the front of all returned paths"""
    entries = []
    data = tree_entries_from_data(odb.stream(tree_sha).read())

    # unpacking/packing is faster than accessing individual items
    for sha, mode, name in data:
        if S_ISDIR(mode):
            entries.extend(traverse_tree_recursive(odb, sha, path_prefix + name + '/'))
        else:
            entries.append((sha, mode, path_prefix + name))
    # END for each item

    return entries


ZERO = timedelta(0)

#{ Functions


def mode_str_to_int(modestr):
    """
    :param modestr: string like 755 or 644 or 100644 - only the last 6 chars will be used
    :return:
        String identifying a mode compatible to the mode methods ids of the
        stat module regarding the rwx permissions for user, group and other,
        special flags and file system flags, i.e. whether it is a symlink
        for example."""
    mode = 0
    for iteration, char in enumerate(reversed(modestr[-6:])):
        mode += int(char) << iteration * 3
    # END for each char
    return mode


def get_object_type_by_name(object_type_name):
    """
    :return: type suitable to handle the given object type name.
        Use the type to create new instances.

    :param object_type_name: Member of TYPES

    :raise ValueError: In case object_type_name is unknown"""
    if object_type_name == b"commit":
        from . import commit
        return commit.Commit
    elif object_type_name == b"tag":
        from . import tag
        return tag.TagObject
    elif object_type_name == b"blob":
        from . import blob
        return blob.Blob
    elif object_type_name == b"tree":
        from . import tree
        return tree.Tree
    else:
        raise ValueError("Cannot handle unknown object type: %s" % object_type_name)


def utctz_to_altz(utctz):
    """we convert utctz to the timezone in seconds, it is the format time.altzone
    returns. Git stores it as UTC timezone which has the opposite sign as well,
    which explains the -1 * ( that was made explicit here )
    :param utctz: git utc timezone string, i.e. +0200"""
    return -1 * int(float(utctz) / 100 * 3600)


def altz_to_utctz_str(altz):
    """As above, but inverses the operation, returning a string that can be used
    in commit objects"""
    utci = -1 * int((float(altz) / 3600) * 100)
    utcs = str(abs(utci))
    utcs = "0" * (4 - len(utcs)) + utcs
    prefix = (utci < 0 and '-') or '+'
    return prefix + utcs


def verify_utctz(offset):
    """:raise ValueError: if offset is incorrect
    :return: offset"""
    fmt_exc = ValueError("Invalid timezone offset format: %s" % offset)
    if len(offset) != 5:
        raise fmt_exc
    if offset[0] not in "+-":
        raise fmt_exc
    if offset[1] not in digits or\
       offset[2] not in digits or\
       offset[3] not in digits or\
       offset[4] not in digits:
        raise fmt_exc
    # END for each char
    return offset


class tzoffset(tzinfo):
    def __init__(self, secs_west_of_utc, name=None):
        self._offset = timedelta(seconds=-secs_west_of_utc)
        self._name = name or 'fixed'

    def utcoffset(self, dt):
        return self._offset

    def tzname(self, dt):
        return self._name

    def dst(self, dt):
        return ZERO


utc = tzoffset(0, 'UTC')


def from_timestamp(timestamp, tz_offset):
    """Converts a timestamp + tz_offset into an aware datetime instance."""
    utc_dt = datetime.fromtimestamp(timestamp, utc)
    try:
        local_dt = utc_dt.astimezone(tzoffset(tz_offset))
        return local_dt
    except ValueError:
        return utc_dt


def parse_date(string_date):
    """
    Parse the given date as one of the following

        * Git internal format: timestamp offset
        * RFC 2822: Thu, 07 Apr 2005 22:13:13 +0200.
        * ISO 8601 2005-04-07T22:13:13
            The T can be a space as well

    :return: Tuple(int(timestamp_UTC), int(offset)), both in seconds since epoch
    :raise ValueError: If the format could not be understood
    :note: Date can also be YYYY.MM.DD, MM/DD/YYYY and DD.MM.YYYY.
    """
    # git time
    try:
        if string_date.count(' ') == 1 and string_date.rfind(':') == -1:
            timestamp, offset = string_date.split()
            timestamp = int(timestamp)
            return timestamp, utctz_to_altz(verify_utctz(offset))
        else:
            offset = "+0000"                    # local time by default
            if string_date[-5] in '-+':
                offset = verify_utctz(string_date[-5:])
                string_date = string_date[:-6]  # skip space as well
            # END split timezone info
            offset = utctz_to_altz(offset)

            # now figure out the date and time portion - split time
            date_formats = []
            splitter = -1
            if ',' in string_date:
                date_formats.append("%a, %d %b %Y")
                splitter = string_date.rfind(' ')
            else:
                # iso plus additional
                date_formats.append("%Y-%m-%d")
                date_formats.append("%Y.%m.%d")
                date_formats.append("%m/%d/%Y")
                date_formats.append("%d.%m.%Y")

                splitter = string_date.rfind('T')
                if splitter == -1:
                    splitter = string_date.rfind(' ')
                # END handle 'T' and ' '
            # END handle rfc or iso

            assert splitter > -1

            # split date and time
            time_part = string_date[splitter + 1:]    # skip space
            date_part = string_date[:splitter]

            # parse time
            tstruct = time.strptime(time_part, "%H:%M:%S")

            for fmt in date_formats:
                try:
                    dtstruct = time.strptime(date_part, fmt)
                    utctime = calendar.timegm((dtstruct.tm_year, dtstruct.tm_mon, dtstruct.tm_mday,
                                               tstruct.tm_hour, tstruct.tm_min, tstruct.tm_sec,
                                               dtstruct.tm_wday, dtstruct.tm_yday, tstruct.tm_isdst))
                    return int(utctime), offset
                except ValueError:
                    continue
                # END exception handling
            # END for each fmt

            # still here ? fail
            raise ValueError("no format matched")
        # END handle format
    except Exception:
        raise ValueError("Unsupported date format: %s" % string_date)
    # END handle exceptions


# precompiled regex
_re_actor_epoch = re.compile(r'^.+? (.*) (\d+) ([+-]\d+).*$')
_re_only_actor = re.compile(r'^.+? (.*)$')


def parse_actor_and_date(line):
    """Parse out the actor (author or committer) info from a line like::

        author Tom Preston-Werner <tom@mojombo.com> 1191999972 -0700

    :return: [Actor, int_seconds_since_epoch, int_timezone_offset]"""
    actor, epoch, offset = '', 0, 0
    m = _re_actor_epoch.search(line)
    if m:
        actor, epoch, offset = m.groups()
    else:
        m = _re_only_actor.search(line)
        actor = m.group(1) if m else line or ''
    return (Actor._from_string(actor), int(epoch), utctz_to_altz(offset))

#} END functions


#{ Classes

class ProcessStreamAdapter(object):

    """Class wireing all calls to the contained Process instance.

    Use this type to hide the underlying process to provide access only to a specified
    stream. The process is usually wrapped into an AutoInterrupt class to kill
    it if the instance goes out of scope."""
    __slots__ = ("_proc", "_stream")

    def __init__(self, process, stream_name):
        self._proc = process
        self._stream = getattr(process, stream_name)

    def __getattr__(self, attr):
        return getattr(self._stream, attr)


class Traversable(object):

    """Simple interface to perform depth-first or breadth-first traversals
    into one direction.
    Subclasses only need to implement one function.
    Instances of the Subclass must be hashable"""
    __slots__ = ()

    @classmethod
    def _get_intermediate_items(cls, item):
        """
        Returns:
            List of items connected to the given item.
            Must be implemented in subclass
        """
        raise NotImplementedError("To be implemented in subclass")

    def list_traverse(self, *args, **kwargs):
        """
        :return: IterableList with the results of the traversal as produced by
            traverse()"""
        out = IterableList(self._id_attribute_)
        out.extend(self.traverse(*args, **kwargs))
        return out

    def traverse(self, predicate=lambda i, d: True,
                 prune=lambda i, d: False, depth=-1, branch_first=True,
                 visit_once=True, ignore_self=1, as_edge=False):
        """:return: iterator yielding of items found when traversing self

        :param predicate: f(i,d) returns False if item i at depth d should not be included in the result

        :param prune:
            f(i,d) return True if the search should stop at item i at depth d.
            Item i will not be returned.

        :param depth:
            define at which level the iteration should not go deeper
            if -1, there is no limit
            if 0, you would effectively only get self, the root of the iteration
            i.e. if 1, you would only get the first level of predecessors/successors

        :param branch_first:
            if True, items will be returned branch first, otherwise depth first

        :param visit_once:
            if True, items will only be returned once, although they might be encountered
            several times. Loops are prevented that way.

        :param ignore_self:
            if True, self will be ignored and automatically pruned from
            the result. Otherwise it will be the first item to be returned.
            If as_edge is True, the source of the first edge is None

        :param as_edge:
            if True, return a pair of items, first being the source, second the
            destination, i.e. tuple(src, dest) with the edge spanning from
            source to destination"""
        visited = set()
        stack = Deque()
        stack.append((0, self, None))       # self is always depth level 0

        def addToStack(stack, item, branch_first, depth):
            lst = self._get_intermediate_items(item)
            if not lst:
                return
            if branch_first:
                stack.extendleft((depth, i, item) for i in lst)
            else:
                reviter = ((depth, lst[i], item) for i in range(len(lst) - 1, -1, -1))
                stack.extend(reviter)
        # END addToStack local method

        while stack:
            d, item, src = stack.pop()          # depth of item, item, item_source

            if visit_once and item in visited:
                continue

            if visit_once:
                visited.add(item)

            rval = (as_edge and (src, item)) or item
            if prune(rval, d):
                continue

            skipStartItem = ignore_self and (item is self)
            if not skipStartItem and predicate(rval, d):
                yield rval

            # only continue to next level if this is appropriate !
            nd = d + 1
            if depth > -1 and nd > depth:
                continue

            addToStack(stack, item, branch_first, nd)
        # END for each item on work stack


class Serializable(object):

    """Defines methods to serialize and deserialize objects from and into a data stream"""
    __slots__ = ()

    def _serialize(self, stream):
        """Serialize the data of this object into the given data stream
        :note: a serialized object would ``_deserialize`` into the same object
        :param stream: a file-like object
        :return: self"""
        raise NotImplementedError("To be implemented in subclass")

    def _deserialize(self, stream):
        """Deserialize all information regarding this object from the stream
        :param stream: a file-like object
        :return: self"""
        raise NotImplementedError("To be implemented in subclass")


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


class IndexObject(Object):

    """Base for all objects that can be part of the index file , namely Tree, Blob and
    SubModule objects"""
    __slots__ = ("path", "mode")

    # for compatibility with iterable lists
    _id_attribute_ = 'path'

    def __init__(self, repo, binsha, mode=None, path=None):
        """Initialize a newly instanced IndexObject

        :param repo: is the Repo we are located in
        :param binsha: 20 byte sha1
        :param mode:
            is the stat compatible file mode as int, use the stat module
            to evaluate the information
        :param path:
            is the path to the file in the file system, relative to the git repository root, i.e.
            file.ext or folder/other.ext
        :note:
            Path may not be set of the index object has been created directly as it cannot
            be retrieved without knowing the parent tree."""
        super(IndexObject, self).__init__(repo, binsha)
        if mode is not None:
            self.mode = mode
        if path is not None:
            self.path = path

    def __hash__(self):
        """
        :return:
            Hash of our path as index items are uniquely identifiable by path, not
            by their data !"""
        return hash(self.path)

    def _set_cache_(self, attr):
        if attr in IndexObject.__slots__:
            # they cannot be retrieved lateron ( not without searching for them )
            raise AttributeError(
                "Attribute '%s' unset: path and mode attributes must have been set during %s object creation"
                % (attr, type(self).__name__))
        else:
            super(IndexObject, self)._set_cache_(attr)
        # END handle slot attribute

    @property
    def name(self):
        """:return: Name portion of the path, effectively being the basename"""
        return osp.basename(self.path)

    @property
    def abspath(self):
        """
        :return:
            Absolute path to this index object in the file system ( as opposed to the
            .path field which is a path relative to the git repository ).

            The returned path will be native to the system and contains '\' on windows. """
        return join_path_native(self.repo.working_tree_dir, self.path)

# In Python 2.6, there is no NullHandler yet. Let's monkey-patch it for a workaround.
if not hasattr(logging, 'NullHandler'):
    logging.NullHandler = NullHandler


if __name__ == '__main__':
    print get_user_id()

    print py_where('git')