# coding: utf-8
import random
import time
import hashlib
from inspect import isclass

from git import Repo as GitRepo

from sqlalchemy.inspection import inspect as sqlalchemyinspect
from sqlalchemy.ext.declarative import declarative_base

from pykl.tiny.grapheneinfo import (
    _is_graphql,
    _is_graphql_cls,
    _is_graphql_mutation
)

from pykl.tiny.codegen.utils import (
    name_from_repr,
    camel_to_underline,
    underline_to_camel,
)

from base_type import *
from cmd import db, app
Base = db.Model


class MigrateVersion(Base):
    u"""table migrate_version"""
    __tablename__ = 'migrate_version'

    repository_id = Column(String(191), primary_key=True, doc=u"""field repository_id""", info=CustomField | SortableField)
    repository_path = Column(Text, doc=u"""field repository_path""", info=CustomField | SortableField)
    version = Column(Integer, doc=u"""field version""", info=CustomField | SortableField)

class Actor(Base):
    u"""table kit_actor"""
    __tablename__ = 'kit_actor'
    actor_id = Column(Integer, primary_key=True, doc=u"""对应 actor_id""", info=SortableField | InitializeField)
    actor_name = Column(String(64), doc=u"""field actor_name""", info=CustomField | SortableField)
    actor_email = Column(String(64), doc=u"""field actor_email""", info=CustomField | SortableField)

class Blob(Base):
    u"""table kit_blob"""
    __tablename__ = 'kit_blob'
    blob_id = Column(Integer, primary_key=True, doc=u"""对应 blob_id""", info=SortableField | InitializeField)
    blob_path = Column(String(64), doc=u"""field blob_path""", info=CustomField | SortableField)
    blob_hash = Column(String(40), doc=u"""field blob_hash""", info=CustomField | SortableField)
    blob_mode = Column(Integer, doc=u"""field blob_mode""", info=CustomField | SortableField)
    blob_size = Column(Integer, doc=u"""field blob_size""", info=CustomField | SortableField)

class Tree(Base):
    u"""table kit_tree"""
    __tablename__ = 'kit_tree'
    tree_id = Column(Integer, primary_key=True, doc=u"""对应 tree_id""", info=SortableField | InitializeField)
    tree_path = Column(String(64), doc=u"""field tree_path""", info=CustomField | SortableField)
    tree_hash = Column(String(40), doc=u"""field tree_hash""", info=CustomField | SortableField)
    tree_mode = Column(Integer, doc=u"""field tree_mode""", info=CustomField | SortableField)
    tree_size = Column(Integer, doc=u"""field tree_size""", info=CustomField | SortableField)

    @classmethod
    def info(cls):
        class Tree(SQLAlchemyObjectType):
            class Meta:
                model = cls

            trees = List(lambda :cls, description=u'trees')
            def resolve_trees(self, args, context, info):
                return [_Tree(tree) for tree in self._tree.trees]

            blobs = List(lambda :Blob, description=u'blobs')
            def resolve_blobs(self, args, context, info):
                return [_Blob(blob) for blob in self._tree.blobs]

            blobfile = Field(lambda :Blob, description=u'对应 blob',
                path=g.Argument(g.String, default_value="", description=u'input you file name')
            )
            def resolve_blobfile(self, args, context, info):
                path = args.get('path', '')
                return search_blobfile(self._tree, path)

            treedir = Field(lambda :Tree, description=u'对应 blob',
                path=g.Argument(g.String, default_value="", description=u'input you file name')
            )
            def resolve_treedir(self, args, context, info):
                path = args.get('path', '')
                return search_treedir(self._tree, path)

        return Tree

class Commit(Base):
    u"""table kit_commit"""
    __tablename__ = 'kit_commit'
    commit_id = Column(Integer, primary_key=True, doc=u"""对应 commit_id""", info=SortableField | InitializeField)
    commit_hash = Column(String(40), doc=u"""field commit_hash""", info=CustomField | SortableField)
    commit_message = Column(String(191), doc=u"""field repo_path""", info=CustomField | SortableField)
    committed_date = Column(Integer, doc=u"""field repo_path""", info=CustomField | SortableField)

    @classmethod
    def info(cls):
        class Commit(SQLAlchemyObjectType):
            class Meta:
                model = cls

            author = Field(lambda :Actor, description=u'对应 author')
            def resolve_author(self, args, context, info):
                author = self._commit.author
                return _Actor(author)

            committer = Field(lambda :Actor, description=u'对应 committer')
            def resolve_committer(self, args, context, info):
                committer = self._commit.committer
                return _Actor(committer)

            parents = List(lambda :cls, description=u'parents commits')
            def resolve_parents(self, args, context, info):
                return [_Commit(commit) for commit in self._commit.parents]

            tree = Field(lambda :Tree, description=u'对应 tree')
            def resolve_tree(self, args, context, info):
                tree = self._commit.tree
                return _Tree(tree)

            blobfile = Field(lambda :Blob, description=u'对应 blob',
                path=g.Argument(g.String, default_value="", description=u'input you file name')
            )
            def resolve_blobfile(self, args, context, info):
                path = args.get('path', '')
                return search_blobfile(self._commit.tree, path)

            treedir = Field(lambda :Tree, description=u'对应 blob',
                path=g.Argument(g.String, default_value="", description=u'input you file name')
            )
            def resolve_treedir(self, args, context, info):
                path = args.get('path', '')
                return search_treedir(self._commit.tree, path)

        return Commit

class Ref(Base):
    u"""table kit_ref"""
    __tablename__ = 'kit_ref'
    ref_id = Column(Integer, primary_key=True, doc=u"""对应 repo_id""", info=SortableField | InitializeField)
    ref_path = Column(String(191), doc=u"""field repo_path""", info=CustomField | SortableField)
    ref_name = Column(String(191), doc=u"""field repo_path""", info=CustomField | SortableField)

    @classmethod
    def info(cls):
        class Ref(SQLAlchemyObjectType):
            class Meta:
                model = cls

            commit = Field(lambda :Commit, description=u'对应 commit')
            def resolve_commit(self, args, context, info):
                commit = self._ref.commit
                return _Commit(commit)

            blobfile = Field(lambda :Blob, description=u'对应 blob',
                path=g.Argument(g.String, default_value="", description=u'input you file name')
            )
            def resolve_blobfile(self, args, context, info):
                path = args.get('path', '')
                return search_blobfile(self._ref.commit.tree, path)

            treedir = Field(lambda :Tree, description=u'对应 blob',
                path=g.Argument(g.String, default_value="", description=u'input you file name')
            )
            def resolve_treedir(self, args, context, info):
                path = args.get('path', '')
                return search_treedir(self._ref.commit.tree, path)

            commits = List(lambda :Commit, description=u'往前推算 commits',
                max_count=g.Argument(g.Int, description=u'input max_count')
            )
            def resolve_commits(self, args, context, info):
                max_count = args.get('max_count', 10)
                if max_count <= 0:
                    return []
                return [_Commit(commit) for commit in self._ref.repo.iter_commits(self._ref.name, max_count=max_count)]

        return Ref

class Repo(Base):
    u"""table kit_repo"""
    __tablename__ = 'kit_repo'

    repo_id = Column(Integer, primary_key=True, doc=u"""对应 repo_id""", info=SortableField | InitializeField)
    repo_path = Column(String(191), doc=u"""field repo_path""", info=CustomField | SortableField)

    @classmethod
    def info(cls):
        class Repo(SQLAlchemyObjectType):
            class Meta:
                model = cls

            head = Field(lambda :Ref, description=u'查找 引用',
                name=g.Argument(g.String, default_value="master", description=u'input you name')
            )
            def resolve_head(self, args, context, info):
                name = args.get('name', '')
                if not name:
                    return None
                ref = self._repo.heads[name]
                return _Ref(ref)

            heads = List(lambda :Ref, description=u'引用')
            def resolve_heads(self, args, context, info):
                return [_Ref(ref) for ref in self._repo.heads]

            master = Field(lambda :Ref, description=u'master 引用')
            def resolve_master(self, args, context, info):
                ref = self._repo.heads.master
                return _Ref(ref)

            tag = Field(lambda :Ref, description=u'查找 tag',
                name=g.Argument(g.String, description=u'input you tag')
            )
            def resolve_tag(self, args, context, info):
                name = args.get('name', '')
                if not name:
                    return None
                ref = self._repo.tags[name]
                return _Ref(ref)

            tags = List(lambda :Ref, description=u'tag')
            def resolve_tags(self, args, context, info):
                return [_Ref(ref) for ref in self._repo.tags]

        return Repo

def search_blobfile(_tree, path):
    if not path:
        return None

    def _resolve_blobfile(blobs, trees):
        for blob in blobs:
            if path == blob.path:
                return _Blob(blob)
        for tree in trees:
            ret = _resolve_blobfile(tree.blobs, tree.trees) if path.startswith(tree.path) else None
            if ret:
                return ret
    return _resolve_blobfile(_tree.blobs, _tree.trees)

def search_treedir(_tree, path):
    if not path:
        return None

    def _resolve_treedir(trees):
        for tree in trees:
            if path == tree.path:
                return _Tree(tree)
        for tree in trees:
            ret = _resolve_treedir(tree.trees) if path.startswith(tree.path) else None
            if ret:
                return ret
    return _resolve_treedir(_tree.trees)

def _Actor(actor, actor_id=0):
    obj = Actor(actor_id=actor_id, actor_name=actor.name, actor_email=actor.email)
    obj._actor = actor
    return obj

def _Blob(blob, blob_id=0):
    obj = Blob(blob_id=0, blob_path=blob.path, blob_hash=blob.hexsha, blob_mode=blob.mode, blob_size=blob.size)
    obj._blob = blob
    return obj

def _Tree(tree, tree_id=0):
    obj = Tree(tree_id=tree_id, tree_path=tree.path, tree_hash=tree.hexsha, tree_mode=tree.mode, tree_size=tree.size)
    obj._tree = tree
    return obj

def _Commit(commit, commit_id=0):
    obj = Commit(commit_id=commit_id, commit_hash=commit.hexsha, commit_message=commit.message, committed_date=commit.committed_date)
    obj._commit = commit
    return obj

def _Ref(ref, ref_id=0):
    obj = Ref(ref_id=ref_id, ref_name=ref.name, ref_path=ref.path)
    obj._ref = ref
    return obj

def _Repo(repo, repo_id=0):
    obj = Repo(repo_id=repo_id, repo_path=repo.working_dir)
    obj._repo = repo
    return obj

##############################################################
###################		根查询 Query		######################
##############################################################

class Query(g.ObjectType):
    hello = g.String(name=g.Argument(g.String, default_value="world", description=u'input you name'))
    deprecatedField = Field(g.String, deprecation_reason = 'This field is deprecated!')
    fieldWithException = g.String()
    migrateVersion = Field(MigrateVersion, description=u'migrate_version')

    repo = Field(Repo, description=u'load repo by path',
        repo_path=g.Argument(g.String, description=u'input repo path'),
    )
    def resolve_repo(self, args, context, info):
        repo_path = args.get('repo_path', '')
        repo = GitRepo(repo_path)
        return _Repo(repo)

    curRepo = Field(Repo, description=u'this repo')
    def resolve_curRepo(self, args, context, info):
        repo = app.config.get('REPO')
        return _Repo(repo)

    def resolve_hello(self, args, context, info):
        return 'Hello, %s!' % (args.get('name', ''), )

    def resolve_deprecatedField(self, args, context, info):
        return 'You can request deprecated field, but it is not displayed in auto-generated documentation by default.'

    def resolve_fieldWithException(self, args, context, info):
        raise ValueError('Exception message thrown in field resolver')

    def resolve_migrateVersion(self, args, context, info):
        return MigrateVersion.query.first()

##############################################################
###################		 Mutations		######################
##############################################################
def build_input(dao, bit_mask):
    return {k: BuildArgument(v) for k, v in mask_field(dao, bit_mask).items()}

class CreateMigrateVersion(g.Mutation):
    Input = type('Input', (), build_input(MigrateVersion, InitializeField))

    ok = g.Boolean()
    msg = g.String()
    migrateVersion = Field(MigrateVersion)

    @staticmethod
    def mutate(root, args, context, info):
        return CreateMigrateVersion(ok=True, msg='suc', migrateVersion=MigrateVersion.query.first())

class UpdateMigrateVersion(g.Mutation):
    Input = type('Input', (), build_input(MigrateVersion, EditableField))

    ok = g.Boolean()
    msg = g.String()
    migrateVersion = Field(MigrateVersion)

    @staticmethod
    def mutate(root, args, context, info):
        return UpdateMigrateVersion(ok=True, msg='suc', migrateVersion=MigrateVersion.query.first())

##############################################################
###################		根查询 Mutations		######################
##############################################################

Mutations = type('Mutations', (g.ObjectType, ), {camel_to_underline(name_from_repr(v)):v.Field() for _, v in globals().items() if _is_graphql_mutation(v)})

tables = [tbl if BuildType(tbl) else tbl for _, tbl in globals().items() if isclass(tbl) and issubclass(tbl, Base) and tbl != Base]
schema = g.Schema(query=Query, mutation=Mutations, types=[BuildType(tbl) for tbl in tables] + [cls for _, cls in globals().items() if _is_graphql_cls(cls)], auto_camelcase = False)